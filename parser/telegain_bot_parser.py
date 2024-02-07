from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from sqlalchemy.orm import sessionmaker

from db.models import BotInfo
from db.postgresql import async_session_noauto

import logging


class TelegaInBotParser:

    BASE_URL: str = 'https://telega.in/catalog_bots?filter%5Btg_bot_theme_id%5D={category}&order%5Bsort%5D=title&order%5Btype%5D=ASC'

    CATEGORY_COUNT: int = 20

    ACTIVE_USERS_LABEL: str = "Активные Юзеры"
    MIN_ORDER_LABEL: str = "Мин. заказ"
    PRICE_PER_1000_LABEL: str = "Цена за 1000"
    PRICE_PER_ALL_USER_LABEL: str = "Цена за всех юзеров"

    def __init__(self, driver: WebDriver, session_maker: sessionmaker = async_session_noauto):
        self.driver: WebDriver = driver
        self.session_maker: sessionmaker = session_maker

    @staticmethod
    def safe_find_element(driver_block: WebDriver, by, value):
        try:
            return driver_block.find_element(by, value)
        except NoSuchElementException:
            return None

    @staticmethod
    def safe_find_element_attribute(driver_block: WebDriver, by, value, attribute):
        element = TelegaInBotParser.safe_find_element(driver_block, by, value)

        if element:
            return element.get_attribute(attribute)

        return None

    @staticmethod
    def safe_find_element_text(driver_block, by, value):
        element = TelegaInBotParser.safe_find_element(driver_block, by, value)

        if element:
            return element.text

        return None

    @staticmethod
    def convert_k_short_decimal_to_float(number_str: str):
        k_count = number_str.count('K')

        if k_count > 0:
            multiplier = 1000 ** k_count
            number = float(number_str.replace('K', '')) * multiplier
            return number

        return float(number_str)

    @staticmethod
    def convert_m_short_decimal_to_float(number_str: str):
        m_count = number_str.count('M')

        if m_count > 0:
            multiplier = 1000000 ** m_count
            number = float(number_str.replace('M', '')) * multiplier
            return number

        return float(number_str)

    @staticmethod
    def convert_short_decimal_to_float(number_str: str):
        if number_str.count('K') > 0:
            return TelegaInBotParser.convert_k_short_decimal_to_float(number_str)

        if number_str.count('M') > 0:
            return TelegaInBotParser.convert_m_short_decimal_to_float(number_str)

        return float(number_str)

    @staticmethod
    def clear_digits(number_str: str):
        number_str_without_space = number_str.replace(' ', '').replace('₽', '')
        return TelegaInBotParser.convert_short_decimal_to_float(number_str_without_space)

    @staticmethod
    def safe_clear_digits(number_str: str):
        if number_str:
            return TelegaInBotParser.clear_digits(number_str)

        return number_str

    def waite_load_page(self):
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'body')))

    def load_all_bots_with_page(self, category: int):
        self.driver.get(self.BASE_URL.format(category=category))

        try:
            self.waite_load_page()

            button = EC.presence_of_element_located(
                (By.XPATH,
                 '//div[contains(@class, "btn_more cursor-pointer color-blue mt-8px font-18px bold js_load_content_btn_more")]'
                )
            )

            if hasattr(button, 'click'):
                button.click()

        except Exception as e:
            logging.error(e)

    def parse_stat_block(self, stat_blocks):
        active_users = None
        min_order = None
        price_per_1000 = None
        price_per_all_users = None

        for stat_block in stat_blocks:
            label = TelegaInBotParser.safe_find_element_text(stat_block, By.XPATH, './/div[contains(@class, "channel-stat-label")]')
            label = TelegaInBotParser.safe_find_element_text(stat_block, By.XPATH, './/div[contains(@class, "channel-stat-label")]')

            value = TelegaInBotParser.safe_find_element_text(stat_block, By.XPATH, './/div[contains(@class, "channel-stat-value")]')

            if self.ACTIVE_USERS_LABEL in label:
                active_users = TelegaInBotParser.safe_clear_digits(value)
            elif self.MIN_ORDER_LABEL in label:
                min_order = TelegaInBotParser.safe_clear_digits(value)
            elif self.PRICE_PER_1000_LABEL in label:
                price_per_1000 = TelegaInBotParser.safe_clear_digits(value)
            elif self.PRICE_PER_ALL_USER_LABEL in label:
                price_per_all_users = TelegaInBotParser.safe_clear_digits(value)
            else:
                continue

        return active_users, min_order, price_per_1000, price_per_all_users

    async def save_to_db(self,
                         active_users,
                         min_order,
                         price_per_1000,
                         price_per_all_users,
                         broadcasting_cost,
                         bot_name,
                         bot_url,
                         category):
        async with self.session_maker() as async_session:
            bot_info = BotInfo(
                name=bot_name,
                url=bot_url,
                category=category,
                active_users=active_users,
                min_order=min_order,
                price_per_1000=price_per_1000,
                price_for_all_users=price_per_all_users,
                cost_mailing=broadcasting_cost
            )

            async_session.add(bot_info)

            await async_session.commit()


    def load_data_from_bot(self, links: list[str]):
        for link_bot in links:
            logging.info(f"Navigating to bot page: {link_bot}")
            self.driver.get(link_bot)

            self.waite_load_page()

            stat_blocks = self.driver.find_elements(By.XPATH, '//div[contains(@class, "channel-stat-block")]')

            active_users, min_order, price_per_1000, price_per_all_users = self.parse_stat_block(stat_blocks)

            broadcasting_cost = TelegaInBotParser.safe_clear_digits(
                TelegaInBotParser.safe_find_element_text(
                    self.driver,
                    By.XPATH,
                    '//div[contains(@class, "channel-buy-block")]\
                    /div[contains(@class, "price")]\
                    /span[contains(@class, "value")]\
                    /span[contains(@class, "amount ru")]'
                )
            )

            bot_name = TelegaInBotParser.safe_find_element_text(self.driver, By.XPATH, '//h1[@class="channel-title"]')
            bot_url = TelegaInBotParser.safe_find_element_attribute(self.driver, By.XPATH, '//a[@class="channel_avatar_link"]', 'href')
            category = TelegaInBotParser.safe_find_element_text(self.driver, By.XPATH, '//a[@class="custom blue ml-4px"]')

            yield active_users, min_order, price_per_1000, price_per_all_users, broadcasting_cost, bot_name, bot_url, category

    async def run(self):
        for category in range(1, self.CATEGORY_COUNT):
            logging.info("---")
            logging.info(f'Start categoty {category}')

            self.load_all_bots_with_page(category=category)

            links = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'color-body') and contains(@class, 'mb-8px')]")
            links = [link.get_attribute('href') for link in links]

            for active_users, min_order, price_per_1000, price_per_all_users, broadcasting_cost, bot_name, bot_url, category in self.load_data_from_bot(links):
                await self.save_to_db(
                    active_users=active_users,
                    min_order=min_order,
                    price_per_1000=price_per_1000,
                    price_per_all_users=price_per_all_users,
                    broadcasting_cost=broadcasting_cost,
                    bot_name=bot_name,
                    bot_url=bot_url,
                    category=category
                )

                logging.info(f"Active Users: {active_users}")
                logging.info(f"Minimum Order: {min_order}")
                logging.info(f"Price per 1000: {price_per_1000}")
                logging.info(f"Price per all users: {price_per_all_users}")
                logging.info(f"Broadcasting Cost: {broadcasting_cost}")
                logging.info(f"Bot Name: {bot_name}")
                logging.info(f"Bot URL: {bot_url}")
                logging.info(f"Category: {category}")
                logging.info("---")

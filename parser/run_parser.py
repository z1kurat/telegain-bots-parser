from selenium import webdriver

from db.postgresql import async_session_noauto

import asyncio

import logging

import os

from telegain_bot_parser import TelegaInBotParser

logging.basicConfig(level=logging.INFO)


async def main():
    logging.info(f'Run parser')

    selenium_host = os.environ.get('SELENIUM_HOST', 'chrome')
    selenium_port = int(os.environ.get('SELENIUM_PORT',  4444))

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.set_capability('browserName', 'chrome')

    driver = webdriver.Remote(
        command_executor=f'http://{selenium_host}:{selenium_port}/wd/hub',
        options=options
    )

    parser: TelegaInBotParser = TelegaInBotParser(
        driver=driver,
        session_maker=async_session_noauto
    )

    await parser.run()

    driver.quit()

if __name__ == '__main__':
    asyncio.run(main())

from __future__ import annotations

from sqlalchemy import Double, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BotInfo(Base):
    __tablename__ = 'bot_info'

    id: Mapped[int] = mapped_column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column('name', String)

    url: Mapped[str] = mapped_column('url', String)

    category: Mapped[str] = mapped_column('category', String)

    active_users: Mapped[int] = mapped_column('active_users', Integer)

    min_order: Mapped[float] = mapped_column('min_order', Double, nullable=True)

    price_per_1000: Mapped[float] = mapped_column('price_per_1000', Double, nullable=True)

    price_for_all_users: Mapped[float] = mapped_column('price_for_all_users', Double, nullable=True)

    cost_mailing: Mapped[float] = mapped_column('cost_mailing', Double, nullable=True)

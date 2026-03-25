from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Column, String, Integer

from app.db.base import Base

class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
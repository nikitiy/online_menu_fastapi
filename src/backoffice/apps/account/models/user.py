from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backoffice.models.base import Base
from src.backoffice.models.mixins import CreatedUpdatedMixin, IdMixin


class User(Base, IdMixin, CreatedUpdatedMixin):
    __tablename__ = "users"
    __repr_fields__ = ("email", "username")

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, index=True
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)

    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(  # type: ignore
        "OAuthAccount", back_populates="user", cascade="all, delete-orphan"
    )
    

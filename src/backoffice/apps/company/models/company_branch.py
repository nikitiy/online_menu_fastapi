from typing import Optional, TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Импорты будут добавлены в __init__.py для избежания циклических импортов
from src.backoffice.models import Base, IdMixin

if TYPE_CHECKING:
    from src.backoffice.apps.location.models.address import Address
    from src.backoffice.apps.company.models.company import Company


class CompanyBranch(Base, IdMixin):
    __tablename__ = "company_branches"
    __repr_fields__ = ("company_id", "name", "address_id")

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company: Mapped["Company"] = relationship(  # type: ignore
        back_populates="branches",
    )

    # Основная информация о филиале
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)

    address_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    address: Mapped[Optional["Address"]] = relationship("Address")

    # Дополнительная информация
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Статус
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Внешние ID для интеграции
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )

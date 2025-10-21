from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Импорты будут добавлены в __init__.py для избежания циклических импортов
from src.backoffice.models import Base, IdMixin


class Address(Base, IdMixin):
    """Модель адреса"""

    __tablename__ = "addresses"
    __repr_fields__ = ("street_id", "house_number", "building", "apartment")

    # Основные поля адреса
    house_number: Mapped[str] = mapped_column(String(20), nullable=True)
    building: Mapped[str] = mapped_column(String(20), nullable=True)  # корпус
    apartment: Mapped[str] = mapped_column(String(20), nullable=True)  # квартира
    entrance: Mapped[str] = mapped_column(String(20), nullable=True)  # подъезд
    floor: Mapped[int] = mapped_column(Integer, nullable=True)

    # Связи с географическими объектами
    street_id: Mapped[int] = mapped_column(
        ForeignKey("streets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Географические координаты
    latitude: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True, index=True)

    # Дополнительная информация
    postal_code: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Статус и валидация
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Внешние ID для интеграции с geocoder
    external_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    geocoder_provider: Mapped[str] = mapped_column(String(50), nullable=True)

    # Relationships
    street: Mapped["Street"] = relationship("Street", back_populates="addresses")  # type: ignore

    @property
    def full_address(self) -> str:
        """Полный адрес в читаемом формате"""
        parts = []
        if self.street:
            parts.append(self.street.name)
        if self.house_number:
            parts.append(f"д. {self.house_number}")
        if self.building:
            parts.append(f"корп. {self.building}")
        if self.apartment:
            parts.append(f"кв. {self.apartment}")
        return ", ".join(parts)

    

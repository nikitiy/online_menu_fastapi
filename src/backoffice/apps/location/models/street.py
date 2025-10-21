from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Импорты будут добавлены в __init__.py для избежания циклических импортов
from src.backoffice.models import Base, IdMixin


class Street(Base, IdMixin):
    """Модель улицы"""

    __tablename__ = "streets"
    __repr_fields__ = ("name", "city_id")

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    city_id: Mapped[int] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Географические координаты (центр улицы)
    latitude: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    # Тип улицы (улица, проспект, переулок и т.д.)
    street_type: Mapped[str] = mapped_column(String(50), nullable=True)
    # Дополнительная информация
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    city: Mapped["City"] = relationship("City", back_populates="streets")  # type: ignore
    addresses: Mapped[list["Address"]] = relationship(  # type: ignore
        "Address", back_populates="street", cascade="all, delete-orphan"
    )

    

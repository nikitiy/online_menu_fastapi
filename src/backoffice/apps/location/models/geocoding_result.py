from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Импорты будут добавлены в __init__.py для избежания циклических импортов
from src.backoffice.models import Base, IdMixin


class GeocodingResult(Base, IdMixin):
    """Модель результата геокодирования"""

    __tablename__ = "geocoding_results"
    __repr_fields__ = ("provider", "query")
    __repr_maxlen__ = 60

    # Исходный запрос
    query: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    # Результат геокодирования
    latitude: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True, index=True)

    # Форматированный адрес
    formatted_address: Mapped[str] = mapped_column(Text, nullable=True)

    # Детализация адреса
    country: Mapped[str] = mapped_column(String(255), nullable=True)
    region: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(255), nullable=True)
    street: Mapped[str] = mapped_column(String(255), nullable=True)
    house_number: Mapped[str] = mapped_column(String(50), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=True)

    # Дополнительная информация
    place_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    place_type: Mapped[str] = mapped_column(String(100), nullable=True)

    # Точность и качество результата
    accuracy: Mapped[str] = mapped_column(
        String(50), nullable=True
    )  # ROOFTOP, RANGE_INTERPOLATED, GEOMETRIC_CENTER, APPROXIMATE
    confidence: Mapped[float] = mapped_column(Float, nullable=True)  # 0.0 - 1.0

    # Провайдер geocoder
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)

    # Метаданные
    raw_response: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # JSON ответ от провайдера
    is_successful: Mapped[bool] = mapped_column(default=True, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Связь с адресом (если был создан)
    address_id: Mapped[int] = mapped_column(
        ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    address: Mapped["Address"] = relationship("Address")  # type: ignore

    

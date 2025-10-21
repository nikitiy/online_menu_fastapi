from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class GeocodingAccuracy(str, Enum):
    """Точность геокодирования"""

    ROOFTOP = "ROOFTOP"
    RANGE_INTERPOLATED = "RANGE_INTERPOLATED"
    GEOMETRIC_CENTER = "GEOMETRIC_CENTER"
    APPROXIMATE = "APPROXIMATE"


class GeocodingProvider(str, Enum):
    """Провайдеры геокодирования"""

    GOOGLE = "google"
    YANDEX = "yandex"
    NOMINATIM = "nominatim"
    MAPBOX = "mapbox"


class GeocodingRequest(BaseModel):
    """Запрос на геокодирование"""

    query: str = Field(
        ..., description="Адрес для геокодирования", min_length=1, max_length=1000
    )
    provider: Optional[GeocodingProvider] = Field(
        GeocodingProvider.GOOGLE, description="Провайдер геокодирования"
    )
    language: Optional[str] = Field("ru", description="Язык ответа", max_length=10)
    region: Optional[str] = Field(
        None, description="Регион для ограничения поиска", max_length=100
    )
    bounds: Optional[str] = Field(
        None, description="Границы поиска (lat1,lng1,lat2,lng2)"
    )
    components: Optional[str] = Field(
        None, description="Компоненты адреса для фильтрации"
    )


class GeocodingResultBase(BaseModel):
    """Базовая схема результата геокодирования"""

    query: str = Field(..., description="Исходный запрос")
    latitude: Optional[float] = Field(None, description="Широта", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="Долгота", ge=-180, le=180)
    formatted_address: Optional[str] = Field(None, description="Форматированный адрес")
    country: Optional[str] = Field(None, description="Страна", max_length=255)
    region: Optional[str] = Field(None, description="Регион", max_length=255)
    city: Optional[str] = Field(None, description="Город", max_length=255)
    street: Optional[str] = Field(None, description="Улица", max_length=255)
    house_number: Optional[str] = Field(None, description="Номер дома", max_length=50)
    postal_code: Optional[str] = Field(
        None, description="Почтовый индекс", max_length=20
    )
    place_id: Optional[str] = Field(None, description="ID места", max_length=255)
    place_type: Optional[str] = Field(None, description="Тип места", max_length=100)
    accuracy: Optional[GeocodingAccuracy] = Field(None, description="Точность")
    confidence: Optional[float] = Field(None, description="Уверенность", ge=0.0, le=1.0)
    provider: GeocodingProvider = Field(..., description="Провайдер")
    external_id: Optional[str] = Field(None, description="Внешний ID", max_length=255)
    is_successful: bool = Field(True, description="Успешно ли геокодирование")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")


class GeocodingResultCreate(GeocodingResultBase):
    """Схема для создания результата геокодирования"""

    raw_response: Optional[str] = Field(None, description="Сырой ответ от провайдера")
    expires_at: Optional[datetime] = Field(None, description="Время истечения кэша")
    address_id: Optional[int] = Field(None, description="ID созданного адреса")


class GeocodingResultResponse(GeocodingResultBase):
    """Схема ответа для результата геокодирования"""

    id: int
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class GeocodingSearchRequest(BaseModel):
    """Запрос на поиск адресов"""

    query: str = Field(
        ..., description="Поисковый запрос", min_length=1, max_length=1000
    )
    provider: Optional[GeocodingProvider] = Field(
        GeocodingProvider.GOOGLE, description="Провайдер"
    )
    language: Optional[str] = Field("ru", description="Язык ответа", max_length=10)
    region: Optional[str] = Field(
        None, description="Регион для ограничения поиска", max_length=100
    )
    bounds: Optional[str] = Field(None, description="Границы поиска")
    components: Optional[str] = Field(None, description="Компоненты адреса")
    limit: Optional[int] = Field(
        10, description="Максимальное количество результатов", ge=1, le=50
    )


class GeocodingSearchResponse(BaseModel):
    """Ответ на поиск адресов"""

    results: List[GeocodingResultResponse]
    total: int
    query: str
    provider: GeocodingProvider


class ReverseGeocodingRequest(BaseModel):
    """Запрос обратного геокодирования"""

    latitude: float = Field(..., description="Широта", ge=-90, le=90)
    longitude: float = Field(..., description="Долгота", ge=-180, le=180)
    provider: Optional[GeocodingProvider] = Field(
        GeocodingProvider.GOOGLE, description="Провайдер"
    )
    language: Optional[str] = Field("ru", description="Язык ответа", max_length=10)
    result_type: Optional[str] = Field(
        None, description="Типы результатов для фильтрации"
    )


class GeocodingListResponse(BaseModel):
    """Схема для списка результатов геокодирования"""

    results: List[GeocodingResultResponse]
    total: int
    page: int
    size: int
    pages: int

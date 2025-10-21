from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StreetBase(BaseModel):
    """Базовая схема улицы"""

    name: str = Field(..., description="Название улицы", max_length=255)
    name_en: str = Field(
        ..., description="Название улицы на английском", max_length=255
    )
    city_id: int = Field(..., description="ID города")
    latitude: Optional[float] = Field(None, description="Широта", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="Долгота", ge=-180, le=180)
    street_type: Optional[str] = Field(None, description="Тип улицы", max_length=50)
    description: Optional[str] = Field(None, description="Описание")
    is_active: bool = Field(True, description="Активна ли улица")


class StreetCreate(StreetBase):
    """Схема для создания улицы"""

    pass


class StreetUpdate(BaseModel):
    """Схема для обновления улицы"""

    name: Optional[str] = Field(None, max_length=255)
    name_en: Optional[str] = Field(None, max_length=255)
    city_id: Optional[int] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    street_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class StreetResponse(StreetBase):
    """Схема ответа для улицы"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StreetListResponse(BaseModel):
    """Схема для списка улиц"""

    streets: list[StreetResponse]
    total: int
    page: int
    size: int
    pages: int

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CityBase(BaseModel):
    """Базовая схема города"""

    name: str = Field(..., description="Название города", max_length=255)
    name_en: str = Field(
        ..., description="Название города на английском", max_length=255
    )
    country_id: int = Field(..., description="ID страны")
    region_id: Optional[int] = Field(None, description="ID региона")
    latitude: Optional[float] = Field(None, description="Широта", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="Долгота", ge=-180, le=180)
    population: Optional[int] = Field(None, description="Население", ge=0)
    timezone: Optional[str] = Field(None, description="Временная зона", max_length=50)
    description: Optional[str] = Field(None, description="Описание")
    is_active: bool = Field(True, description="Активен ли город")


class CityCreate(CityBase):
    """Схема для создания города"""

    pass


class CityUpdate(BaseModel):
    """Схема для обновления города"""

    name: Optional[str] = Field(None, max_length=255)
    name_en: Optional[str] = Field(None, max_length=255)
    country_id: Optional[int] = None
    region_id: Optional[int] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    population: Optional[int] = Field(None, ge=0)
    timezone: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CityResponse(CityBase):
    """Схема ответа для города"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CityListResponse(BaseModel):
    """Схема для списка городов"""

    cities: list[CityResponse]
    total: int
    page: int
    size: int
    pages: int

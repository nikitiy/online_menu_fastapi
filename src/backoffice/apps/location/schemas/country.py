from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CountryBase(BaseModel):
    """Базовая схема страны"""

    name: str = Field(..., description="Название страны", max_length=255)
    name_en: str = Field(
        ..., description="Название страны на английском", max_length=255
    )
    code: str = Field(..., description="ISO 3166-1 alpha-3 код", max_length=3)
    code_alpha2: str = Field(..., description="ISO 3166-1 alpha-2 код", max_length=2)
    phone_code: Optional[str] = Field(None, description="Телефонный код", max_length=10)
    currency_code: Optional[str] = Field(None, description="Код валюты", max_length=3)
    timezone: Optional[str] = Field(None, description="Временная зона", max_length=50)
    description: Optional[str] = Field(None, description="Описание")
    is_active: bool = Field(True, description="Активна ли страна")


class CountryCreate(CountryBase):
    """Схема для создания страны"""

    pass


class CountryUpdate(BaseModel):
    """Схема для обновления страны"""

    name: Optional[str] = Field(None, max_length=255)
    name_en: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=3)
    code_alpha2: Optional[str] = Field(None, max_length=2)
    phone_code: Optional[str] = Field(None, max_length=10)
    currency_code: Optional[str] = Field(None, max_length=3)
    timezone: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CountryResponse(CountryBase):
    """Схема ответа для страны"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CountryListResponse(BaseModel):
    """Схема для списка стран"""

    countries: list[CountryResponse]
    total: int
    page: int
    size: int
    pages: int

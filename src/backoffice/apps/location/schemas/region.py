from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RegionBase(BaseModel):
    """Базовая схема региона"""

    name: str = Field(..., description="Название региона", max_length=255)
    name_en: str = Field(
        ..., description="Название региона на английском", max_length=255
    )
    code: Optional[str] = Field(None, description="Код региона", max_length=20)
    country_id: int = Field(..., description="ID страны")
    description: Optional[str] = Field(None, description="Описание")
    is_active: bool = Field(True, description="Активен ли регион")


class RegionCreate(RegionBase):
    """Схема для создания региона"""

    pass


class RegionUpdate(BaseModel):
    """Схема для обновления региона"""

    name: Optional[str] = Field(None, max_length=255)
    name_en: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=20)
    country_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RegionResponse(RegionBase):
    """Схема ответа для региона"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RegionListResponse(BaseModel):
    """Схема для списка регионов"""

    regions: list[RegionResponse]
    total: int
    page: int
    size: int
    pages: int

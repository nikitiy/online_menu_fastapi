from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MenuItemBase(BaseModel):
    """Базовая схема для MenuItem."""

    name: str = Field(..., min_length=1, max_length=255, description="Название блюда")
    description: str = Field(..., min_length=1, description="Описание блюда")
    category_id: int = Field(..., description="ID категории")
    grams: int = Field(..., gt=0, description="Вес в граммах")
    kilocalories: Optional[int] = Field(None, ge=0, description="Калории")
    proteins: Optional[int] = Field(None, ge=0, description="Белки")
    fats: Optional[int] = Field(None, ge=0, description="Жиры")
    carbohydrated: Optional[int] = Field(None, ge=0, description="Углеводы")
    is_template: bool = Field(False, description="Является ли шаблоном")
    owner_company_id: Optional[int] = Field(
        None, description="ID компании-владельца (для не шаблонных позиций)"
    )


class MenuItemCreate(MenuItemBase):
    """Схема для создания MenuItem."""

    pass


class MenuItemUpdate(BaseModel):
    """Схема для обновления MenuItem."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    category_id: Optional[int] = None
    grams: Optional[int] = Field(None, gt=0)
    kilocalories: Optional[int] = Field(None, ge=0)
    proteins: Optional[int] = Field(None, ge=0)
    fats: Optional[int] = Field(None, ge=0)
    carbohydrated: Optional[int] = Field(None, ge=0)
    is_template: Optional[bool] = None


class MenuItemResponse(MenuItemBase):
    """Схема для ответа с MenuItem."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    breadcrumbs: List[Dict[str, str]] = Field(..., description="Хлебные крошки")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MenuItemListResponse(BaseModel):
    """Схема для списка MenuItem."""

    model_config = ConfigDict(from_attributes=True)

    items: List[MenuItemResponse]
    total: int
    page: int
    size: int
    pages: int

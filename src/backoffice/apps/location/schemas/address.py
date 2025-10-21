from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AddressBase(BaseModel):
    """Базовая схема адреса"""

    house_number: Optional[str] = Field(None, description="Номер дома", max_length=20)
    building: Optional[str] = Field(None, description="Корпус", max_length=20)
    apartment: Optional[str] = Field(None, description="Квартира", max_length=20)
    entrance: Optional[str] = Field(None, description="Подъезд", max_length=20)
    floor: Optional[int] = Field(None, description="Этаж", ge=0)
    street_id: int = Field(..., description="ID улицы")
    latitude: Optional[float] = Field(None, description="Широта", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="Долгота", ge=-180, le=180)
    postal_code: Optional[str] = Field(
        None, description="Почтовый индекс", max_length=20
    )
    description: Optional[str] = Field(None, description="Описание")
    is_verified: bool = Field(False, description="Проверен ли адрес")
    is_active: bool = Field(True, description="Активен ли адрес")
    external_id: Optional[str] = Field(None, description="Внешний ID", max_length=100)
    geocoder_provider: Optional[str] = Field(
        None, description="Провайдер геокодера", max_length=50
    )


class AddressCreate(AddressBase):
    """Схема для создания адреса"""

    pass


class AddressUpdate(BaseModel):
    """Схема для обновления адреса"""

    house_number: Optional[str] = Field(None, max_length=20)
    building: Optional[str] = Field(None, max_length=20)
    apartment: Optional[str] = Field(None, max_length=20)
    entrance: Optional[str] = Field(None, max_length=20)
    floor: Optional[int] = Field(None, ge=0)
    street_id: Optional[int] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    postal_code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None
    external_id: Optional[str] = Field(None, max_length=100)
    geocoder_provider: Optional[str] = Field(None, max_length=50)


class AddressResponse(AddressBase):
    """Схема ответа для адреса"""

    id: int
    full_address: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AddressListResponse(BaseModel):
    """Схема для списка адресов"""

    addresses: list[AddressResponse]
    total: int
    page: int
    size: int
    pages: int

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MenuImageBase(BaseModel):
    """Базовая схема изображения меню"""

    alt_text: Optional[str] = Field(
        None, description="Альтернативный текст изображения"
    )
    display_order: int = Field(0, description="Порядок отображения")
    is_primary: bool = Field(False, description="Является ли изображение основным")


class MenuImageCreate(MenuImageBase):
    """Схема для создания изображения"""

    menu_item_id: int = Field(..., description="ID элемента меню")


class MenuImageUpdate(BaseModel):
    """Схема для обновления изображения"""

    alt_text: Optional[str] = Field(
        None, description="Альтернативный текст изображения"
    )
    display_order: Optional[int] = Field(None, description="Порядок отображения")
    is_primary: Optional[bool] = Field(
        None, description="Является ли изображение основным"
    )
    is_active: Optional[bool] = Field(None, description="Активно ли изображение")


class MenuImageResponse(MenuImageBase):
    """Схема ответа с изображением"""

    id: int = Field(..., description="ID изображения")
    filename: str = Field(..., description="Имя файла")
    original_filename: str = Field(..., description="Оригинальное имя файла")
    file_path: str = Field(..., description="Путь к файлу в S3")
    file_size: int = Field(..., description="Размер файла в байтах")
    mime_type: str = Field(..., description="MIME тип файла")
    width: Optional[int] = Field(None, description="Ширина изображения")
    height: Optional[int] = Field(None, description="Высота изображения")
    url: str = Field(..., description="URL изображения")
    thumbnails: List[dict] = Field(
        default_factory=list, description="Миниатюры изображения"
    )
    is_active: bool = Field(..., description="Активно ли изображение")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")
    menu_item_id: int = Field(..., description="ID элемента меню")

    class Config:
        from_attributes = True


class MenuImageListResponse(BaseModel):
    """Схема ответа со списком изображений"""

    images: List[MenuImageResponse] = Field(..., description="Список изображений")
    total: int = Field(..., description="Общее количество изображений")


class MenuImageUploadResponse(BaseModel):
    """Схема ответа при загрузке изображения"""

    success: bool = Field(..., description="Успешность загрузки")
    message: str = Field(..., description="Сообщение")
    image: MenuImageResponse = Field(..., description="Загруженное изображение")


class MenuImageDeleteResponse(BaseModel):
    """Схема ответа при удалении изображения"""

    success: bool = Field(..., description="Успешность удаления")
    message: str = Field(..., description="Сообщение")


class MenuImagePresignedUrlResponse(BaseModel):
    """Схема ответа с presigned URL"""

    url: str = Field(..., description="Presigned URL")
    expires_at: datetime = Field(..., description="Время истечения URL")
    image_id: int = Field(..., description="ID изображения")


class ThumbnailInfo(BaseModel):
    """Информация о миниатюре"""

    size: str = Field(..., description="Размер миниатюры (small, medium, large)")
    width: int = Field(..., description="Ширина миниатюры")
    height: int = Field(..., description="Высота миниатюры")
    file_path: str = Field(..., description="Путь к файлу миниатюры")
    url: str = Field(..., description="URL миниатюры")

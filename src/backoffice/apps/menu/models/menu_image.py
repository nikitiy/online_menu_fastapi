from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backoffice.models import Base, CreatedUpdatedMixin, IdMixin


class MenuImage(Base, IdMixin, CreatedUpdatedMixin):
    """Модель для изображений элементов меню"""
    __repr_fields__ = ("filename", "menu_item_id", "is_primary")

    # Основные поля
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # Путь в S3
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Размер в байтах
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Метаданные изображения
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    alt_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Связь с элементом меню
    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    menu_item: Mapped["MenuItem"] = relationship(  # type: ignore
        back_populates="images", passive_deletes=True
    )

    # Порядок отображения (для множественных изображений)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Статус изображения
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    

    @property
    def file_extension(self) -> str:
        """Получить расширение файла"""
        return self.filename.split(".")[-1].lower() if "." in self.filename else ""

    @property
    def is_image(self) -> bool:
        """Проверить, является ли файл изображением"""
        image_extensions = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "svg"}
        return self.file_extension in image_extensions

    @property
    def display_size(self) -> str:
        """Получить размер файла в читаемом формате"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

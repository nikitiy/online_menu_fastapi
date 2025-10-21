from typing import List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backoffice.apps.menu.models.menu_image import MenuImage
from src.backoffice.apps.menu.models.menu_item import MenuItem
from src.backoffice.core.dependencies import SessionDep
from src.backoffice.core.services.s3_client import s3_client


class MenuImageService:
    """Сервис для работы с изображениями меню"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upload_image(
        self,
        menu_item_id: int,
        file: UploadFile,
        alt_text: Optional[str] = None,
        is_primary: bool = False,
        display_order: int = 0,
    ) -> MenuImage:
        """
        Загрузить изображение для элемента меню

        Args:
            menu_item_id: ID элемента меню
            file: Файл изображения
            alt_text: Альтернативный текст
            is_primary: Является ли изображение основным
            display_order: Порядок отображения

        Returns:
            MenuImage: Созданная запись изображения
        """
        # Проверка существования элемента меню
        menu_item = await self._get_menu_item(menu_item_id)

        # Загрузка файла в S3
        upload_result = await s3_client.upload_file(file, folder="menu-images")

        # Если это основное изображение, снимаем флаг с других
        if is_primary:
            await self._unset_primary_images(menu_item_id)

        # Создание записи в БД
        menu_image = MenuImage(
            filename=upload_result["filename"],
            original_filename=upload_result["original_filename"],
            file_path=upload_result["file_path"],
            file_size=upload_result["file_size"],
            mime_type=upload_result["mime_type"],
            width=upload_result.get("width"),
            height=upload_result.get("height"),
            alt_text=alt_text,
            menu_item_id=menu_item_id,
            display_order=display_order,
            is_primary=is_primary,
            is_active=True,
        )

        self.session.add(menu_image)
        await self.session.commit()
        await self.session.refresh(menu_image)

        return menu_image

    async def get_images_by_menu_item(self, menu_item_id: int) -> List[MenuImage]:
        """
        Получить все изображения элемента меню

        Args:
            menu_item_id: ID элемента меню

        Returns:
            List[MenuImage]: Список изображений
        """
        stmt = (
            select(MenuImage)
            .where(MenuImage.menu_item_id == menu_item_id, MenuImage.is_active == True)
            .order_by(MenuImage.display_order, MenuImage.updated_at)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_primary_image(self, menu_item_id: int) -> Optional[MenuImage]:
        """
        Получить основное изображение элемента меню

        Args:
            menu_item_id: ID элемента меню

        Returns:
            Optional[MenuImage]: Основное изображение или None
        """
        stmt = select(MenuImage).where(
            MenuImage.menu_item_id == menu_item_id,
            MenuImage.is_primary == True,
            MenuImage.is_active == True,
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_image(
        self,
        image_id: int,
        alt_text: Optional[str] = None,
        is_primary: Optional[bool] = None,
        display_order: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> MenuImage:
        """
        Обновить изображение

        Args:
            image_id: ID изображения
            alt_text: Альтернативный текст
            is_primary: Является ли основным
            display_order: Порядок отображения
            is_active: Активно ли изображение

        Returns:
            MenuImage: Обновленное изображение
        """
        image = await self._get_image(image_id)

        # Если устанавливаем как основное, снимаем флаг с других
        if is_primary and not image.is_primary:
            await self._unset_primary_images(image.menu_item_id)

        # Обновление полей
        if alt_text is not None:
            image.alt_text = alt_text
        if is_primary is not None:
            image.is_primary = is_primary
        if display_order is not None:
            image.display_order = display_order
        if is_active is not None:
            image.is_active = is_active

        # updated_at автоматически обновится благодаря CreatedUpdatedMixin

        await self.session.commit()
        await self.session.refresh(image)

        return image

    async def delete_image(self, image_id: int) -> bool:
        """
        Удалить изображение

        Args:
            image_id: ID изображения

        Returns:
            bool: True если удалено успешно
        """
        image = await self._get_image(image_id)

        # Удаление файла из S3
        await s3_client.delete_file(image.file_path)

        # Удаление миниатюр
        if image.file_path:
            # Удаление миниатюр (предполагаем стандартную структуру папок)
            thumbnail_path = image.file_path.replace(
                "menu-images/", "menu-images/thumbnails/"
            )
            await s3_client.delete_file(thumbnail_path)

        # Удаление записи из БД
        await self.session.delete(image)
        await self.session.commit()

        return True

    async def set_primary_image(self, image_id: int) -> MenuImage:
        """
        Установить изображение как основное

        Args:
            image_id: ID изображения

        Returns:
            MenuImage: Обновленное изображение
        """
        image = await self._get_image(image_id)

        # Снимаем флаг с других изображений этого элемента меню
        await self._unset_primary_images(image.menu_item_id)

        # Устанавливаем как основное
        image.is_primary = True
        # updated_at автоматически обновится благодаря CreatedUpdatedMixin

        await self.session.commit()
        await self.session.refresh(image)

        return image

    async def get_presigned_url(self, image_id: int, expiry_hours: int = 1) -> str:
        """
        Получить presigned URL для изображения

        Args:
            image_id: ID изображения
            expiry_hours: Время жизни URL в часах

        Returns:
            str: Presigned URL
        """
        image = await self._get_image(image_id)
        return await s3_client.get_presigned_url(image.file_path, expiry_hours)

    async def _get_menu_item(self, menu_item_id: int) -> MenuItem:
        """Получить элемент меню по ID"""
        stmt = select(MenuItem).where(MenuItem.id == menu_item_id)
        result = await self.session.execute(stmt)
        menu_item = result.scalar_one_or_none()

        if not menu_item:
            raise HTTPException(status_code=404, detail="Элемент меню не найден")

        return menu_item

    async def _get_image(self, image_id: int) -> MenuImage:
        """Получить изображение по ID"""
        stmt = select(MenuImage).where(MenuImage.id == image_id)
        result = await self.session.execute(stmt)
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(status_code=404, detail="Изображение не найдено")

        return image

    async def _unset_primary_images(self, menu_item_id: int) -> None:
        """Снять флаг основного изображения со всех изображений элемента меню"""
        stmt = select(MenuImage).where(
            MenuImage.menu_item_id == menu_item_id, MenuImage.is_primary == True
        )
        result = await self.session.execute(stmt)
        images = result.scalars().all()

        for image in images:
            image.is_primary = False
            # updated_at автоматически обновится благодаря CreatedUpdatedMixin

        await self.session.commit()


# Фабрика для создания сервиса
async def get_menu_image_service(session: SessionDep) -> MenuImageService:
    """Получить экземпляр сервиса изображений меню"""
    return MenuImageService(session)

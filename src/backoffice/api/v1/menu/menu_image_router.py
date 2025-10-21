from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     UploadFile)
from sqlalchemy import select

from src.backoffice.apps.menu.models.menu_image import MenuImage
from src.backoffice.apps.menu.schemas.menu_image import (
    MenuImageDeleteResponse, MenuImageListResponse,
    MenuImagePresignedUrlResponse, MenuImageResponse, MenuImageUpdate,
    MenuImageUploadResponse)
from src.backoffice.apps.menu.services.menu_image_service import (
    MenuImageService, get_menu_image_service)

router = APIRouter(prefix="/menu-images", tags=["Menu Images"])


@router.post("/upload", response_model=MenuImageUploadResponse)
async def upload_menu_image(
    menu_item_id: int = Form(..., description="ID элемента меню"),
    file: UploadFile = File(..., description="Файл изображения"),
    alt_text: str = Form(None, description="Альтернативный текст"),
    is_primary: bool = Form(False, description="Является ли основным изображением"),
    display_order: int = Form(0, description="Порядок отображения"),
    image_service: MenuImageService = Depends(get_menu_image_service),
):
    """
    Загрузить изображение для элемента меню

    - **menu_item_id**: ID элемента меню
    - **file**: Файл изображения (jpg, png, gif, webp, bmp, svg)
    - **alt_text**: Альтернативный текст для изображения
    - **is_primary**: Установить как основное изображение
    - **display_order**: Порядок отображения (0 - первый)
    """
    try:
        image = await image_service.upload_image(
            menu_item_id=menu_item_id,
            file=file,
            alt_text=alt_text,
            is_primary=is_primary,
            display_order=display_order,
        )

        return MenuImageUploadResponse(
            success=True,
            message="Изображение успешно загружено",
            image=MenuImageResponse.model_validate(image, from_attributes=True),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/menu-item/{menu_item_id}", response_model=MenuImageListResponse)
async def get_menu_item_images(
    menu_item_id: int, image_service: MenuImageService = Depends(get_menu_image_service)
):
    """
    Получить все изображения элемента меню

    - **menu_item_id**: ID элемента меню
    """
    try:
        images = await image_service.get_images_by_menu_item(menu_item_id)

        return MenuImageListResponse(
            images=[
                MenuImageResponse.model_validate(img, from_attributes=True)
                for img in images
            ],
            total=len(images),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/menu-item/{menu_item_id}/primary", response_model=MenuImageResponse)
async def get_primary_menu_image(
    menu_item_id: int, image_service: MenuImageService = Depends(get_menu_image_service)
):
    """
    Получить основное изображение элемента меню

    - **menu_item_id**: ID элемента меню
    """
    try:
        image = await image_service.get_primary_image(menu_item_id)
        if not image:
            raise HTTPException(
                status_code=404, detail="Основное изображение не найдено"
            )

        return MenuImageResponse.model_validate(image, from_attributes=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{image_id}", response_model=MenuImageResponse)
async def get_menu_image(
    image_id: int, image_service: MenuImageService = Depends(get_menu_image_service)
):
    """
    Получить изображение по ID

    - **image_id**: ID изображения
    """
    try:
        # Используем внутренний метод сервиса для получения изображения
        stmt = select(MenuImage).where(MenuImage.id == image_id)
        result = await image_service.session.execute(stmt)
        image = result.scalar_one_or_none()

        if not image:
            raise HTTPException(status_code=404, detail="Изображение не найдено")

        return MenuImageResponse.model_validate(image, from_attributes=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{image_id}", response_model=MenuImageResponse)
async def update_menu_image(
    image_id: int,
    image_update: MenuImageUpdate,
    image_service: MenuImageService = Depends(get_menu_image_service),
):
    """
    Обновить изображение

    - **image_id**: ID изображения
    - **image_update**: Данные для обновления
    """
    try:
        image = await image_service.update_image(
            image_id=image_id,
            alt_text=image_update.alt_text,
            is_primary=image_update.is_primary,
            display_order=image_update.display_order,
            is_active=image_update.is_active,
        )

        return MenuImageResponse.model_validate(image, from_attributes=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{image_id}/set-primary", response_model=MenuImageResponse)
async def set_primary_image(
    image_id: int, image_service: MenuImageService = Depends(get_menu_image_service)
):
    """
    Установить изображение как основное

    - **image_id**: ID изображения
    """
    try:
        image = await image_service.set_primary_image(image_id)
        return MenuImageResponse.model_validate(image, from_attributes=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{image_id}", response_model=MenuImageDeleteResponse)
async def delete_menu_image(
    image_id: int, image_service: MenuImageService = Depends(get_menu_image_service)
):
    """
    Удалить изображение

    - **image_id**: ID изображения
    """
    try:
        success = await image_service.delete_image(image_id)

        if success:
            return MenuImageDeleteResponse(
                success=True, message="Изображение успешно удалено"
            )
        else:
            raise HTTPException(
                status_code=400, detail="Ошибка при удалении изображения"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{image_id}/presigned-url", response_model=MenuImagePresignedUrlResponse)
async def get_presigned_url(
    image_id: int,
    expiry_hours: int = Query(1, description="Время жизни URL в часах", ge=1, le=24),
    image_service: MenuImageService = Depends(get_menu_image_service),
):
    """
    Получить presigned URL для доступа к изображению

    - **image_id**: ID изображения
    - **expiry_hours**: Время жизни URL в часах (1-24)
    """
    try:
        url = await image_service.get_presigned_url(image_id, expiry_hours)

        from datetime import datetime, timedelta, timezone

        expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)

        return MenuImagePresignedUrlResponse(
            url=url, expires_at=expires_at, image_id=image_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

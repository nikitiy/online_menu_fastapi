from fastapi import APIRouter, HTTPException, Query, status

from src.backoffice.apps.menu.schemas.menu_item import (MenuItemCreate,
                                                        MenuItemListResponse,
                                                        MenuItemResponse,
                                                        MenuItemUpdate)
from src.backoffice.apps.menu.services.menu_item_service import MenuItemService
from src.backoffice.core.dependencies import SessionDep

router = APIRouter(prefix="/items", tags=["menu-items"])


@router.post("/", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    payload: MenuItemCreate,
    session: SessionDep,
):
    service = MenuItemService(session)
    # Валидация согласованности template/owner делается чек-констрейнтом на уровне БД
    item = await service.create(payload)
    return item


@router.get("/", response_model=MenuItemListResponse)
async def list_menu_items(
    session: SessionDep,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category_id: int | None = None,
    is_template: bool | None = None,
    search: str | None = None,
    company_id: int | None = Query(
        None,
        description="Если задан, будут показаны шаблоны и элементы этой компании",
    ),
):
    service = MenuItemService(session)
    return await service.get_list(
        page=page,
        size=size,
        category_id=category_id,
        is_template=is_template,
        search=search,
        visible_for_company_id=company_id,
    )


@router.get("/{slug}", response_model=MenuItemResponse)
async def get_menu_item(slug: str, session: SessionDep):
    service = MenuItemService(session)
    item = await service.get_by_slug(slug)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item


@router.patch("/{slug}", response_model=MenuItemResponse)
async def update_menu_item(
    slug: str,
    payload: MenuItemUpdate,
    session: SessionDep,
):
    service = MenuItemService(session)
    item = await service.update_by_slug(slug, payload)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(
    slug: str,
    session: SessionDep,
):
    service = MenuItemService(session)
    deleted = await service.delete_by_slug(slug)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return None

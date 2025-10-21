from typing import List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backoffice.apps.menu.models.menu_item import MenuItem
from src.backoffice.apps.menu.schemas.menu_item import (MenuItemCreate,
                                                        MenuItemListResponse,
                                                        MenuItemUpdate)
from src.backoffice.core.services import SlugService


class MenuItemService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, menu_item_data: MenuItemCreate) -> MenuItem:
        """
        Create new MenuItem.

        Args:
            menu_item_data: Data for creating MenuItem

        Returns:
            Created MenuItem
        """
        menu_item = MenuItem(
            name=menu_item_data.name,
            description=menu_item_data.description,
            category_id=menu_item_data.category_id,
            grams=menu_item_data.grams,
            kilocalories=menu_item_data.kilocalories,
            proteins=menu_item_data.proteins,
            fats=menu_item_data.fats,
            carbohydrated=menu_item_data.carbohydrated,
            is_template=menu_item_data.is_template,
            owner_company_id=menu_item_data.owner_company_id,
            slug="",
        )

        self.session.add(menu_item)
        await self.session.flush()

        SlugService.set_slug(instance=menu_item, name=menu_item.name)

        return menu_item

    async def get_by_id(self, menu_item_id: int) -> Optional[MenuItem]:
        """
        Get MenuItem by ID.

        Args:
            menu_item_id: ID MenuItem

        Returns:
            MenuItem or None
        """
        return await self.session.get(MenuItem, menu_item_id)

    async def get_by_slug(self, slug: str) -> Optional[MenuItem]:
        """
        Get MenuItem by slug.

        Args:
            slug: Slug MenuItem

        Returns:
            MenuItem or None
        """
        stmt = select(MenuItem).where(MenuItem.slug == slug)
        return await self.session.scalar(stmt)

    async def get_list(
        self,
        page: int = 1,
        size: int = 20,
        category_id: Optional[int] = None,
        is_template: Optional[bool] = None,
        search: Optional[str] = None,
        visible_for_company_id: Optional[int] = None,  # TODO изменить, мы должны компанию получать иным способом, что просто ее передавать
                                                       # Нужно вообще будет убрать это поле
    ) -> MenuItemListResponse:
        """
        Get list MenuItem with pagination and filtering.

        Args:
            page: Page number (starts from 1)
            size: Pase size
            category_id: Filter by category id
            is_template: Filter by is_template
            search: Search by title and description

        Returns:
            List MenuItem with pagination metadata
            :param search:
            :param is_template:
            :param category_id:
            :param size:
            :param page:
            :param visible_for_company_id:
        """

        stmt = select(MenuItem)
        count_stmt = select(func.count(MenuItem.id))

        filters = []

        if category_id is not None:
            filters.append(MenuItem.category_id == category_id)

        if is_template is not None:
            filters.append(MenuItem.is_template == is_template)

        if search:
            search_filter = and_(
                MenuItem.name.ilike(f"%{search}%"),
                MenuItem.description.ilike(f"%{search}%"),
            )
            filters.append(search_filter)

        # Видимость: шаблоны видны всем, company-специфичные — только своей компании
        if visible_for_company_id is not None:
            visibility_filter = or_(
                MenuItem.is_template == True,
                MenuItem.owner_company_id == visible_for_company_id,
            )
            filters.append(visibility_filter)

        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))

        total = await self.session.scalar(count_stmt)

        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size)

        result = await self.session.execute(stmt)
        items = result.scalars().all()

        pages = (total + size - 1) // size

        return MenuItemListResponse(
            items=items, total=total, page=page, size=size, pages=pages
        )

    async def update_by_slug(
        self, menu_item_slug: str, update_data: MenuItemUpdate
    ) -> Optional[MenuItem]:
        """
        Update MenuItem.

        Args:
            menu_item_slug: MenuItem.slug
            update_data: Data for updating MenuItem

        Returns:
            Updated MenuItem or None
        """
        menu_item = await self.get_by_slug(menu_item_slug)
        if not menu_item:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(menu_item, field, value)

        if "name" in update_dict:
            SlugService.set_slug(instance=menu_item, name=menu_item.name)

        return menu_item

    async def delete_by_slug(self, menu_item_slug: str) -> bool:
        """
        Delete MenuItem.

        Args:
            menu_item_slug: MenuItem.slug

        Returns:
            True if deleted, False if not found
        """
        menu_item = await self.get_by_slug(menu_item_slug)
        if not menu_item:
            return False

        await self.session.delete(menu_item)
        return True

    async def get_templates(self) -> List[MenuItem]:
        """
        Get all MenuItem templates.

        Returns:
            List MenuItem templates
        """
        stmt = select(MenuItem).where(MenuItem.is_template == True)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

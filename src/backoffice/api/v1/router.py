from fastapi import APIRouter

from src.backoffice.api.health import router as health_router
from src.backoffice.api.v1.auth import auth_router
from src.backoffice.api.v1.company.members_router import \
    router as company_members_router
from src.backoffice.api.v1.location import geocoding_router, location_router
from src.backoffice.api.v1.menu.menu_image_router import \
    router as menu_image_router
from src.backoffice.api.v1.menu.menu_item_router import \
    router as menu_item_router

api_router = APIRouter()

# Auth routes
api_router.include_router(auth_router)

# Location routes
api_router.include_router(geocoding_router, prefix="/location")
api_router.include_router(location_router, prefix="/location")

# Menu routes
api_router.include_router(menu_image_router, prefix="/menu")
api_router.include_router(menu_item_router, prefix="/menu")

# Company routes
api_router.include_router(company_members_router, prefix="/company")

# Health
api_router.include_router(health_router)

__all__ = ("api_router",)

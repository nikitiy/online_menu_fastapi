from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.backoffice.apps.location.schemas.geocoding import (
    GeocodingRequest, GeocodingResultResponse, GeocodingSearchRequest,
    GeocodingSearchResponse, ReverseGeocodingRequest)
from src.backoffice.apps.location.services.geocoder_service import \
    GeocoderService
from src.backoffice.core.config import geocoding_settings
from src.backoffice.core.dependencies import SessionDep

router = APIRouter(prefix="/geocoding", tags=["geocoding"])


async def get_geocoder_service(session: SessionDep) -> GeocoderService:
    """Dependency для получения сервиса геокодирования"""
    return GeocoderService(session)


@router.post("/geocode", response_model=List[GeocodingResultResponse])
async def geocode_address(
    request: GeocodingRequest,
    geocoder_service: GeocoderService = Depends(get_geocoder_service),
):
    """
    Геокодирование адреса

    Преобразует текстовый адрес в географические координаты (широта, долгота).
    Поддерживает множественные провайдеры: Google Maps, Yandex Maps, OpenStreetMap Nominatim.
    """
    try:
        results = await geocoder_service.geocode(request)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")


@router.post("/search", response_model=GeocodingSearchResponse)
async def search_addresses(
    request: GeocodingSearchRequest,
    geocoder_service: GeocoderService = Depends(get_geocoder_service),
):
    """
    Поиск адресов

    Выполняет поиск адресов по запросу с возможностью ограничения количества результатов.
    """
    try:
        results = await geocoder_service.search(request)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Address search failed: {str(e)}")


@router.post("/reverse", response_model=List[GeocodingResultResponse])
async def reverse_geocode(
    request: ReverseGeocodingRequest,
    geocoder_service: GeocoderService = Depends(get_geocoder_service),
):
    """
    Обратное геокодирование

    Преобразует географические координаты в текстовый адрес.
    """
    try:
        results = await geocoder_service.reverse_geocode(request)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Reverse geocoding failed: {str(e)}"
        )


@router.get("/providers", response_model=List[str])
async def get_available_providers():
    """
    Получение списка доступных провайдеров геокодирования

    Возвращает список провайдеров, которые настроены и доступны для использования.
    """
    available_providers = []

    for provider_name, config in geocoding_settings.providers_config.items():
        if config.get("enabled", False):
            available_providers.append(provider_name)

    return available_providers


@router.get("/providers/{provider}/status")
async def get_provider_status(provider: str):
    """
    Получение статуса провайдера

    Возвращает информацию о доступности и конфигурации конкретного провайдера.
    """
    if provider not in geocoding_settings.providers_config:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

    config = geocoding_settings.providers_config[provider]

    return {
        "provider": provider,
        "enabled": config.get("enabled", False),
        "rate_limit": config.get("rate_limit"),
        "timeout": config.get("timeout"),
        "has_api_key": bool(config.get("api_key")),
    }


@router.get("/health")
async def health_check():
    """
    Проверка здоровья сервиса геокодирования

    Возвращает статус доступности сервиса и его компонентов.
    """
    health_status = {
        "status": "healthy",
        "providers": {},
        "cache_ttl": geocoding_settings.cache_ttl,
        "rate_limit_requests": geocoding_settings.rate_limit_requests,
        "rate_limit_period": geocoding_settings.rate_limit_period,
    }

    for provider_name, config in geocoding_settings.providers_config.items():
        health_status["providers"][provider_name] = {
            "enabled": config.get("enabled", False),
            "configured": bool(config.get("api_key") or provider_name == "nominatim"),
        }

    return health_status

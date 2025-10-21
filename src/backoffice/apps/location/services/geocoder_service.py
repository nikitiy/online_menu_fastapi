import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backoffice.apps.location.models import GeocodingResult
from src.backoffice.apps.location.schemas.geocoding import (
    GeocodingRequest, GeocodingResultResponse, GeocodingSearchRequest,
    GeocodingSearchResponse, ReverseGeocodingRequest)
from src.backoffice.core.config import geocoding_settings

logger = logging.getLogger(__name__)


class GeocodingProviderInterface(ABC):
    """Интерфейс для провайдеров геокодирования"""

    @abstractmethod
    async def geocode(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Геокодирование адреса"""
        pass

    @abstractmethod
    async def reverse_geocode(
        self, latitude: float, longitude: float, **kwargs
    ) -> List[Dict[str, Any]]:
        """Обратное геокодирование координат"""
        pass

    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Парсинг ответа провайдера"""
        pass


class GoogleGeocodingProvider(GeocodingProviderInterface):
    """Google Maps Geocoding API провайдер"""

    def __init__(self, api_key: str, base_url: str, timeout: int = 10):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    async def geocode(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Геокодирование через Google Maps API"""
        params = {
            "address": query,
            "key": self.api_key,
            "language": kwargs.get("language", "ru"),
            "region": kwargs.get("region"),
            "bounds": kwargs.get("bounds"),
            "components": kwargs.get("components"),
        }

        # Убираем None значения
        params = {k: v for k, v in params.items() if v is not None}

        url = f"{self.base_url}?{urlencode(params)}"

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_response(data)
                else:
                    logger.error(f"Google Geocoding API error: {response.status}")
                    return []

    async def reverse_geocode(
        self, latitude: float, longitude: float, **kwargs
    ) -> List[Dict[str, Any]]:
        """Обратное геокодирование через Google Maps API"""
        params = {
            "latlng": f"{latitude},{longitude}",
            "key": self.api_key,
            "language": kwargs.get("language", "ru"),
            "result_type": kwargs.get("result_type"),
        }

        params = {k: v for k, v in params.items() if v is not None}
        url = f"{self.base_url}?{urlencode(params)}"

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_response(data)
                else:
                    logger.error(
                        f"Google Reverse Geocoding API error: {response.status}"
                    )
                    return []

    def parse_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Парсинг ответа Google Maps API"""
        results = []

        if response.get("status") != "OK":
            logger.warning(f"Google Geocoding API status: {response.get('status')}")
            return results

        for item in response.get("results", []):
            geometry = item.get("geometry", {})
            location = geometry.get("location", {})

            # Парсинг компонентов адреса
            address_components = {}
            for component in item.get("address_components", []):
                types = component.get("types", [])
                if "country" in types:
                    address_components["country"] = component.get("long_name")
                elif "administrative_area_level_1" in types:
                    address_components["region"] = component.get("long_name")
                elif "locality" in types or "administrative_area_level_2" in types:
                    address_components["city"] = component.get("long_name")
                elif "route" in types:
                    address_components["street"] = component.get("long_name")
                elif "street_number" in types:
                    address_components["house_number"] = component.get("long_name")
                elif "postal_code" in types:
                    address_components["postal_code"] = component.get("long_name")

            result = {
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
                "formatted_address": item.get("formatted_address"),
                "place_id": item.get("place_id"),
                "place_type": ",".join(item.get("types", [])),
                "accuracy": geometry.get("location_type", "APPROXIMATE"),
                "confidence": (
                    1.0 if geometry.get("location_type") == "ROOFTOP" else 0.8
                ),
                "external_id": item.get("place_id"),
                "raw_response": json.dumps(item),
                **address_components,
            }
            results.append(result)

        return results


class YandexGeocodingProvider(GeocodingProviderInterface):
    """Yandex Maps Geocoding API провайдер"""

    def __init__(self, api_key: str, base_url: str, timeout: int = 10):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    async def geocode(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Геокодирование через Yandex Maps API"""
        params = {
            "geocode": query,
            "apikey": self.api_key,
            "format": "json",
            "results": kwargs.get("limit", 10),
            "lang": kwargs.get("language", "ru_RU"),
        }

        url = f"{self.base_url}?{urlencode(params)}"

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_response(data)
                else:
                    logger.error(f"Yandex Geocoding API error: {response.status}")
                    return []

    async def reverse_geocode(
        self, latitude: float, longitude: float, **kwargs
    ) -> List[Dict[str, Any]]:
        """Обратное геокодирование через Yandex Maps API"""
        query = f"{longitude},{latitude}"
        return await self.geocode(query, **kwargs)

    def parse_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Парсинг ответа Yandex Maps API"""
        results = []

        response_data = response.get("response", {})
        geo_objects = response_data.get("GeoObjectCollection", {}).get(
            "featureMember", []
        )

        for item in geo_objects:
            geo_object = item.get("GeoObject", {})
            point = geo_object.get("Point", {})
            pos = point.get("pos", "").split()

            if len(pos) == 2:
                longitude, latitude = float(pos[0]), float(pos[1])

                # Парсинг компонентов адреса
                meta_data = geo_object.get("metaDataProperty", {}).get(
                    "GeocoderMetaData", {}
                )
                address_components = meta_data.get("Address", {})

                result = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "formatted_address": geo_object.get("name"),
                    "place_id": geo_object.get("metaDataProperty", {})
                    .get("GeocoderMetaData", {})
                    .get("id"),
                    "place_type": meta_data.get("kind"),
                    "accuracy": (
                        "ROOFTOP"
                        if meta_data.get("precision") == "exact"
                        else "APPROXIMATE"
                    ),
                    "confidence": 1.0 if meta_data.get("precision") == "exact" else 0.7,
                    "external_id": geo_object.get("metaDataProperty", {})
                    .get("GeocoderMetaData", {})
                    .get("id"),
                    "raw_response": json.dumps(geo_object),
                    "country": address_components.get("country"),
                    "region": address_components.get("AdministrativeArea", {}).get(
                        "AdministrativeAreaName"
                    ),
                    "city": address_components.get("Locality", {}).get("LocalityName"),
                    "street": address_components.get("Thoroughfare", {}).get(
                        "ThoroughfareName"
                    ),
                    "house_number": address_components.get("Premise", {}).get(
                        "PremiseNumber"
                    ),
                    "postal_code": address_components.get("postal_code"),
                }
                results.append(result)

        return results


class NominatimGeocodingProvider(GeocodingProviderInterface):
    """OpenStreetMap Nominatim провайдер"""

    def __init__(self, base_url: str, user_agent: str, timeout: int = 10):
        self.base_url = base_url
        self.user_agent = user_agent
        self.timeout = timeout

    async def geocode(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Геокодирование через Nominatim"""
        params = {
            "q": query,
            "format": "json",
            "limit": kwargs.get("limit", 10),
            "addressdetails": 1,
            "accept-language": kwargs.get("language", "ru"),
        }

        url = f"{self.base_url}/search?{urlencode(params)}"
        headers = {"User-Agent": self.user_agent}

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_response(data)
                else:
                    logger.error(f"Nominatim API error: {response.status}")
                    return []

    async def reverse_geocode(
        self, latitude: float, longitude: float, **kwargs
    ) -> List[Dict[str, Any]]:
        """Обратное геокодирование через Nominatim"""
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "addressdetails": 1,
            "accept-language": kwargs.get("language", "ru"),
        }

        url = f"{self.base_url}/reverse?{urlencode(params)}"
        headers = {"User-Agent": self.user_agent}

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_response(
                        [data] if isinstance(data, dict) else data
                    )
                else:
                    logger.error(f"Nominatim Reverse API error: {response.status}")
                    return []

    def parse_response(self, response: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Парсинг ответа Nominatim"""
        results = []

        for item in response:
            address = item.get("address", {})

            result = {
                "latitude": float(item.get("lat", 0)),
                "longitude": float(item.get("lon", 0)),
                "formatted_address": item.get("display_name"),
                "place_id": str(item.get("place_id", "")),
                "place_type": item.get("type"),
                "accuracy": (
                    "ROOFTOP" if item.get("class") == "building" else "APPROXIMATE"
                ),
                "confidence": 0.9 if item.get("class") == "building" else 0.6,
                "external_id": str(item.get("place_id", "")),
                "raw_response": json.dumps(item),
                "country": address.get("country"),
                "region": address.get("state"),
                "city": address.get("city")
                or address.get("town")
                or address.get("village"),
                "street": address.get("road"),
                "house_number": address.get("house_number"),
                "postal_code": address.get("postcode"),
            }
            results.append(result)

        return results


class GeocoderService:
    """Сервис геокодирования с поддержкой множественных провайдеров"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.providers = self._initialize_providers()

    @staticmethod
    def _initialize_providers() -> Dict[str, GeocodingProviderInterface]:
        """Инициализация провайдеров"""
        providers = {}

        # Google Maps
        if geocoding_settings.is_provider_enabled("google"):
            config = geocoding_settings.get_provider_config("google")
            providers["google"] = GoogleGeocodingProvider(
                api_key=config["api_key"],
                base_url=config["base_url"],
                timeout=config["timeout"],
            )

        # Yandex Maps
        if geocoding_settings.is_provider_enabled("yandex"):
            config = geocoding_settings.get_provider_config("yandex")
            providers["yandex"] = YandexGeocodingProvider(
                api_key=config["api_key"],
                base_url=config["base_url"],
                timeout=config["timeout"],
            )

        # Nominatim
        if geocoding_settings.is_provider_enabled("nominatim"):
            config = geocoding_settings.get_provider_config("nominatim")
            providers["nominatim"] = NominatimGeocodingProvider(
                base_url=config["base_url"],
                user_agent=config["user_agent"],
                timeout=config["timeout"],
            )

        return providers

    async def geocode(self, request: GeocodingRequest) -> List[GeocodingResultResponse]:
        """Геокодирование адреса"""
        # Проверяем кэш
        cached_results = await self._get_cached_results(request.query, request.provider)
        if cached_results:
            return cached_results

        # Выполняем геокодирование
        provider = self.providers.get(request.provider)
        if not provider:
            raise ValueError(f"Provider {request.provider} is not available")

        try:
            raw_results = await provider.geocode(
                request.query,
                language=request.language,
                region=request.region,
                bounds=request.bounds,
                components=request.components,
            )

            # Сохраняем результаты в БД
            results = []
            for raw_result in raw_results:
                result = await self._save_geocoding_result(
                    query=request.query,
                    provider=request.provider,
                    raw_result=raw_result,
                )
                results.append(GeocodingResultResponse.model_validate(result))

            return results

        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            # Сохраняем ошибку в БД
            await self._save_error_result(request.query, request.provider, str(e))
            return []

    async def search(self, request: GeocodingSearchRequest) -> GeocodingSearchResponse:
        """Поиск адресов"""
        results = await self.geocode(
            GeocodingRequest(
                query=request.query,
                provider=request.provider,
                language=request.language,
                region=request.region,
                bounds=request.bounds,
                components=request.components,
            )
        )

        # Ограничиваем количество результатов
        limited_results = results[: request.limit]

        return GeocodingSearchResponse(
            results=limited_results,
            total=len(limited_results),
            query=request.query,
            provider=request.provider,
        )

    async def reverse_geocode(
        self, request: ReverseGeocodingRequest
    ) -> List[GeocodingResultResponse]:
        """Обратное геокодирование"""
        provider = self.providers.get(request.provider)
        if not provider:
            raise ValueError(f"Provider {request.provider} is not available")

        try:
            raw_results = await provider.reverse_geocode(
                request.latitude,
                request.longitude,
                language=request.language,
                result_type=request.result_type,
            )

            # Сохраняем результаты в БД
            results = []
            for raw_result in raw_results:
                result = await self._save_geocoding_result(
                    query=f"{request.latitude},{request.longitude}",
                    provider=request.provider,
                    raw_result=raw_result,
                )
                results.append(GeocodingResultResponse.model_validate(result))

            return results

        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}")
            await self._save_error_result(
                f"{request.latitude},{request.longitude}", request.provider, str(e)
            )
            return []

    async def _get_cached_results(
        self, query: str, provider: str
    ) -> Optional[List[GeocodingResultResponse]]:
        """Получение кэшированных результатов"""
        stmt = select(GeocodingResult).where(
            and_(
                GeocodingResult.query == query,
                GeocodingResult.provider == provider,
                GeocodingResult.is_successful == True,
                GeocodingResult.expires_at > datetime.now(timezone.utc),
            )
        )

        result = await self.db_session.execute(stmt)
        cached_results = result.scalars().all()

        if cached_results:
            return [GeocodingResultResponse.model_validate(r) for r in cached_results]

        return None

    async def _save_geocoding_result(
        self, query: str, provider: str, raw_result: Dict[str, Any]
    ) -> GeocodingResult:
        """Сохранение результата геокодирования в БД"""
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=geocoding_settings.cache_ttl)

        result = GeocodingResult(
            query=query,
            latitude=raw_result.get("latitude"),
            longitude=raw_result.get("longitude"),
            formatted_address=raw_result.get("formatted_address"),
            country=raw_result.get("country"),
            region=raw_result.get("region"),
            city=raw_result.get("city"),
            street=raw_result.get("street"),
            house_number=raw_result.get("house_number"),
            postal_code=raw_result.get("postal_code"),
            place_id=raw_result.get("place_id"),
            place_type=raw_result.get("place_type"),
            accuracy=raw_result.get("accuracy"),
            confidence=raw_result.get("confidence"),
            provider=provider,
            external_id=raw_result.get("external_id"),
            raw_response=raw_result.get("raw_response"),
            is_successful=True,
            expires_at=expires_at,
        )

        self.db_session.add(result)
        await self.db_session.commit()
        await self.db_session.refresh(result)

        return result

    async def _save_error_result(
        self, query: str, provider: str, error_message: str
    ) -> None:
        """Сохранение ошибки геокодирования в БД"""
        result = GeocodingResult(
            query=query,
            provider=provider,
            is_successful=False,
            error_message=error_message,
        )

        self.db_session.add(result)
        await self.db_session.commit()

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.backoffice.apps.location.schemas import (AddressCreate,
                                                  AddressListResponse,
                                                  AddressResponse, CityCreate,
                                                  CityListResponse,
                                                  CityResponse, CountryCreate,
                                                  CountryListResponse,
                                                  CountryResponse,
                                                  CountryUpdate, RegionCreate,
                                                  RegionListResponse,
                                                  RegionResponse, StreetCreate,
                                                  StreetListResponse,
                                                  StreetResponse)
from src.backoffice.apps.location.services.location_service import \
    LocationService
from src.backoffice.core.dependencies import SessionDep

router = APIRouter(prefix="/locations", tags=["locations"])


async def get_location_service(session: SessionDep) -> LocationService:
    """Dependency для получения сервиса локаций"""
    return LocationService(session)


# ==================== COUNTRIES ====================


@router.post("/countries", response_model=CountryResponse, status_code=201)
async def create_country(
    country_data: CountryCreate,
    location_service: LocationService = Depends(get_location_service),
):
    """Создание новой страны"""
    try:
        country = await location_service.create_country(country_data)
        return country
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to create country: {str(e)}"
        )


@router.get("/countries/{country_id}", response_model=CountryResponse)
async def get_country(
    country_id: int, location_service: LocationService = Depends(get_location_service)
):
    """Получение страны по ID"""
    country = await location_service.get_country(country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


@router.get("/countries", response_model=CountryListResponse)
async def get_countries(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    location_service: LocationService = Depends(get_location_service),
):
    """Получение списка стран с пагинацией и поиском"""
    try:
        countries = await location_service.get_countries(
            page=page, size=size, search=search, is_active=is_active
        )
        return countries
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get countries: {str(e)}"
        )


@router.put("/countries/{country_id}", response_model=CountryResponse)
async def update_country(
    country_id: int,
    country_data: CountryUpdate,
    location_service: LocationService = Depends(get_location_service),
):
    """Обновление страны"""
    try:
        country = await location_service.update_country(country_id, country_data)
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        return country
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to update country: {str(e)}"
        )


@router.delete("/countries/{country_id}", status_code=204)
async def delete_country(
    country_id: int, location_service: LocationService = Depends(get_location_service)
):
    """Удаление страны"""
    try:
        success = await location_service.delete_country(country_id)
        if not success:
            raise HTTPException(status_code=404, detail="Country not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to delete country: {str(e)}"
        )


# ==================== REGIONS ====================


@router.post("/regions", response_model=RegionResponse, status_code=201)
async def create_region(
    region_data: RegionCreate,
    location_service: LocationService = Depends(get_location_service),
):
    """Создание нового региона"""
    try:
        region = await location_service.create_region(region_data)
        return region
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to create region: {str(e)}"
        )


@router.get("/regions/{region_id}", response_model=RegionResponse)
async def get_region(
    region_id: int, location_service: LocationService = Depends(get_location_service)
):
    """Получение региона по ID"""
    region = await location_service.get_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.get("/countries/{country_id}/regions", response_model=RegionListResponse)
async def get_regions_by_country(
    country_id: int,
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    location_service: LocationService = Depends(get_location_service),
):
    """Получение регионов по стране"""
    try:
        regions = await location_service.get_regions_by_country(
            country_id=country_id,
            page=page,
            size=size,
            search=search,
            is_active=is_active,
        )
        return regions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get regions: {str(e)}")


# ==================== CITIES ====================


@router.post("/cities", response_model=CityResponse, status_code=201)
async def create_city(
    city_data: CityCreate,
    location_service: LocationService = Depends(get_location_service),
):
    """Создание нового города"""
    try:
        city = await location_service.create_city(city_data)
        return city
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create city: {str(e)}")


@router.get("/cities/{city_id}", response_model=CityResponse)
async def get_city(
    city_id: int, location_service: LocationService = Depends(get_location_service)
):
    """Получение города по ID"""
    city = await location_service.get_city(city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return city


@router.get("/countries/{country_id}/cities", response_model=CityListResponse)
async def get_cities_by_country(
    country_id: int,
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    location_service: LocationService = Depends(get_location_service),
):
    """Получение городов по стране"""
    try:
        cities = await location_service.get_cities_by_country(
            country_id=country_id,
            page=page,
            size=size,
            search=search,
            is_active=is_active,
        )
        return cities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cities: {str(e)}")


@router.get("/regions/{region_id}/cities", response_model=CityListResponse)
async def get_cities_by_region(
    region_id: int,
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    location_service: LocationService = Depends(get_location_service),
):
    """Получение городов по региону"""
    try:
        cities = await location_service.get_cities_by_region(
            region_id=region_id,
            page=page,
            size=size,
            search=search,
            is_active=is_active,
        )
        return cities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cities: {str(e)}")


# ==================== STREETS ====================


@router.post("/streets", response_model=StreetResponse, status_code=201)
async def create_street(
    street_data: StreetCreate,
    location_service: LocationService = Depends(get_location_service),
):
    """Создание новой улицы"""
    try:
        street = await location_service.create_street(street_data)
        return street
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to create street: {str(e)}"
        )


@router.get("/streets/{street_id}", response_model=StreetResponse)
async def get_street(
    street_id: int, location_service: LocationService = Depends(get_location_service)
):
    """Получение улицы по ID"""
    street = await location_service.get_street(street_id)
    if not street:
        raise HTTPException(status_code=404, detail="Street not found")
    return street


@router.get("/cities/{city_id}/streets", response_model=StreetListResponse)
async def get_streets_by_city(
    city_id: int,
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    location_service: LocationService = Depends(get_location_service),
):
    """Получение улиц по городу"""
    try:
        streets = await location_service.get_streets_by_city(
            city_id=city_id, page=page, size=size, search=search, is_active=is_active
        )
        return streets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get streets: {str(e)}")


# ==================== ADDRESSES ====================


@router.post("/addresses", response_model=AddressResponse, status_code=201)
async def create_address(
    address_data: AddressCreate,
    location_service: LocationService = Depends(get_location_service),
):
    """Создание нового адреса"""
    try:
        address = await location_service.create_address(address_data)
        return address
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to create address: {str(e)}"
        )


@router.get("/addresses/{address_id}", response_model=AddressResponse)
async def get_address(
    address_id: int, location_service: LocationService = Depends(get_location_service)
):
    """Получение адреса по ID"""
    address = await location_service.get_address(address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


@router.get("/streets/{street_id}/addresses", response_model=AddressListResponse)
async def get_addresses_by_street(
    street_id: int,
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    location_service: LocationService = Depends(get_location_service),
):
    """Получение адресов по улице"""
    try:
        addresses = await location_service.get_addresses_by_street(
            street_id=street_id,
            page=page,
            size=size,
            search=search,
            is_active=is_active,
        )
        return addresses
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get addresses: {str(e)}"
        )


# ==================== SEARCH ====================


@router.get("/search")
async def search_locations(
    query: str = Query(..., description="Поисковый запрос"),
    country_id: Optional[int] = Query(
        None, description="ID страны для ограничения поиска"
    ),
    region_id: Optional[int] = Query(
        None, description="ID региона для ограничения поиска"
    ),
    city_id: Optional[int] = Query(
        None, description="ID города для ограничения поиска"
    ),
    limit: int = Query(
        10, ge=1, le=50, description="Максимальное количество результатов"
    ),
    location_service: LocationService = Depends(get_location_service),
):
    """
    Поиск локаций по запросу

    Выполняет поиск по странам, регионам, городам, улицам и адресам.
    """
    try:
        results = await location_service.search_locations(
            query=query,
            country_id=country_id,
            region_id=region_id,
            city_id=city_id,
            limit=limit,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

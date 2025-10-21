import logging
from typing import Any, Dict, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backoffice.apps.location.models import (Address, City, Country,
                                                 GeocodingResult, Region,
                                                 Street)
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
from src.backoffice.apps.location.services.geocoder_service import \
    GeocoderService

logger = logging.getLogger(__name__)


class LocationService:
    """Сервис для работы с географическими данными"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.geocoder_service = GeocoderService(db_session)

    # ==================== COUNTRIES ====================

    async def create_country(self, country_data: CountryCreate) -> CountryResponse:
        """Создание страны"""
        country = Country(**country_data.model_dump())
        self.db_session.add(country)
        await self.db_session.commit()
        await self.db_session.refresh(country)
        return CountryResponse.model_validate(country)

    async def get_country(self, country_id: int) -> Optional[CountryResponse]:
        """Получение страны по ID"""
        stmt = select(Country).where(Country.id == country_id)
        result = await self.db_session.execute(stmt)
        country = result.scalar_one_or_none()

        if country:
            return CountryResponse.model_validate(country)
        return None

    async def get_countries(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> CountryListResponse:
        """Получение списка стран с пагинацией и поиском"""
        stmt = select(Country)

        # Фильтры
        conditions = []
        if search:
            conditions.append(
                or_(
                    Country.name.ilike(f"%{search}%"),
                    Country.name_en.ilike(f"%{search}%"),
                    Country.code.ilike(f"%{search}%"),
                )
            )
        if is_active is not None:
            conditions.append(Country.is_active == is_active)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Подсчет общего количества
        count_stmt = select(func.count(Country.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))

        count_result = await self.db_session.execute(count_stmt)
        total = count_result.scalar()

        # Пагинация
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size).order_by(Country.name)

        result = await self.db_session.execute(stmt)
        countries = result.scalars().all()

        pages = (total + size - 1) // size

        return CountryListResponse(
            countries=[CountryResponse.model_validate(c) for c in countries],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def update_country(
        self, country_id: int, country_data: CountryUpdate
    ) -> Optional[CountryResponse]:
        """Обновление страны"""
        stmt = select(Country).where(Country.id == country_id)
        result = await self.db_session.execute(stmt)
        country = result.scalar_one_or_none()

        if not country:
            return None

        update_data = country_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(country, field, value)

        await self.db_session.commit()
        await self.db_session.refresh(country)
        return CountryResponse.model_validate(country)

    async def delete_country(self, country_id: int) -> bool:
        """Удаление страны"""
        stmt = select(Country).where(Country.id == country_id)
        result = await self.db_session.execute(stmt)
        country = result.scalar_one_or_none()

        if not country:
            return False

        await self.db_session.delete(country)
        await self.db_session.commit()
        return True

    # ==================== REGIONS ====================

    async def create_region(self, region_data: RegionCreate) -> RegionResponse:
        """Создание региона"""
        region = Region(**region_data.model_dump())
        self.db_session.add(region)
        await self.db_session.commit()
        await self.db_session.refresh(region)
        return RegionResponse.model_validate(region)

    async def get_region(self, region_id: int) -> Optional[RegionResponse]:
        """Получение региона по ID"""
        stmt = select(Region).where(Region.id == region_id)
        result = await self.db_session.execute(stmt)
        region = result.scalar_one_or_none()

        if region:
            return RegionResponse.model_validate(region)
        return None

    async def get_regions_by_country(
        self,
        country_id: int,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> RegionListResponse:
        """Получение регионов по стране"""
        stmt = select(Region).where(Region.country_id == country_id)

        # Фильтры
        conditions = [Region.country_id == country_id]
        if search:
            conditions.append(
                or_(
                    Region.name.ilike(f"%{search}%"),
                    Region.name_en.ilike(f"%{search}%"),
                )
            )
        if is_active is not None:
            conditions.append(Region.is_active == is_active)

        stmt = stmt.where(and_(*conditions))

        # Подсчет общего количества
        count_stmt = select(func.count(Region.id)).where(and_(*conditions))
        count_result = await self.db_session.execute(count_stmt)
        total = count_result.scalar()

        # Пагинация
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size).order_by(Region.name)

        result = await self.db_session.execute(stmt)
        regions = result.scalars().all()

        pages = (total + size - 1) // size

        return RegionListResponse(
            regions=[RegionResponse.model_validate(r) for r in regions],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    # ==================== CITIES ====================

    async def create_city(self, city_data: CityCreate) -> CityResponse:
        """Создание города"""
        city = City(**city_data.model_dump())
        self.db_session.add(city)
        await self.db_session.commit()
        await self.db_session.refresh(city)
        return CityResponse.model_validate(city)

    async def get_city(self, city_id: int) -> Optional[CityResponse]:
        """Получение города по ID"""
        stmt = select(City).where(City.id == city_id)
        result = await self.db_session.execute(stmt)
        city = result.scalar_one_or_none()

        if city:
            return CityResponse.model_validate(city)
        return None

    async def get_cities_by_country(
        self,
        country_id: int,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> CityListResponse:
        """Получение городов по стране"""
        stmt = select(City).where(City.country_id == country_id)

        # Фильтры
        conditions = [City.country_id == country_id]
        if search:
            conditions.append(
                or_(City.name.ilike(f"%{search}%"), City.name_en.ilike(f"%{search}%"))
            )
        if is_active is not None:
            conditions.append(City.is_active == is_active)

        stmt = stmt.where(and_(*conditions))

        # Подсчет общего количества
        count_stmt = select(func.count(City.id)).where(and_(*conditions))
        count_result = await self.db_session.execute(count_stmt)
        total = count_result.scalar()

        # Пагинация
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size).order_by(City.name)

        result = await self.db_session.execute(stmt)
        cities = result.scalars().all()

        pages = (total + size - 1) // size

        return CityListResponse(
            cities=[CityResponse.model_validate(c) for c in cities],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_cities_by_region(
        self,
        region_id: int,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> CityListResponse:
        """Получение городов по региону"""
        stmt = select(City).where(City.region_id == region_id)

        # Фильтры
        conditions = [City.region_id == region_id]
        if search:
            conditions.append(
                or_(City.name.ilike(f"%{search}%"), City.name_en.ilike(f"%{search}%"))
            )
        if is_active is not None:
            conditions.append(City.is_active == is_active)

        stmt = stmt.where(and_(*conditions))

        # Подсчет общего количества
        count_stmt = select(func.count(City.id)).where(and_(*conditions))
        count_result = await self.db_session.execute(count_stmt)
        total = count_result.scalar()

        # Пагинация
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size).order_by(City.name)

        result = await self.db_session.execute(stmt)
        cities = result.scalars().all()

        pages = (total + size - 1) // size

        return CityListResponse(
            cities=[CityResponse.model_validate(c) for c in cities],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    # ==================== STREETS ====================

    async def create_street(self, street_data: StreetCreate) -> StreetResponse:
        """Создание улицы"""
        street = Street(**street_data.model_dump())
        self.db_session.add(street)
        await self.db_session.commit()
        await self.db_session.refresh(street)
        return StreetResponse.model_validate(street)

    async def get_street(self, street_id: int) -> Optional[StreetResponse]:
        """Получение улицы по ID"""
        stmt = select(Street).where(Street.id == street_id)
        result = await self.db_session.execute(stmt)
        street = result.scalar_one_or_none()

        if street:
            return StreetResponse.model_validate(street)
        return None

    async def get_streets_by_city(
        self,
        city_id: int,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> StreetListResponse:
        """Получение улиц по городу"""
        stmt = select(Street).where(Street.city_id == city_id)

        # Фильтры
        conditions = [Street.city_id == city_id]
        if search:
            conditions.append(
                or_(
                    Street.name.ilike(f"%{search}%"),
                    Street.name_en.ilike(f"%{search}%"),
                )
            )
        if is_active is not None:
            conditions.append(Street.is_active == is_active)

        stmt = stmt.where(and_(*conditions))

        # Подсчет общего количества
        count_stmt = select(func.count(Street.id)).where(and_(*conditions))
        count_result = await self.db_session.execute(count_stmt)
        total = count_result.scalar()

        # Пагинация
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size).order_by(Street.name)

        result = await self.db_session.execute(stmt)
        streets = result.scalars().all()

        pages = (total + size - 1) // size

        return StreetListResponse(
            streets=[StreetResponse.model_validate(s) for s in streets],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    # ==================== ADDRESSES ====================

    async def create_address(self, address_data: AddressCreate) -> AddressResponse:
        """Создание адреса"""
        address = Address(**address_data.model_dump())
        self.db_session.add(address)
        await self.db_session.commit()
        await self.db_session.refresh(address)
        return AddressResponse.model_validate(address)

    async def get_address(self, address_id: int) -> Optional[AddressResponse]:
        """Получение адреса по ID"""
        stmt = select(Address).where(Address.id == address_id)
        result = await self.db_session.execute(stmt)
        address = result.scalar_one_or_none()

        if address:
            return AddressResponse.model_validate(address)
        return None

    async def get_addresses_by_street(
        self,
        street_id: int,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> AddressListResponse:
        """Получение адресов по улице"""
        stmt = select(Address).where(Address.street_id == street_id)

        # Фильтры
        conditions = [Address.street_id == street_id]
        if search:
            conditions.append(
                or_(
                    Address.house_number.ilike(f"%{search}%"),
                    Address.building.ilike(f"%{search}%"),
                    Address.apartment.ilike(f"%{search}%"),
                )
            )
        if is_active is not None:
            conditions.append(Address.is_active == is_active)

        stmt = stmt.where(and_(*conditions))

        # Подсчет общего количества
        count_stmt = select(func.count(Address.id)).where(and_(*conditions))
        count_result = await self.db_session.execute(count_stmt)
        total = count_result.scalar()

        # Пагинация
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size).order_by(Address.house_number)

        result = await self.db_session.execute(stmt)
        addresses = result.scalars().all()

        pages = (total + size - 1) // size

        return AddressListResponse(
            addresses=[AddressResponse.model_validate(a) for a in addresses],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    # ==================== GEOCODING INTEGRATION ====================

    async def create_address_from_geocoding(
        self, geocoding_result_id: int
    ) -> Optional[AddressResponse]:
        """Создание адреса из результата геокодирования"""
        stmt = select(GeocodingResult).where(GeocodingResult.id == geocoding_result_id)
        result = await self.db_session.execute(stmt)
        geocoding_result = result.scalar_one_or_none()

        if not geocoding_result or not geocoding_result.is_successful:
            return None

        # Создаем адрес на основе результата геокодирования
        address_data = AddressCreate(
            house_number=geocoding_result.house_number,
            building=geocoding_result.building,
            apartment=geocoding_result.apartment,
            entrance=geocoding_result.entrance,
            floor=geocoding_result.floor,
            street_id=1,  # TODO: Найти или создать улицу
            latitude=geocoding_result.latitude,
            longitude=geocoding_result.longitude,
            postal_code=geocoding_result.postal_code,
            description=geocoding_result.description,
            is_verified=True,
            is_active=True,
            external_id=geocoding_result.external_id,
            geocoder_provider=geocoding_result.provider,
        )

        address = await self.create_address(address_data)

        # Обновляем связь в результате геокодирования
        geocoding_result.address_id = address.id
        await self.db_session.commit()

        return address

    async def search_locations(
        self,
        query: str,
        country_id: Optional[int] = None,
        region_id: Optional[int] = None,
        city_id: Optional[int] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Поиск локаций по запросу"""
        results = {
            "countries": [],
            "regions": [],
            "cities": [],
            "streets": [],
            "addresses": [],
        }

        # Поиск по странам
        if not country_id:
            stmt = (
                select(Country)
                .where(
                    or_(
                        Country.name.ilike(f"%{query}%"),
                        Country.name_en.ilike(f"%{query}%"),
                    )
                )
                .limit(limit)
            )
            result = await self.db_session.execute(stmt)
            countries = result.scalars().all()
            results["countries"] = [
                CountryResponse.model_validate(c) for c in countries
            ]

        # Поиск по регионам
        if not region_id:
            region_conditions = []
            if country_id:
                region_conditions.append(Region.country_id == country_id)
            region_conditions.append(
                or_(Region.name.ilike(f"%{query}%"), Region.name_en.ilike(f"%{query}%"))
            )

            stmt = select(Region).where(and_(*region_conditions)).limit(limit)
            result = await self.db_session.execute(stmt)
            regions = result.scalars().all()
            results["regions"] = [RegionResponse.model_validate(r) for r in regions]

        # Поиск по городам
        if not city_id:
            city_conditions = []
            if country_id:
                city_conditions.append(City.country_id == country_id)
            if region_id:
                city_conditions.append(City.region_id == region_id)
            city_conditions.append(
                or_(City.name.ilike(f"%{query}%"), City.name_en.ilike(f"%{query}%"))
            )

            stmt = select(City).where(and_(*city_conditions)).limit(limit)
            result = await self.db_session.execute(stmt)
            cities = result.scalars().all()
            results["cities"] = [CityResponse.model_validate(c) for c in cities]

        # Поиск по улицам
        street_conditions = []
        if city_id:
            street_conditions.append(Street.city_id == city_id)
        street_conditions.append(
            or_(Street.name.ilike(f"%{query}%"), Street.name_en.ilike(f"%{query}%"))
        )

        stmt = select(Street).where(and_(*street_conditions)).limit(limit)
        result = await self.db_session.execute(stmt)
        streets = result.scalars().all()
        results["streets"] = [StreetResponse.model_validate(s) for s in streets]

        return results

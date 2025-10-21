from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.backoffice.models import Base, IdMixin


class CompanyEstablishmentType(str, PyEnum):
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    COFFEE_SHOP = "coffee_shop"
    BAR = "bar"
    OTHER = "other"


class CuisineCategory(str, PyEnum):
    JAPANESE = "japanese"
    RUSSIAN = "russian"
    OTHER = "other"


class Company(Base, IdMixin):
    __tablename__ = "companies"
    __repr_fields__ = ("name", "subdomain")

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subdomain: Mapped[str] = mapped_column(
        String(63),
        unique=True,
        index=True,
    )

    type_of_establishment: Mapped[CompanyEstablishmentType] = mapped_column(
        PGEnum(CompanyEstablishmentType, name="company_establishment_type"),
        default=CompanyEstablishmentType.RESTAURANT,
        nullable=False,
    )

    cuisine_category: Mapped[CuisineCategory] = mapped_column(
        PGEnum(CuisineCategory, name="cuisine_category"),
        default=CuisineCategory.OTHER,
        nullable=False,
    )

    

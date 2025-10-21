from enum import Enum as PyEnum

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.backoffice.models import Base, CreatedUpdatedMixin, IdMixin


class CompanyRole(str, PyEnum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class CompanyMember(Base, IdMixin, CreatedUpdatedMixin):
    __tablename__ = "company_members"
    __repr_fields__ = ("company_id", "user_id", "role")

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[CompanyRole] = mapped_column(
        PGEnum(CompanyRole, name="company_role"),
        nullable=False,
        default=CompanyRole.VIEWER,
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "user_id",
            name="uq_company_member_company_user",
        ),
    )

    

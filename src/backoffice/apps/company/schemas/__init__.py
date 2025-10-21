from pydantic import BaseModel

from src.backoffice.apps.company.models import CompanyRole


class CompanyMemberBase(BaseModel):
    role: CompanyRole


class CompanyMemberCreate(CompanyMemberBase):
    user_id: int


class CompanyMemberUpdate(BaseModel):
    role: CompanyRole


class CompanyMemberOut(CompanyMemberBase):
    id: int
    company_id: int
    user_id: int

    class Config:
        from_attributes = True


__all__ = (
    "CompanyMemberBase",
    "CompanyMemberCreate",
    "CompanyMemberUpdate",
    "CompanyMemberOut",
)

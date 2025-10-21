from fastapi import APIRouter, Depends, status

from src.backoffice.apps.company.models import CompanyRole
from src.backoffice.apps.company.schemas import (CompanyMemberCreate,
                                                 CompanyMemberOut,
                                                 CompanyMemberUpdate)
from src.backoffice.apps.company.services import CompanyMembershipService
from src.backoffice.core.dependencies import SessionDep, TokenDep, require_company_role

router = APIRouter(prefix="/members", tags=["company:members"])


async def _require_admin_for_company(
    company_id: int, 
    token: TokenDep, 
    session: SessionDep
):
    return await require_company_role(company_id, CompanyRole.ADMIN, token, session)


@router.get("/{company_id}", response_model=list[CompanyMemberOut])
async def list_members(company_id: int, session: SessionDep):
    service = CompanyMembershipService(session)
    members = await service.list_members(company_id)
    return [CompanyMemberOut.model_validate(m) for m in members]


@router.post(
    "/{company_id}",
    response_model=CompanyMemberOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    company_id: int,
    payload: CompanyMemberCreate,
    session: SessionDep,
    _current_user=Depends(_require_admin_for_company),
):
    service = CompanyMembershipService(session)
    member = await service.add_member(company_id, payload.user_id, payload.role)
    return CompanyMemberOut.model_validate(member)


@router.patch("/{company_id}/{user_id}", response_model=CompanyMemberOut)
async def update_member_role(
    company_id: int,
    user_id: int,
    payload: CompanyMemberUpdate,
    session: SessionDep,
    _current_user=Depends(_require_admin_for_company),
):
    service = CompanyMembershipService(session)
    member = await service.update_role(company_id, user_id, payload.role)
    return CompanyMemberOut.model_validate(member)


@router.delete("/{company_id}/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    company_id: int,
    user_id: int,
    session: SessionDep,
    _current_user=Depends(_require_admin_for_company),
):
    service = CompanyMembershipService(session)
    await service.remove_member(company_id, user_id)
    return None

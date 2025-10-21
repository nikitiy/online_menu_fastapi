from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backoffice.apps.company.models import CompanyMember, CompanyRole


class CompanyMembershipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_members(self, company_id: int) -> Sequence[CompanyMember]:
        stmt = select(CompanyMember).where(CompanyMember.company_id == company_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_member(self, company_id: int, user_id: int) -> CompanyMember | None:
        stmt = select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_member(
        self, company_id: int, user_id: int, role: CompanyRole
    ) -> CompanyMember:
        member = CompanyMember(company_id=company_id, user_id=user_id, role=role)
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def update_role(
        self, company_id: int, user_id: int, role: CompanyRole
    ) -> CompanyMember | None:
        member = await self.get_member(company_id, user_id)
        if not member:
            return None
        member.role = role
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def remove_member(self, company_id: int, user_id: int) -> int:
        stmt = (
            delete(CompanyMember)
            .where(
                CompanyMember.company_id == company_id, CompanyMember.user_id == user_id
            )
            .returning(CompanyMember.id)
        )
        result = await self.session.execute(stmt)
        deleted_ids = result.scalars().all()
        return len(deleted_ids)

    @staticmethod
    def has_required_role(user_role: CompanyRole, required: CompanyRole) -> bool:
        hierarchy = [
            CompanyRole.VIEWER,
            CompanyRole.EDITOR,
            CompanyRole.ADMIN,
            CompanyRole.OWNER,
        ]
        return hierarchy.index(user_role) >= hierarchy.index(required)

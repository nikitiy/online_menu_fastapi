from typing import Annotated, TypeAlias

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from src.backoffice.apps.account.schemas import UserProfile
from src.backoffice.apps.account.services.jwt_service import jwt_service
from src.backoffice.apps.account.services.user_service import UserService
from src.backoffice.apps.company.models import CompanyRole
from src.backoffice.apps.company.services import CompanyMembershipService
from src.backoffice.core.config import db_settings

engine = create_async_engine(db_settings.ASYNC_DATABASE_URL, echo=False, future=True)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Типизированные зависимости для переиспользования
SessionDep: TypeAlias = Annotated[AsyncSession, Depends(get_session)]

# Создаем экземпляр HTTPBearer для переиспользования
security = HTTPBearer()

# Типизированная зависимость для токена авторизации
TokenDep: TypeAlias = Annotated[HTTPAuthorizationCredentials, Depends(security)]


async def get_current_user(
    token: TokenDep,
    session: AsyncSession,
) -> UserProfile:
    """Извлечь и проверить текущего пользователя из bearer-токена.
    Локальная реализация для избежания циклического импорта с роутером аутентификации.
    """
    payload = jwt_service.verify_access_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user_service = UserService(session)
    user = await user_service.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return UserProfile.model_validate(user)


async def require_company_role(
    company_id: int,
    required_role: CompanyRole,
    token: TokenDep,
    session: SessionDep,
) -> UserProfile:
    """Ensure current user has at least required_role in the company.
    Returns current user profile on success.
    """
    current_user = await get_current_user(token, session)
    membership_service = CompanyMembershipService(session)
    member = await membership_service.get_member(company_id, current_user.id)
    if not member or not CompanyMembershipService.has_required_role(
        member.role, required_role
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    return current_user

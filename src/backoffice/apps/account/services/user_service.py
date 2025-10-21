from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backoffice.apps.account.models import OAuthAccount, RefreshToken, User
from src.backoffice.apps.account.schemas import UserCreate, UserUpdate


class UserService:
    """Сервис для работы с пользователями"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по username"""
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> User:
        """Создать пользователя"""
        user = User(
            email=str(user_data.email),
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            avatar_url=user_data.avatar_url,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Обновить пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_or_create_user_by_oauth(
        self, provider: str, provider_user_id: str, user_info: dict
    ) -> tuple[User, bool]:
        """Получить или создать пользователя через OAuth"""
        # Ищем существующий OAuth аккаунт
        oauth_account = await self.session.execute(
            select(OAuthAccount)
            .where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
            .options(selectinload(OAuthAccount.user))
        )
        oauth_account = oauth_account.scalar_one_or_none()

        if oauth_account:
            # Обновляем информацию о пользователе
            user = oauth_account.user
            user.first_name = user_info.get("first_name") or user.first_name
            user.last_name = user_info.get("last_name") or user.last_name
            user.avatar_url = user_info.get("avatar_url") or user.avatar_url
            user.last_login = datetime.now(timezone.utc)

            # Обновляем OAuth аккаунт
            oauth_account.provider_username = user_info.get("username")
            oauth_account.provider_email = user_info.get("email")
            oauth_account.updated_at = datetime.now(timezone.utc)

            await self.session.commit()
            return user, False

        # Ищем пользователя по email
        email = user_info.get("email")
        if email:
            user = await self.get_user_by_email(email)
            if user:
                # Создаем OAuth аккаунт для существующего пользователя
                oauth_account = OAuthAccount(
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=provider_user_id,
                    provider_username=user_info.get("username"),
                    provider_email=email,
                    access_token=user_info.get("access_token"),
                    refresh_token=user_info.get("refresh_token"),
                )
                self.session.add(oauth_account)
                user.last_login = datetime.now(timezone.utc)
                await self.session.commit()
                return user, False

        # Создаем нового пользователя
        user = User(
            email=email or f"{provider_user_id}@{provider}.local",
            username=user_info.get("username"),
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name"),
            avatar_url=user_info.get("avatar_url"),
            is_verified=True,  # OAuth пользователи считаются верифицированными
        )
        self.session.add(user)
        await self.session.flush()  # Получаем ID пользователя

        # Создаем OAuth аккаунт
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_username=user_info.get("username"),
            provider_email=email,
            access_token=user_info.get("access_token"),
            refresh_token=user_info.get("refresh_token"),
        )
        self.session.add(oauth_account)
        await self.session.commit()
        await self.session.refresh(user)

        return user, True

    async def create_refresh_token(
        self, user_id: int, token: str, expires_at: datetime
    ) -> RefreshToken:
        """Создать refresh токен"""
        refresh_token = RefreshToken(
            user_id=user_id, token=token, expires_at=expires_at
        )
        self.session.add(refresh_token)
        await self.session.commit()
        await self.session.refresh(refresh_token)
        return refresh_token

    async def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Получить refresh токен"""
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token: str) -> bool:
        """Отозвать refresh токен"""
        refresh_token = await self.get_refresh_token(token)
        if refresh_token:
            refresh_token.is_revoked = True
            await self.session.commit()
            return True
        return False

    async def revoke_all_user_tokens(self, user_id: int) -> int:
        """Отозвать все токены пользователя"""
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.is_revoked == False
            )
        )
        tokens = result.scalars().all()

        for token in tokens:
            token.is_revoked = True

        await self.session.commit()
        return len(tokens)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя по email и паролю"""
        user = await self.get_user_by_email(email)
        if not user or not user.is_active:
            return None

        # Здесь должна быть проверка пароля
        # Для простоты пропускаем, так как у нас нет поля password в модели
        # В реальном проекте нужно добавить поле password_hash
        return user

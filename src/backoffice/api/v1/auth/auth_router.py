from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from src.backoffice.apps.account.schemas import (OAuthProvider, OAuthProviders,
                                                 RefreshTokenRequest, Token,
                                                 UserLogin, UserProfile)
from src.backoffice.apps.account.services.jwt_service import jwt_service
from src.backoffice.apps.account.services.oauth_service import (
    google_oauth_service, vk_oauth_service, yandex_oauth_service)
from src.backoffice.apps.account.services.user_service import UserService
from src.backoffice.core.config import auth_settings
from src.backoffice.core.dependencies import SessionDep, TokenDep

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_user(token: TokenDep, session: SessionDep) -> UserProfile:
    """Получить текущего пользователя из токена"""
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


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: UserProfile = Depends(get_current_user),
):
    """Получить профиль текущего пользователя"""
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest, session: SessionDep):
    """Обновить access токен"""
    user_service = UserService(session)

    # Проверяем refresh токен
    payload = jwt_service.verify_refresh_token(refresh_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Проверяем токен в базе данных
    refresh_token_obj = await user_service.get_refresh_token(refresh_data.refresh_token)
    if not refresh_token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Получаем пользователя
    user = await user_service.get_user_by_id(refresh_token_obj.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Создаем новые токены
    token_data = {"user_id": user.id, "email": user.email}
    access_token = jwt_service.create_access_token(token_data)
    new_refresh_token = jwt_service.create_refresh_token(token_data)

    # Отзываем старый refresh токен
    await user_service.revoke_refresh_token(refresh_data.refresh_token)

    # Создаем новый refresh токен в базе
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=auth_settings.refresh_token_expire_days
    )
    await user_service.create_refresh_token(user.id, new_refresh_token, expires_at)

    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout")
async def logout(refresh_data: RefreshTokenRequest, session: SessionDep):
    """Выйти из системы"""
    user_service = UserService(session)
    await user_service.revoke_refresh_token(refresh_data.refresh_token)
    return {"message": "Successfully logged out"}


@router.get("/providers", response_model=OAuthProviders)
async def get_oauth_providers():
    """Получить список доступных OAuth провайдеров"""
    providers = []

    # Google
    if auth_settings.google_client_id:
        providers.append(
            OAuthProvider(
                name="google",
                display_name="Google",
                auth_url=f"{auth_settings.backend_url}/api/v1/auth/google",
                enabled=True,
            )
        )

    # Yandex
    if auth_settings.yandex_client_id:
        providers.append(
            OAuthProvider(
                name="yandex",
                display_name="Yandex",
                auth_url=f"{auth_settings.backend_url}/api/v1/auth/yandex",
                enabled=True,
            )
        )

    # VK
    if auth_settings.vk_client_id:
        providers.append(
            OAuthProvider(
                name="vk",
                display_name="VKontakte",
                auth_url=f"{auth_settings.backend_url}/api/v1/auth/vk",
                enabled=True,
            )
        )

    return OAuthProviders(providers=providers)


@router.get("/google")
async def google_auth():
    """Начать авторизацию через Google"""
    auth_url = google_oauth_service.get_authorization_url()
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_callback(code: str, session: SessionDep):
    """Callback для Google OAuth"""
    # TODO: Implement state validation for CSRF protection
    # For now, we accept any state or no state
    # In production, you should validate the state parameter

    # Получаем access токен
    token_data = await google_oauth_service.get_access_token(code)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get access token from Google",
        )

    # Получаем информацию о пользователе
    user_info = await google_oauth_service.get_user_info(token_data["access_token"])
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from Google",
        )

    # Создаем или получаем пользователя
    user_service = UserService(session)
    user, is_new = await user_service.get_or_create_user_by_oauth(
        provider="google",
        provider_user_id=user_info["id"],
        user_info={
            **user_info,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
        },
    )

    # Создаем JWT токены
    token_data_jwt = {"user_id": user.id, "email": user.email}
    access_token = jwt_service.create_access_token(token_data_jwt)
    refresh_token = jwt_service.create_refresh_token(token_data_jwt)

    # Сохраняем refresh токен в базе
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=auth_settings.refresh_token_expire_days
    )
    await user_service.create_refresh_token(user.id, refresh_token, expires_at)

    # Перенаправляем на фронтенд с токенами
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserLogin.model_validate(user),
        "is_new_user": is_new,
    }


@router.get("/yandex")
async def yandex_auth():
    """Начать авторизацию через Yandex"""
    auth_url = yandex_oauth_service.get_authorization_url()
    return {"auth_url": auth_url}


@router.get("/yandex/callback")
async def yandex_callback(code: str, session: SessionDep):
    """Callback для Yandex OAuth"""
    # TODO: Implement state validation for CSRF protection
    # For now, we accept any state or no state
    # In production, you should validate the state parameter

    # Получаем access токен
    token_data = await yandex_oauth_service.get_access_token(code)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get access token from Yandex",
        )

    # Получаем информацию о пользователе
    user_info = await yandex_oauth_service.get_user_info(token_data["access_token"])
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from Yandex",
        )

    # Создаем или получаем пользователя
    user_service = UserService(session)
    user, is_new = await user_service.get_or_create_user_by_oauth(
        provider="yandex",
        provider_user_id=user_info["id"],
        user_info={
            **user_info,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
        },
    )

    # Создаем JWT токены
    token_data_jwt = {"user_id": user.id, "email": user.email}
    access_token = jwt_service.create_access_token(token_data_jwt)
    refresh_token = jwt_service.create_refresh_token(token_data_jwt)

    # Сохраняем refresh токен в базе
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=auth_settings.refresh_token_expire_days
    )
    await user_service.create_refresh_token(user.id, refresh_token, expires_at)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserLogin.model_validate(user),
        "is_new_user": is_new,
    }


@router.get("/vk")
async def vk_auth():
    """Начать авторизацию через VK"""
    auth_url = vk_oauth_service.get_authorization_url()
    return {"auth_url": auth_url}


@router.get("/vk/callback")
async def vk_callback(code: str, session: SessionDep):
    """Callback для VK OAuth"""
    # TODO: Implement state validation for CSRF protection
    # For now, we accept any state or no state
    # In production, you should validate the state parameter

    # Получаем access токен
    token_data = await vk_oauth_service.get_access_token(code)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get access token from VK",
        )

    # Получаем информацию о пользователе
    user_info = await vk_oauth_service.get_user_info(token_data["access_token"])
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from VK",
        )

    # Создаем или получаем пользователя
    user_service = UserService(session)
    user, is_new = await user_service.get_or_create_user_by_oauth(
        provider="vk",
        provider_user_id=user_info["id"],
        user_info={
            **user_info,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
        },
    )

    # Создаем JWT токены
    token_data_jwt = {"user_id": user.id, "email": user.email}
    access_token = jwt_service.create_access_token(token_data_jwt)
    refresh_token = jwt_service.create_refresh_token(token_data_jwt)

    # Сохраняем refresh токен в базе
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=auth_settings.refresh_token_expire_days
    )
    await user_service.create_refresh_token(user.id, refresh_token, expires_at)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserLogin.model_validate(user),
        "is_new_user": is_new,
    }

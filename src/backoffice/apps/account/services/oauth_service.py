from typing import Dict, Optional

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client

from src.backoffice.core.config import auth_settings


class OAuthService:
    """Базовый сервис для OAuth авторизации"""

    def __init__(self):
        self.auth_settings = auth_settings

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Получить информацию о пользователе (должен быть переопределен в наследниках)"""
        raise NotImplementedError


class GoogleOAuthService(OAuthService):
    """Сервис для Google OAuth"""

    def __init__(self):
        super().__init__()
        self.client_id = self.auth_settings.google_client_id
        self.client_secret = self.auth_settings.google_client_secret
        self.redirect_uri = self.auth_settings.google_redirect_uri
        self.scope = "openid email profile"
        self.authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Получить URL для авторизации"""
        if not self.client_id or not self.client_secret:
            raise ValueError("Google OAuth credentials not configured")

        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
        )

        authorization_url, _ = client.create_authorization_url(
            self.authorize_url, state=state
        )
        return authorization_url

    async def get_access_token(self, code: str) -> Optional[Dict]:
        """Получить access токен"""
        async with AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
        ) as client:
            try:
                token = await client.fetch_token(
                    self.token_url, 
                    code=code,
                    grant_type="authorization_code"
                )
                return token
            except Exception:
                return None

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Получить информацию о пользователе"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.user_info_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                return response.json()
            except Exception:
                return None


class YandexOAuthService(OAuthService):
    """Сервис для Yandex OAuth"""

    def __init__(self):
        super().__init__()
        self.client_id = self.auth_settings.yandex_client_id
        self.client_secret = self.auth_settings.yandex_client_secret
        self.redirect_uri = self.auth_settings.yandex_redirect_uri
        self.scope = "login:email login:info"
        self.authorize_url = "https://oauth.yandex.ru/authorize"
        self.token_url = "https://oauth.yandex.ru/token"
        self.user_info_url = "https://login.yandex.ru/info"

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Получить URL для авторизации"""
        if not self.client_id or not self.client_secret:
            raise ValueError("Yandex OAuth credentials not configured")

        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
        )

        authorization_url, _ = client.create_authorization_url(
            self.authorize_url, state=state
        )
        return authorization_url

    async def get_access_token(self, code: str) -> Optional[Dict]:
        """Получить access токен"""
        async with AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
        ) as client:
            try:
                token = await client.fetch_token(
                    self.token_url, 
                    code=code,
                    grant_type="authorization_code"
                )
                return token
            except Exception:
                return None

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Получить информацию о пользователе"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.user_info_url,
                    headers={"Authorization": f"OAuth {access_token}"},
                )
                response.raise_for_status()
                return response.json()
            except Exception:
                return None


class VKOAuthService(OAuthService):
    """Сервис для VK OAuth"""

    def __init__(self):
        super().__init__()
        self.client_id = self.auth_settings.vk_client_id
        self.client_secret = self.auth_settings.vk_client_secret
        self.redirect_uri = self.auth_settings.vk_redirect_uri
        self.scope = "email"
        self.authorize_url = "https://oauth.vk.com/authorize"
        self.token_url = "https://oauth.vk.com/access_token"
        self.user_info_url = "https://api.vk.com/method/users.get"

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Получить URL для авторизации"""
        if not self.client_id or not self.client_secret:
            raise ValueError("VK OAuth credentials not configured")

        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
        )

        authorization_url, _ = client.create_authorization_url(
            self.authorize_url, state=state
        )
        return authorization_url

    async def get_access_token(self, code: str) -> Optional[Dict]:
        """Получить access токен"""
        async with AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
        ) as client:
            try:
                token = await client.fetch_token(
                    self.token_url, 
                    code=code,
                    grant_type="authorization_code"
                )
                return token
            except Exception:
                return None

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Получить информацию о пользователе"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.user_info_url,
                    params={
                        "access_token": access_token,
                        "fields": "id,first_name,last_name,email,photo_200",
                        "v": "5.131",
                    },
                )
                response.raise_for_status()
                data = response.json()
                if "response" in data and data["response"]:
                    user_data = data["response"][0]
                    return {
                        "id": str(user_data.get("id")),
                        "first_name": user_data.get("first_name"),
                        "last_name": user_data.get("last_name"),
                        "email": data.get("email"),  # Email приходит отдельно
                        "avatar_url": user_data.get("photo_200"),
                    }
                return None
            except Exception:
                return None


# Создаем экземпляры сервисов
google_oauth_service = GoogleOAuthService()
yandex_oauth_service = YandexOAuthService()
vk_oauth_service = VKOAuthService()

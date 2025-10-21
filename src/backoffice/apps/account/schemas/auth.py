from typing import Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Схема токена"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Схема данных токена"""

    user_id: Optional[int] = None
    email: Optional[str] = None


class LoginRequest(BaseModel):
    """Схема запроса входа"""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Схема запроса обновления токена"""

    refresh_token: str


class OAuthCallback(BaseModel):
    """Схема OAuth callback"""

    code: str
    state: Optional[str] = None


class OAuthProvider(BaseModel):
    """Схема OAuth провайдера"""

    name: str
    display_name: str
    auth_url: str
    enabled: bool


class OAuthProviders(BaseModel):
    """Схема доступных OAuth провайдеров"""

    providers: list[OAuthProvider]


class UserLogin(BaseModel):
    """Схема входа пользователя"""

    user_id: int
    email: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_superuser: bool

import logging
import time
import uuid
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

from src.backoffice.apps.account.services.jwt_service import jwt_service
from src.backoffice.core.config import logging_settings
from src.backoffice.core.context import request_id_ctx_var, user_id_ctx_var
from src.backoffice.core.logging import get_logger


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware для проверки авторизации"""

    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/",
            "/api/v1/location/geocoding/",
            "/api/v1/location/locations/",
            "/api/v1/health/",
        ]
        self.security = HTTPBearer(auto_error=False)

    async def dispatch(self, request: Request, call_next):
        # Проверяем, нужно ли проверять авторизацию для этого пути
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # Проверяем наличие токена
        authorization: Optional[HTTPAuthorizationCredentials] = await self.security(
            request
        )

        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Проверяем токен
        payload = jwt_service.verify_access_token(authorization.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Добавляем информацию о пользователе в request state
        request.state.user_id = payload.get("user_id")
        request.state.user_email = payload.get("email")

        return await call_next(request)

    def _is_excluded_path(self, path: str) -> bool:
        """Проверить, исключен ли путь из проверки авторизации"""
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return True
        return False


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Присваивает request_id, захватывает user_id из state, логирует запрос/ответ."""

    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("http")

    async def dispatch(self, request: Request, call_next):
        started_at = time.time()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_ctx_var.set(request_id)
        user_token = user_id_ctx_var.set("-")

        # Read request body carefully for logging, without consuming stream for downstream
        body_bytes: bytes = b""
        if logging_settings.log_requests:
            body_bytes = await request.body()
            if len(body_bytes) > logging_settings.body_limit:
                body_preview = body_bytes[: logging_settings.body_limit] + b"..."
            else:
                body_preview = body_bytes

            async def receive() -> Message:
                return {"type": "http.request", "body": body_bytes, "more_body": False}

            request._receive = receive  # type: ignore[attr-defined]

        self.logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "user_id": getattr(getattr(request.state, "user_id", None), "", None)
                or "-",
            },
        )

        try:
            response = await call_next(request)
        finally:
            # restore context vars
            request_id_ctx_var.reset(token)
            user_id_ctx_var.reset(user_token)

        process_time_ms = int((time.time() - started_at) * 1000)

        # capture user_id if set by AuthMiddleware
        user_id = getattr(request.state, "user_id", "-")

        # Log response
        extra = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "user_id": user_id or "-",
            "status_code": getattr(response, "status_code", 0),
            "process_time_ms": process_time_ms,
        }

        if logging_settings.log_requests and hasattr(response, "body_iterator"):
            # Best-effort: avoid consuming the stream; only log known content-length
            content_length = response.headers.get("content-length")
            if content_length is not None:
                extra["response_length"] = int(content_length)

        level = logging.INFO if extra["status_code"] < 500 else logging.ERROR
        self.logger.log(level, "response", extra=extra)

        return response

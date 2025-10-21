from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backoffice.api.v1 import api_router
from src.backoffice.core.config import (auth_settings, cors_settings,
                                        logging_settings)
from src.backoffice.core.exceptions import register_exception_handlers
from src.backoffice.core.logging import configure_logging
from src.backoffice.core.middleware import (AuthMiddleware,
                                            RequestContextMiddleware)


def create_app() -> FastAPI:
    """Application factory to assemble the FastAPI app with middlewares and routers."""
    configure_logging(level=logging_settings.level, fmt=logging_settings.format)

    app = FastAPI(
        title="Backoffice API",
        description="API для управления backoffice с поддержкой авторизации и геокодирования",
        version="0.1.0",
    )

    # Request context and auth middleware
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(AuthMiddleware, excluded_paths=auth_settings.auth_excluded_paths)

    # Optional CORS
    if cors_settings.enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_settings.allow_origins,
            allow_credentials=cors_settings.allow_credentials,
            allow_methods=cors_settings.allow_methods,
            allow_headers=cors_settings.allow_headers,
        )

    # Routers
    app.include_router(api_router, prefix="/api/v1")

    # Exceptions
    register_exception_handlers(app)

    return app


__all__ = ("create_app",)

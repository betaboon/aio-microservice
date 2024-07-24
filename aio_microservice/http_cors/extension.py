from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.config.cors import CORSConfig
from pydantic import BaseModel, Field

from aio_microservice.core.abc import ExtensionABC, litestar_on_app_init

if TYPE_CHECKING:
    from litestar.config.app import AppConfig


class HttpCorsSettings(BaseModel):
    allow_origins: str = Field(
        default="*",
        description="Comma separated list of allowed origins.",
    )
    allow_methods: str = Field(
        default="*",
        description="Comma separated list of allowed methods.",
    )
    allow_headers: str = Field(
        default="*",
        description="Comma separated list of allowed headers.",
    )
    allow_credentials: bool = Field(
        default=False,
        description="Whether or not to set 'Access-Control-Allow-Credentials'.",
    )
    allow_origin_regex: str | None = Field(
        default=None,
        description="Regex of allowed origins.",
    )
    expose_headers: str = Field(
        default="",
        description="Comma separated list of headers set in the 'Access-Control-Expose-Headers'.",
    )
    max_age: int = Field(
        default=600,
        description="Response cache TTL in seconds.",
    )


class HttpCorsExtensionSettings(BaseModel):
    http_cors: HttpCorsSettings = HttpCorsSettings()


class HttpCorsExtension(ExtensionABC):
    def __init__(self, settings: HttpCorsExtensionSettings) -> None:
        self._litestar_cors_config = CORSConfig(
            allow_origins=settings.http_cors.allow_origins.split(","),
            allow_methods=settings.http_cors.allow_methods.split(","),  # type: ignore[arg-type]
            allow_headers=settings.http_cors.allow_headers.split(","),
            allow_credentials=settings.http_cors.allow_credentials,
            allow_origin_regex=settings.http_cors.allow_origin_regex,
            expose_headers=settings.http_cors.expose_headers.split(","),
            max_age=settings.http_cors.max_age,
        )

    @litestar_on_app_init
    def http_cors_litestar_on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config.cors_config = self._litestar_cors_config
        return app_config

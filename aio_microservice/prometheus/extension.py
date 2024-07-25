from __future__ import annotations

from typing import TYPE_CHECKING

from humps import kebabize
from litestar.contrib.prometheus import PrometheusConfig, PrometheusController
from pydantic import BaseModel, Field

from aio_microservice import litestar_on_app_init
from aio_microservice.core.abc import ExtensionABC

if TYPE_CHECKING:
    from litestar.config.app import AppConfig


class PrometheusSettings(BaseModel):
    prefix: str = Field(
        default="http",
        description="The prefix to use for the HTTP metrics.",
    )
    # Note: cannot support callables because of typed-settings
    labels: dict[str, str] | None = Field(
        default=None,
        description="A mapping of labels to add to the HTTP metrics.",
    )
    exclude: list[str] | None = Field(
        default=[
            "^/readiness$",
            "^/liveness$",
            "^/metrics$",
        ],
        description="A list of patterns for routes to exclude from the HTTP metrics.",
    )


class PrometheusExtensionSettings(BaseModel):
    prometheus: PrometheusSettings = PrometheusSettings()


class PrometheusExtension(ExtensionABC):
    def __init__(self, settings: PrometheusExtensionSettings) -> None:
        self._prometheus_config = PrometheusConfig(
            app_name=kebabize(self.__class__.__name__),
            prefix=settings.prometheus.prefix,
            labels=settings.prometheus.labels,
            exclude=settings.prometheus.exclude,
        )

    @litestar_on_app_init
    def prometheus_on_litestar_init(self, app_config: AppConfig) -> AppConfig:
        app_config.route_handlers.append(PrometheusController)
        app_config.middleware.append(self._prometheus_config.middleware)
        return app_config

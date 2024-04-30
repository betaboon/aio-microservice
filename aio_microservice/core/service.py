from __future__ import annotations

import asyncio
import logging
import typing
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from functools import partial
from textwrap import dedent
from typing import Any, Callable, ClassVar, Generic, TypeVar

import litestar.config.cors
import rich
import rich_click as click
import typed_settings
import uvicorn
from humps import kebabize
from loguru import logger
from pydantic import BaseModel, Field

from aio_microservice.core.abc import ServiceABC, startup_message
from aio_microservice.core.logging import setup_logging
from aio_microservice.core.openapi import OpenAPIController
from aio_microservice.types import Port  # noqa: TCH001

if typing.TYPE_CHECKING:
    from collections.abc import AsyncGenerator


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


class HttpSettings(BaseModel):
    host: str = Field(
        default="localhost",
        description="The ip to bind to.",
    )
    port: Port = Field(
        default=8080,
        description="The port to bind to.",
    )
    timeout_keep_alive: int = Field(
        default=5,
        description="Close Keep-Alive connections if no new data is received within this timeout.",
    )
    cors: HttpCorsSettings = HttpCorsSettings()


class ServiceSettings(BaseModel):
    debug: bool = Field(
        default=False,
        description="Whether to enable debug logging.",
    )
    http: HttpSettings = HttpSettings()


ServiceSettingsT = TypeVar("ServiceSettingsT", bound=ServiceSettings)


class Service(Generic[ServiceSettingsT], ServiceABC):
    _settings_cls: ClassVar[type[ServiceSettings]]

    def __init_subclass__(cls) -> None:
        # determine settings-class based on generic
        cls._settings_cls = typing.get_args(cls.__orig_bases__[0])[0]  # type: ignore

    def __init__(self, settings: ServiceSettingsT | None = None) -> None:
        if settings is None:
            settings = typing.cast(ServiceSettingsT, self._settings_cls())
        ServiceABC.__init__(self, settings=settings)

        self.settings = settings

        self._litestar_app = self._create_litestar_app()
        self._uvicorn_server = self._create_uvicorn_server(self._litestar_app)

    @property
    def litestar_app(self) -> litestar.Litestar:
        return self._litestar_app

    def _get_litestar_on_startup(self) -> list[litestar.types.LifespanHook]:
        fns: list[litestar.types.LifespanHook] = [partial(fn, self) for fn in self._startup_hooks]
        fns.append(self._emit_startup_message)
        return fns

    def _get_litestar_on_shutdown(self) -> list[litestar.types.LifespanHook]:
        return [partial(fn, self) for fn in self._shutdown_hooks]

    def _get_litestar_lifespan(
        self,
    ) -> list[[Callable[litestar.Litestar], AbstractAsyncContextManager[Any]]]:  # type: ignore
        # NOTE this is ugly, but works
        @asynccontextmanager
        async def wrapper(fn: Any, app: litestar.Litestar) -> AsyncGenerator[None, None]:  # noqa: ANN401
            fn_ctx = asynccontextmanager(fn)
            async with fn_ctx(self):
                yield

        return [partial(wrapper, hook.fn) for hook in self._lifespan_hooks]

    def _get_litestar_route_handlers(
        self,
    ) -> list[litestar.types.ControllerRouterHandler]:
        litestar_route_handlers = self._litestar_http_controllers
        for route_handler in self._litestar_http_route_handlers:
            # replace fn with a partial to emulate Controller behavior
            route_handler._fn = partial(route_handler.fn, self)
            litestar_route_handlers.append(route_handler)

        def create_probe_response(value: bool) -> litestar.Response[bool]:
            status_code = (
                litestar.status_codes.HTTP_200_OK
                if value
                else litestar.status_codes.HTTP_503_SERVICE_UNAVAILABLE
            )
            return litestar.Response(content=value, status_code=status_code)

        @litestar.get(path="/readiness", include_in_schema=False)
        async def _get_readiness() -> litestar.Response[bool]:
            readiness = await self._get_readiness()
            return create_probe_response(readiness)

        @litestar.get(path="/liveness", include_in_schema=False)
        async def _get_liveness() -> litestar.Response[bool]:
            readiness = await self._get_liveness()
            return create_probe_response(readiness)

        litestar_route_handlers.append(_get_readiness)
        litestar_route_handlers.append(_get_liveness)
        return litestar_route_handlers

    def _create_litestar_app(self) -> litestar.Litestar:
        openapi_config = litestar.openapi.OpenAPIConfig(
            title=self.__class__.__name__,
            version=self.__version__,
            description=self.__description__,
            enabled_endpoints={"openapi.json", "openapi.yaml", "openapi.yml"},
            openapi_controller=OpenAPIController,
        )
        cors_config = litestar.config.cors.CORSConfig(
            allow_origins=self.settings.http.cors.allow_origins.split(","),
            allow_methods=self.settings.http.cors.allow_methods.split(","),  # type: ignore[arg-type]
            allow_headers=self.settings.http.cors.allow_headers.split(","),
            allow_credentials=self.settings.http.cors.allow_credentials,
            allow_origin_regex=self.settings.http.cors.allow_origin_regex,
            expose_headers=self.settings.http.cors.expose_headers.split(","),
            max_age=self.settings.http.cors.max_age,
        )
        return litestar.Litestar(
            on_startup=self._get_litestar_on_startup(),
            on_shutdown=self._get_litestar_on_shutdown(),
            lifespan=self._get_litestar_lifespan(),
            route_handlers=self._get_litestar_route_handlers(),
            listeners=self._litestar_listeners,
            openapi_config=openapi_config,
            cors_config=cors_config,
        )

    def _create_uvicorn_server(self, litestar_app: litestar.Litestar) -> uvicorn.Server:
        config = uvicorn.Config(
            app=litestar_app,
            host=self.settings.http.host,
            port=self.settings.http.port,
            timeout_keep_alive=self.settings.http.timeout_keep_alive,
            log_config=None,
            log_level=logging.DEBUG if self.settings.debug else logging.INFO,
        )
        return uvicorn.Server(
            config=config,
        )

    async def _get_readiness(self) -> bool:
        fns = [fn(self) for fn in self._readiness_probes]
        results = await asyncio.gather(*fns)
        return all(results)

    async def _get_liveness(self) -> bool:
        fns = [fn(self) for fn in self._liveness_probes]
        results = await asyncio.gather(*fns)
        return all(results)

    async def _emit_startup_message(self) -> None:
        messages = [await fn(service=self) for fn in self._startup_messages]
        if not messages:
            return  # pragma: no cover
        startup_message = ""
        for index, message in enumerate(messages):
            _message = dedent(message).lstrip().rstrip()
            startup_message += _message.format(
                scheme="https" if self._uvicorn_server.config.is_ssl else "http",
                host=self._uvicorn_server.config.host,
                port=self._uvicorn_server.config.port,
            )
            if index < len(messages) - 1:
                startup_message += "\n\n"

        console = rich.console.Console()
        markdown = rich.markdown.Markdown(startup_message)
        console.print(markdown)

    @startup_message
    async def _startup_message(self) -> str:
        return """
            # Http

            The following http-endpoints are available:
            - {scheme}://{host}:{port}/schema/openapi
            - {scheme}://{host}:{port}/schema/openapi.json
            - {scheme}://{host}:{port}/schema/openapi.yaml
        """

    async def run(self) -> None:
        logger.info(f"Starting Service: {self.__class__.__name__}")
        logger.info(f"Using Settings: {self.settings}")
        await self._uvicorn_server.serve()

    @classmethod
    def cli(cls) -> None:
        @click.group(help=cls.__description__)
        def _cli() -> None:
            pass

        @_cli.command(
            name="version",
            short_help="Print version of the service.",
        )
        def _version() -> None:
            print(cls.__version__)  # noqa: T201

        @_cli.command(
            name="run",
            short_help="Run the service.",
            help=cls.__description__,
        )
        @typed_settings.click_options(
            settings_cls=cls._settings_cls,
            loaders=kebabize(cls.__name__),
            show_envvars_in_help=True,
        )
        def _run(settings: ServiceSettingsT) -> None:
            loglevel = logging.DEBUG if settings.debug else logging.INFO
            setup_logging(level=loglevel)
            service = cls(settings=settings)
            asyncio.run(service.run())

        _cli()

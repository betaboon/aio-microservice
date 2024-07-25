from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, ClassVar, TypeVar

import litestar

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable

    from pydantic import BaseModel


class CommonABC(ABC):
    __version__: ClassVar[str] = "1.0.0"
    __description__: ClassVar[str] = ""

    def __init__(self) -> None:
        self._startup_hooks: list[startup_hook] = []
        self._shutdown_hooks: list[shutdown_hook] = []
        self._lifespan_hooks: list[lifespan_hook] = []
        self._readiness_probes: list[readiness_probe] = []
        self._liveness_probes: list[liveness_probe] = []
        self._startup_messages: list[startup_message] = []
        self._litestar_on_app_init: list[litestar_on_app_init] = []
        self._litestar_http_route_handlers: list[litestar.handlers.HTTPRouteHandler] = []
        self._litestar_http_controllers: list[litestar.types.ControllerRouterHandler] = []
        self._litestar_listeners: list[litestar.events.EventListener] = []

        self._collect_decorated_functions()

    def _collect_decorated_functions(self) -> None:  # noqa: C901
        for _, attribute in inspect.getmembers(self.__class__):
            if isinstance(attribute, startup_hook):
                self._startup_hooks.append(attribute)
            elif isinstance(attribute, shutdown_hook):
                self._shutdown_hooks.append(attribute)
            elif isinstance(attribute, lifespan_hook):
                self._lifespan_hooks.append(attribute)
            elif isinstance(attribute, readiness_probe):
                self._readiness_probes.append(attribute)
            elif isinstance(attribute, liveness_probe):
                self._liveness_probes.append(attribute)
            elif isinstance(attribute, startup_message):
                self._startup_messages.append(attribute)
            elif isinstance(attribute, litestar_on_app_init):
                self._litestar_on_app_init.append(attribute)
            elif isinstance(attribute, litestar.handlers.HTTPRouteHandler):
                self._litestar_http_route_handlers.append(attribute)
            elif isinstance(attribute, litestar.events.EventListener):
                self._litestar_listeners.append(attribute)


class ServiceABC(CommonABC):
    def __init__(self, settings: BaseModel) -> None:
        CommonABC.__init__(self)
        self._init_extensions(settings)

    def _init_extensions(self, settings: BaseModel) -> None:
        for extension_cls in ExtensionABC._extension_classes:
            if not isinstance(self, extension_cls):
                continue
            # pass settings if the extension-constructor expects them
            init_kwargs = {}
            init_signature = inspect.signature(extension_cls.__init__)
            if "settings" in init_signature.parameters:
                init_kwargs["settings"] = settings
            extension_cls.__init__(self, **init_kwargs)

    @abstractmethod
    async def run(self) -> None: ...  # pragma: no cover


class ExtensionABC(CommonABC):
    _extension_classes: ClassVar[set[type[ExtensionABC]]] = set()

    def __init_subclass__(cls) -> None:
        if ServiceABC in cls.__mro__:  # pragma: no cover
            return
        ExtensionABC._extension_classes.add(cls)


CommonABCT = TypeVar("CommonABCT", bound=CommonABC)


class startup_hook:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[CommonABCT], Awaitable[None]],
    ) -> None:
        self.fn = fn

    async def __call__(self, service: CommonABCT) -> None:
        await self.fn(service)


class shutdown_hook:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[CommonABCT], Awaitable[None]],
    ) -> None:
        self.fn = fn

    async def __call__(self, service: CommonABCT) -> None:
        await self.fn(service)


class lifespan_hook:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[CommonABCT], AsyncGenerator[None, None]],
    ) -> None:
        self.fn = fn


class readiness_probe:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[CommonABCT], Awaitable[bool]],
    ) -> None:
        self.fn = fn

    async def __call__(self, service: CommonABCT) -> bool:
        return await self.fn(service)


class liveness_probe:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[CommonABCT], Awaitable[bool]],
    ) -> None:
        self.fn = fn

    async def __call__(self, service: CommonABCT) -> bool:
        return await self.fn(service)


class startup_message:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[CommonABCT], Awaitable[str]],
    ) -> None:
        self.fn = fn

    async def __call__(self, service: CommonABCT) -> str:
        return await self.fn(service)


class litestar_on_app_init:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[CommonABCT, litestar.config.app.AppConfig], litestar.config.app.AppConfig],
    ) -> None:
        self.fn = fn

    def __call__(
        self,
        service: CommonABCT,
        app_config: litestar.config.app.AppConfig,
    ) -> litestar.config.app.AppConfig:
        return self.fn(service, app_config)

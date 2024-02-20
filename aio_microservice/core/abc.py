import inspect
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Awaitable
from typing import Callable, ClassVar, TypeVar

import litestar
from pydantic import BaseModel


class ServiceABC(ABC):
    __version__: ClassVar[str] = "1.0.0"
    __description__: ClassVar[str] = ""

    def __init__(self, settings: BaseModel) -> None:
        self._startup_hooks: list[startup_hook] = []
        self._shutdown_hooks: list[shutdown_hook] = []
        self._lifespan_hooks: list[lifespan_hook] = []
        self._readiness_probes: list[readiness_probe] = []
        self._liveness_probes: list[liveness_probe] = []
        self._startup_messages: list[startup_message] = []
        self._http_route_handlers: list[litestar.handlers.HTTPRouteHandler] = []
        self._http_controllers: list[litestar.types.ControllerRouterHandler] = []

        # initialize extensions
        for extension_cls in self.__class__.__bases__:
            if not issubclass(extension_cls, ServiceExtensionABC):
                continue
            init_kwargs = {}
            init_signature = inspect.signature(extension_cls.__init__)
            if "settings" in init_signature.parameters:
                init_kwargs["settings"] = settings
            extension_cls.__init__(self, **init_kwargs)

        self._collect_decorated_functions()

    def _collect_decorated_functions(self) -> None:
        # collect decorated functions
        for attribute_name in dir(self.__class__):
            attribute = getattr(self.__class__, attribute_name)
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
            elif isinstance(attribute, litestar.handlers.HTTPRouteHandler):
                self._http_route_handlers.append(attribute)

    def register_http_controller(
        self,
        controller: litestar.types.ControllerRouterHandler,
    ) -> None:
        self._http_controllers.append(controller)

    @abstractmethod
    async def run(self) -> None: ...  # pragma: no cover


class ServiceExtensionABC(ServiceABC): ...


ServiceABCT = TypeVar("ServiceABCT", bound=ServiceABC)


class startup_hook:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[ServiceABCT], Awaitable[None]],
    ) -> None:
        self.fn = fn

    async def __call__(self, service: ServiceABCT) -> None:
        await self.fn(service)


class shutdown_hook:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[ServiceABCT], Awaitable[None]],
    ) -> None:
        self.fn = fn

    async def __call__(self, service: ServiceABCT) -> None:
        await self.fn(service)


class lifespan_hook:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[ServiceABCT], AsyncGenerator[None, None]],
    ) -> None:
        self.fn = fn


class readiness_probe:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[ServiceABCT], Awaitable[bool]],
    ) -> None:
        self.fn = fn

    async def __call__(self, service: ServiceABCT) -> bool:
        return await self.fn(service)


class liveness_probe:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[ServiceABCT], Awaitable[bool]],
    ) -> None:
        self.fn = fn

    async def __call__(self, service: ServiceABCT) -> bool:
        return await self.fn(service)


class startup_message:  # noqa: N801
    def __init__(
        self,
        fn: Callable[[ServiceABCT], Awaitable[str]],
    ) -> None:
        self.fn = fn

    async def __call__(self, service: ServiceABCT) -> str:
        return await self.fn(service)

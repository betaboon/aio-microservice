from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Callable, ClassVar, TypeVar

from faststream import BaseMiddleware, FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from loguru import logger
from pydantic import BaseModel, Field, SecretStr
from typing_extensions import Concatenate, ParamSpec

from aio_microservice.amqp.asyncapi import make_asyncapi_controller
from aio_microservice.core.abc import (
    ExtensionABC,
    readiness_probe,
    shutdown_hook,
    startup_hook,
    startup_message,
)
from aio_microservice.types import Port  # noqa: TCH001

if TYPE_CHECKING:
    from faststream.rabbit.shared.schemas import ReplyConfig
    from faststream.rabbit.shared.types import TimeoutType


class AmqpSettings(BaseModel):
    host: str = Field(
        default="localhost",
        description="The ip for connecting to the broker.",
    )
    port: Port = Field(
        default=5672,
        description="The port for connecting to the broker.",
    )
    username: str = Field(
        default="guest",
        description="The username for authentication on the broker.",
    )
    password: SecretStr = Field(
        default=SecretStr("guest"),
        description="The password for authentication on the broker.",
    )
    prefetch_count: int | None = Field(
        default=None,
        description="The prefetch window size.",
    )
    timeout_graceful_shutdown: float | None = Field(
        default=None,
        description="The timeout for graceful shutdown (in seconds).",
    )


class AmqpExtensionImpl:
    def __init__(self, service: AmqpExtension, settings: AmqpSettings) -> None:
        self._service = service
        self._settings = settings
        self._faststream_rabbit_broker = RabbitBroker(
            host=self._settings.host,
            port=self._settings.port,
            login=self._settings.username,
            password=self._settings.password.get_secret_value(),
            middlewares=service.__amqp_middlewares__,
            max_consumers=self._settings.prefetch_count,
            graceful_timeout=self._settings.timeout_graceful_shutdown,
        )
        self._faststream_app = FastStream(
            broker=self._faststream_rabbit_broker,
            title=service.__class__.__name__,
            version=service.__version__,
            description=service.__description__,
        )
        self._asyncapi_controller = make_asyncapi_controller(
            app=self._faststream_app,
        )
        self._register_handlers()

    def _register_handlers(self) -> None:
        handler_methods = inspect.getmembers(
            object=self._service,
            predicate=lambda obj: hasattr(obj, AmqpDecorator.MARKER),
        )
        for handler_name, _ in handler_methods:
            handler = getattr(self._service, handler_name)
            handler_settings = getattr(handler, AmqpDecorator.MARKER)
            for handler_setting in handler_settings:
                if isinstance(handler_setting, subscriber):
                    wrapper = self._faststream_rabbit_broker.subscriber(
                        queue=handler_setting.queue,
                        exchange=handler_setting.exchange,
                        reply_config=handler_setting.reply_config,
                        no_ack=handler_setting.no_ack,
                        retry=handler_setting.retry,
                        title=handler_setting.title,
                        description=handler_setting.description,
                        include_in_schema=handler_setting.include_in_schema,
                    )
                elif isinstance(handler_setting, publisher):  # pragma: no branch
                    wrapper = self._faststream_rabbit_broker.publisher(
                        queue=handler_setting.queue,
                        exchange=handler_setting.exchange,
                        routing_key=handler_setting.routing_key,
                        reply_to=handler_setting.reply_to,
                        mandatory=handler_setting.mandatory,
                        immediate=handler_setting.immediate,
                        persist=handler_setting.persist,
                        timeout=handler_setting.timeout,
                        priority=handler_setting.priority,
                        title=handler_setting.title,
                        description=handler_setting.description,
                        include_in_schema=handler_setting.include_in_schema,
                    )
                handler = wrapper(handler)

    @property
    def broker(self) -> RabbitBroker:
        return self._faststream_rabbit_broker


class AmqpExtensionSettings(BaseModel):
    amqp: AmqpSettings = AmqpSettings()


class AmqpExtension(ExtensionABC):
    __amqp_middlewares__: ClassVar[list[type[BaseMiddleware]]] = []

    def __init__(self, settings: AmqpExtensionSettings) -> None:
        self.amqp = AmqpExtensionImpl(service=self, settings=settings.amqp)
        self.register_http_controller(self.amqp._asyncapi_controller)

    @startup_message
    async def _amqp_startup_message(self) -> str:
        return """
            # Amqp

            The following http-endpoints are available:
            - {scheme}://{host}:{port}/schema/asyncapi
            - {scheme}://{host}:{port}/schema/asyncapi.json
            - {scheme}://{host}:{port}/schema/asyncapi.yaml
        """

    @startup_hook
    async def _amqp_startup_hook(self) -> None:
        logger.info("Connecting to broker")
        await self.amqp._faststream_rabbit_broker.start()

    @shutdown_hook
    async def _amqp_shutdown_hook(self) -> None:
        logger.info("Disconnecting from broker")
        await self.amqp._faststream_rabbit_broker.close()

    @readiness_probe
    async def _amqp_readiness_probe(self) -> bool:
        if self.amqp._faststream_rabbit_broker._connection:
            # NOTE this might break.
            # faststream maintainer says, they will provide functionality like this.
            return self.amqp._faststream_rabbit_broker._connection.connected.is_set()
        return False  # pragma: no cover


AmqpExtensionT = TypeVar("AmqpExtensionT", bound=AmqpExtension)
P = ParamSpec("P")
R = TypeVar("R")


class AmqpDecorator:
    MARKER = "_amqp_decorator"


# TODO support all faststream decorator options
class subscriber(AmqpDecorator):  # noqa: N801
    def __init__(
        self,
        queue: RabbitQueue | str,
        exchange: RabbitExchange | str | None = None,
        reply_config: ReplyConfig | None = None,
        no_ack: bool = False,
        retry: bool | int = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
    ) -> None:
        self.queue = queue
        self.exchange = exchange
        self.reply_config = reply_config
        self.no_ack = no_ack
        self.retry = retry
        self.title = title
        self.description = description
        self.include_in_schema = include_in_schema

    def __call__(
        self,
        fn: Callable[Concatenate[AmqpExtensionT, P], R],
    ) -> Callable[Concatenate[AmqpExtensionT, P], R]:
        handlers = getattr(fn, self.MARKER, [])
        handlers.append(self)
        setattr(fn, self.MARKER, handlers)
        return fn


class publisher(AmqpDecorator):  # noqa: N801
    def __init__(
        self,
        queue: RabbitQueue | str = "",
        exchange: RabbitExchange | str | None = None,
        routing_key: str = "",
        reply_to: str | None = None,
        mandatory: bool = True,
        immediate: bool = False,
        persist: bool = False,
        timeout: TimeoutType = None,
        priority: int | None = None,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
    ) -> None:
        self.queue = queue
        self.exchange = exchange
        self.routing_key = routing_key
        self.reply_to = reply_to
        self.mandatory = mandatory
        self.immediate = immediate
        self.persist = persist
        self.timeout = timeout
        self.priority = priority
        self.title = title
        self.description = description
        self.include_in_schema = include_in_schema

    def __call__(
        self,
        fn: Callable[Concatenate[AmqpExtensionT, P], R],
    ) -> Callable[Concatenate[AmqpExtensionT, P], R]:
        handlers = getattr(fn, self.MARKER, [])
        handlers.append(self)
        setattr(fn, self.MARKER, handlers)
        return fn

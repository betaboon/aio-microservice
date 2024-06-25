from __future__ import annotations

import dataclasses
import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, ClassVar, TypeVar

from faststream import BaseMiddleware, FastStream
from faststream.broker.utils import default_filter
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from faststream.security import SASLPlaintext
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
    from collections.abc import Iterable

    from aio_pika.abc import TimeoutType
    from faststream.broker.types import (
        Filter,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.rabbit.message import RabbitMessage
    from faststream.rabbit.schemas import ReplyConfig
    from faststream.types import AnyDict


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
        self._faststream_rabbit_broker = self._create_faststream_broker(
            service=service,
        )
        self._faststream_app = self._create_faststream_app(
            service=service,
            broker=self._faststream_rabbit_broker,
        )
        self._asyncapi_controller = make_asyncapi_controller(
            app=self._faststream_app,
        )
        self._register_handlers()

    def _create_faststream_broker(self, service: AmqpExtension) -> RabbitBroker:
        security = SASLPlaintext(
            username=self._settings.username,
            password=self._settings.password.get_secret_value(),
        )
        return RabbitBroker(
            host=self._settings.host,
            port=self._settings.port,
            security=security,
            middlewares=service.__amqp_middlewares__,
            max_consumers=self._settings.prefetch_count,
            graceful_timeout=self._settings.timeout_graceful_shutdown,
        )

    def _create_faststream_app(self, service: AmqpExtension, broker: RabbitBroker) -> FastStream:
        return FastStream(
            broker=broker,
            title=service.__class__.__name__,
            version=service.__version__,
            description=service.__description__,
        )

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
                    subscriber_decorator = self._faststream_rabbit_broker.subscriber(
                        **dataclasses.asdict(handler_setting),
                    )
                    handler = subscriber_decorator(handler)
                elif isinstance(handler_setting, publisher):  # pragma: no branch
                    publisher_decorator = self._faststream_rabbit_broker.publisher(
                        **dataclasses.asdict(handler_setting),
                    )
                    handler = publisher_decorator(handler)

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


@dataclass
class subscriber(AmqpDecorator):  # noqa: N801
    queue: RabbitQueue | str
    exchange: RabbitExchange | str | None = None
    consume_args: AnyDict | None = None
    reply_config: ReplyConfig | None = None

    # broker arguments
    middlewares: Iterable[SubscriberMiddleware[RabbitMessage]] = ()
    filter: Filter[RabbitMessage] = default_filter
    retry: bool | int = False
    no_ack: bool = False
    no_reply: bool = False

    # AsyncAPI information
    title: str | None = None
    description: str | None = None
    include_in_schema: bool = True

    def __call__(
        self,
        fn: Callable[Concatenate[AmqpExtensionT, P], R],
    ) -> Callable[Concatenate[AmqpExtensionT, P], R]:
        handlers = getattr(fn, self.MARKER, [])
        handlers.append(self)
        setattr(fn, self.MARKER, handlers)
        return fn


@dataclass
class publisher(AmqpDecorator):  # noqa: N801
    queue: RabbitQueue | str = ""
    exchange: RabbitExchange | str | None = None
    routing_key: str = ""
    mandatory: bool = True
    immediate: bool = False
    timeout: TimeoutType = None
    persist: bool = False
    reply_to: str | None = None
    priority: int | None = None

    # specific
    middlewares: Iterable[PublisherMiddleware] = ()

    # AsyncAPI information
    title: str | None = None
    description: str | None = None
    include_in_schema: bool = True

    def __call__(
        self,
        fn: Callable[Concatenate[AmqpExtensionT, P], R],
    ) -> Callable[Concatenate[AmqpExtensionT, P], R]:
        handlers = getattr(fn, self.MARKER, [])
        handlers.append(self)
        setattr(fn, self.MARKER, handlers)
        return fn

from __future__ import annotations

from typing import Callable, TypeVar

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from loguru import logger
from pydantic import BaseModel, Field, SecretStr
from typing_extensions import Concatenate, ParamSpec

from aio_microservice.amqp.asyncapi import make_asyncapi_controller
from aio_microservice.core.abc import (
    ServiceExtensionABC,
    readiness_probe,
    shutdown_hook,
    startup_hook,
    startup_message,
)
from aio_microservice.types import Port  # noqa: TCH001


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


class AmqpExtensionImpl:
    def __init__(self, service: AmqpExtension, settings: AmqpSettings) -> None:
        self._service = service
        self._settings = settings
        self._faststream_rabbit_broker = RabbitBroker(
            host=self._settings.host,
            port=self._settings.port,
            login=self._settings.username,
            password=self._settings.password.get_secret_value(),
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
        for attribute_name in dir(self._service):
            attribute = getattr(self._service, attribute_name)
            if not hasattr(attribute, AmqpDecorator.MARKER):
                continue
            handler = attribute
            handler_settings = getattr(handler, AmqpDecorator.MARKER)
            for handler_setting in handler_settings:
                if isinstance(handler_setting, subscriber):
                    wrapper = self._faststream_rabbit_broker.subscriber(
                        queue=handler_setting.queue,
                    )
                elif isinstance(handler_setting, publisher):  # pragma: no branch
                    wrapper = self._faststream_rabbit_broker.publisher(
                        queue=handler_setting.queue,
                    )
                handler = wrapper(handler)

    @property
    def broker(self) -> RabbitBroker:
        return self._faststream_rabbit_broker


class AmqpExtensionSettings(BaseModel):
    amqp: AmqpSettings = AmqpSettings()


class AmqpExtension(ServiceExtensionABC):
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
    def __init__(self, queue: str) -> None:
        self.queue = queue

    def __call__(
        self,
        fn: Callable[Concatenate[AmqpExtensionT, P], R],
    ) -> Callable[Concatenate[AmqpExtensionT, P], R]:
        handlers = getattr(fn, self.MARKER, [])
        handlers.append(self)
        setattr(fn, self.MARKER, handlers)
        return fn


class publisher(AmqpDecorator):  # noqa: N801
    def __init__(self, queue: str) -> None:
        self.queue = queue

    def __call__(
        self,
        fn: Callable[Concatenate[AmqpExtensionT, P], R],
    ) -> Callable[Concatenate[AmqpExtensionT, P], R]:
        handlers = getattr(fn, self.MARKER, [])
        handlers.append(self)
        setattr(fn, self.MARKER, handlers)
        return fn

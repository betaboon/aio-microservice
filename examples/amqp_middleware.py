from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from loguru import logger
from pydantic import BaseModel, Field

from aio_microservice import Service, ServiceSettings, amqp
from aio_microservice.amqp import AmqpExtension, AmqpExtensionSettings, BaseMiddleware

if TYPE_CHECKING:
    from types import TracebackType


class GreetingRequest(BaseModel):
    name: str = Field(
        description="Name of person to greet",
        examples=["Jane", "John"],
    )


class GreetingResponse(BaseModel):
    message: str = Field(
        description="The greeting message",
        examples=["Hello world"],
    )


class MyAmqpMiddleware(BaseMiddleware):
    async def on_receive(self) -> None:
        logger.info(f"received {self.msg}")
        await super().on_receive()

    async def after_processed(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exec_tb: TracebackType | None = None,
    ) -> bool | None:
        logger.info(f"processed {self.msg}")
        return await super().after_processed(exc_type, exc_val, exec_tb)


class MySettings(ServiceSettings, AmqpExtensionSettings): ...


class MyService(Service[MySettings], AmqpExtension):
    __amqp_middlewares__: ClassVar = [MyAmqpMiddleware]

    @amqp.subscriber(queue="request-queue")
    async def handle_greeting_request(self, message: GreetingRequest) -> GreetingResponse:
        return GreetingResponse(message=f"Hello {message.name}")


if __name__ == "__main__":
    MyService.cli()

from __future__ import annotations

from typing import TypeVar

from loguru import logger
from pydantic import BaseModel, Field

from aio_microservice import Service, ServiceSettings, amqp
from aio_microservice.amqp import AmqpExtension, AmqpExtensionSettings


class MyBaseSettings(ServiceSettings, AmqpExtensionSettings): ...


MyBaseSettingsT = TypeVar("MyBaseSettingsT", bound=MyBaseSettings)


class MyBaseService(Service[MyBaseSettingsT], AmqpExtension):
    def __init__(self, settings: MyBaseSettingsT | None = None) -> None:
        super().__init__(settings=settings)


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


class MySettings(MyBaseSettings): ...


class MyService(MyBaseService[MySettings]):
    @amqp.subscriber(queue="request-queue")
    @amqp.publisher(queue="response-queue")
    async def handle_greeting_request(self, message: GreetingRequest) -> GreetingResponse:
        logger.info(f"{message=}")
        return GreetingResponse(message=f"Hello {message.name}")


if __name__ == "__main__":
    MyService.cli()

from __future__ import annotations

from loguru import logger
from pydantic import BaseModel, Field

from aio_microservice import Service, ServiceSettings, amqp
from aio_microservice.amqp import AmqpExtension, AmqpExtensionSettings


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


class MySettings(ServiceSettings, AmqpExtensionSettings): ...


class MyService(Service[MySettings], AmqpExtension):
    def __init__(self, settings: MySettings | None = None) -> None:
        super().__init__(settings=settings)
        self.response_publisher = self.amqp.broker.publisher(
            queue="response-queue",
            schema=GreetingResponse,
        )

    @amqp.subscriber(queue="request-queue")
    async def handle_greeting_request(self, message: GreetingRequest) -> None:
        logger.info(f"{message=}")
        response = GreetingResponse(message=f"Hello {message.name}")
        await self.response_publisher.publish(response)

    @amqp.subscriber(queue="response-queue")
    async def handle_greeting_response(self, message: GreetingResponse) -> None:
        logger.info(f"{message=}")


if __name__ == "__main__":
    MyService.cli()

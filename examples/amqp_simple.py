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
    @amqp.subscriber(queue="request-queue")
    @amqp.publisher(queue="response-queue")
    async def handle_greeting_request(self, message: GreetingRequest) -> GreetingResponse:
        logger.info(f"{message=}")
        return GreetingResponse(message=f"Hello {message.name}")

    @amqp.subscriber(queue="response-queue")
    async def handle_greeting_response(self, message: GreetingResponse) -> None:
        logger.info(f"{message=}")


if __name__ == "__main__":
    MyService.cli()

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from pydantic import BaseModel, Field

from aio_microservice import (
    Service,
    ServiceSettings,
    amqp,
    http,
    lifespan_hook,
    liveness_probe,
    readiness_probe,
    shutdown_hook,
    startup_hook,
    startup_message,
)
from aio_microservice.amqp import AmqpExtension, AmqpExtensionSettings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


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


class ExampleSettings(ServiceSettings, AmqpExtensionSettings):
    something: str = Field(
        default="else",
        description="This explains something.",
    )


class ExampleService(Service[ExampleSettings], AmqpExtension):
    __version__ = "2.0.0"
    __description__ = """
        Some description of this service.
        And some more text.
    """

    def __init__(self, settings: ExampleSettings | None = None) -> None:
        super().__init__(settings=settings)
        self.request_publisher = self.amqp.broker.publisher(
            queue="request-queue",
            schema=GreetingRequest,
        )

        self.response_publisher = self.amqp.broker.publisher(
            queue="response-queue",
            schema=GreetingResponse,
        )

    @startup_message
    async def get_startup_message(self) -> str:
        return """
            # Service Information

            Hello World.

            The service listens on {scheme}://{host}:{port}
        """

    @readiness_probe
    async def get_readiness(self) -> bool:
        return True

    @liveness_probe
    async def get_liveness(self) -> bool:
        return True

    @startup_hook
    async def on_startup(self) -> None:
        logger.debug("startup")
        await self.amqp.broker.publish(
            queue="request-queue",
            message=GreetingRequest(name="world"),
        )

    @shutdown_hook
    async def on_shutdown(self) -> None:
        logger.debug("shutdown")

    @lifespan_hook
    async def on_lifespan(self) -> AsyncGenerator[None, None]:
        logger.debug("lifespan startup")
        yield
        logger.debug("lifespan shutdown")

    @http.get(path="/greeting")
    async def get_greeting(self, name: str) -> GreetingResponse:
        response = GreetingResponse(message=f"Hello {name}")
        await self.response_publisher.publish(response)
        return response

    @http.post(path="/greeting")
    async def post_greeting(self, data: GreetingRequest) -> GreetingResponse:
        await self.request_publisher.publish(data)
        return GreetingResponse(message=f"Hello {data.name}")

    @amqp.subscriber(queue="response-queue")
    async def handle_greeting_response(self, message: GreetingResponse) -> None:
        logger.info(f"{message=}")

    @amqp.subscriber(queue="request-queue")
    @amqp.publisher(queue="response-queue")
    async def handle_greeting_request(self, message: GreetingRequest) -> GreetingResponse:
        logger.info(f"{message=}")
        return GreetingResponse(message=f"Hello {message.name}")


if __name__ == "__main__":
    ExampleService.cli()

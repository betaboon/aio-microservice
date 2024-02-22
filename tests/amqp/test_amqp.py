from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar

from testcontainers_on_whales.rabbitmq import RabbitmqContainer

from aio_microservice import Service, ServiceSettings, amqp, http
from aio_microservice.amqp import (
    AmqpExtension,
    AmqpExtensionSettings,
    AmqpSettings,
    BaseMiddleware,
    TestAmqpBroker,
)
from aio_microservice.http import TestHttpClient

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


async def test_amqp_readiness_probe() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension): ...

    container = RabbitmqContainer()
    container.start()
    container.wait_ready(timeout=120)

    settings = TestSettings(
        amqp=AmqpSettings(
            host=container.get_container_ip(),
            port=container.get_container_port(RabbitmqContainer.RABBITMQ_PORT),
        ),
    )

    service = TestService(settings=settings)
    async with TestHttpClient(service=service) as http_client:
        response_running = await http_client.get("/readiness")

        container.stop()
        container.wait_exited(timeout=10)

        response_stopped = await http_client.get("/readiness")

        assert response_running.status_code == http.status_codes.HTTP_200_OK
        assert response_stopped.status_code == http.status_codes.HTTP_503_SERVICE_UNAVAILABLE


async def test_amqp_retry_on_failure(mocker: MockerFixture) -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        def __init__(self, settings: TestSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.handler_stub = mocker.stub()
            self.handler_should_fail = True

        @amqp.subscriber(queue="test-subscriber-queue", retry=True)
        async def handle_test(self, message: str) -> None:
            self.handler_stub(message)
            if self.handler_should_fail:
                self.handler_should_fail = False
                raise Exception()  # noqa: TRY002

    container = RabbitmqContainer()
    container.start()
    container.wait_ready(timeout=120)

    settings = TestSettings(
        amqp=AmqpSettings(
            host=container.get_container_ip(),
            port=container.get_container_port(RabbitmqContainer.RABBITMQ_PORT),
        ),
    )

    service = TestService(settings=settings)
    async with TestAmqpBroker(service=service, with_real=True) as amqp_broker:
        await amqp_broker.publish(queue="test-subscriber-queue", message="TEST")
        await asyncio.sleep(0.5)

        assert len(service.handler_stub.call_args_list) == 2

    container.stop()
    container.wait_exited(timeout=10)


async def test_amqp_middleware(mocker: MockerFixture) -> None:
    middleware_stub = mocker.stub()

    class TestMiddleware(BaseMiddleware):
        async def on_receive(self) -> None:
            middleware_stub()
            await super().on_receive()

    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        __amqp_middlewares__: ClassVar = [TestMiddleware]

        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self, message: str) -> None:
            pass

    service = TestService()

    async with TestAmqpBroker(service) as amqp_broker:
        await amqp_broker.publish(queue="test-subscriber-queue", message="TEST")

    middleware_stub.assert_called_once()

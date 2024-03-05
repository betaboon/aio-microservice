from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar

import pytest
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
    from collections.abc import Iterable

    from pytest_mock import MockerFixture


@pytest.fixture
def rabbitmq_container() -> Iterable[RabbitmqContainer]:
    with RabbitmqContainer() as container:
        container.wait_ready(timeout=120)
        yield container


@pytest.fixture
def rabbitmq_ip(rabbitmq_container: RabbitmqContainer) -> str:
    return rabbitmq_container.get_container_ip()


@pytest.fixture
def rabbitmq_port(rabbitmq_container: RabbitmqContainer) -> int:
    return rabbitmq_container.get_container_port(RabbitmqContainer.RABBITMQ_PORT)


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


async def test_amqp_retry_on_failure(
    mocker: MockerFixture,
    rabbitmq_ip: str,
    rabbitmq_port: int,
) -> None:
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

    settings = TestSettings(amqp=AmqpSettings(host=rabbitmq_ip, port=rabbitmq_port))
    service = TestService(settings=settings)

    async with TestAmqpBroker(service=service, with_real=True) as amqp_broker:
        await amqp_broker.publish(queue="test-subscriber-queue", message="TEST")
        await asyncio.sleep(0.5)

        assert len(service.handler_stub.call_args_list) == 2


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


async def test_amqp_prefetch_count_none(mocker: MockerFixture) -> None:
    handler_pre_stub = mocker.stub()
    handler_post_stub = mocker.stub()

    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        def __init__(self, settings: TestSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.keep_running = True

        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self) -> None:
            handler_pre_stub()
            while self.keep_running:
                await asyncio.sleep(0.1)
            handler_post_stub()

    service = TestService()

    async with TestAmqpBroker(service) as amqp_broker:
        task1 = asyncio.create_task(amqp_broker.publish(queue="test-subscriber-queue"))
        task2 = asyncio.create_task(amqp_broker.publish(queue="test-subscriber-queue"))

        await asyncio.sleep(0.5)

        assert handler_pre_stub.call_count == 2
        assert handler_post_stub.call_count == 0

        service.keep_running = False

        await task1
        await task2

        assert handler_pre_stub.call_count == 2
        assert handler_post_stub.call_count == 2


async def test_amqp_prefetch_count_one(
    mocker: MockerFixture,
    rabbitmq_ip: str,
    rabbitmq_port: int,
) -> None:
    handler_pre_stub = mocker.stub()
    handler_post_stub = mocker.stub()

    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        __amqp_prefetch_count__ = 1

        def __init__(self, settings: TestSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.keep_running = True

        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self) -> None:
            handler_pre_stub()
            while self.keep_running:
                await asyncio.sleep(0.1)
            handler_post_stub()

    settings = TestSettings(amqp=AmqpSettings(host=rabbitmq_ip, port=rabbitmq_port))
    service = TestService(settings=settings)

    async with TestAmqpBroker(service, with_real=True) as amqp_broker:
        task1 = asyncio.create_task(amqp_broker.publish(queue="test-subscriber-queue"))
        task2 = asyncio.create_task(amqp_broker.publish(queue="test-subscriber-queue"))

        await asyncio.sleep(0.5)

        assert handler_pre_stub.call_count == 1
        assert handler_post_stub.call_count == 0

        service.keep_running = False

        await asyncio.sleep(0.5)

        await task1
        await task2

        assert handler_pre_stub.call_count == 2
        assert handler_post_stub.call_count == 2

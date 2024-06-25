from __future__ import annotations

from pydantic import BaseModel

from aio_microservice import Service, ServiceSettings, amqp, http
from aio_microservice.amqp import AmqpExtension, AmqpExtensionSettings, TestAmqpBroker
from aio_microservice.http import TestHttpClient


async def test_amqp_test_broker_subscriber_decorator() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        def __init__(self, settings: TestSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.handler_got_called = False

        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self, message: str) -> None:
            self.handler_got_called = True

    service = TestService()

    async with TestAmqpBroker(service) as amqp_broker:
        await amqp_broker.publish(queue="test-subscriber-queue", message="TEST")
        assert service.handler_got_called is True


async def test_amqp_test_broker_publisher_decorator() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        @amqp.subscriber(queue="test-subscriber-queue")
        @amqp.publisher(queue="test-publisher-queue")
        async def handle_test(self, message: str) -> str:
            return "TEST-RESPONSE"

    service = TestService()

    async with TestAmqpBroker(service) as amqp_broker:
        await amqp_broker.publish(queue="test-subscriber-queue", message="TEST-REQUEST")

        published_messages = amqp_broker.get_published_messages(queue="test-publisher-queue")
        assert len(published_messages) == 1
        assert published_messages[0] == "TEST-RESPONSE"


async def test_amqp_test_broker_publisher_decorator_pydantic() -> None:
    class Response(BaseModel):
        message: str
        number: int

    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        @amqp.subscriber(queue="test-subscriber-queue")
        @amqp.publisher(queue="test-publisher-queue")
        async def handle_test(self, message: str) -> Response:
            return Response(message="TEST-RESPONSE", number=42)

    service = TestService()

    async with TestAmqpBroker(service) as amqp_broker:
        await amqp_broker.publish(queue="test-subscriber-queue", message="TEST-REQUEST")

        published_messages = amqp_broker.get_published_messages(queue="test-publisher-queue")
        assert len(published_messages) == 1
        assert published_messages[0] == Response(message="TEST-RESPONSE", number=42).model_dump()


async def test_amqp_test_broker_publisher_instance() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        def __init__(self, settings: TestSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.publisher = self.amqp.broker.publisher(
                queue="test-publisher-queue",
            )

        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self, message: str) -> None:
            await self.publisher.publish("TEST-RESPONSE")

    service = TestService()

    async with TestAmqpBroker(service) as amqp_broker:
        await amqp_broker.publish(queue="test-subscriber-queue", message="TEST-REQUEST")

        published_messages = amqp_broker.get_published_messages(queue="test-publisher-queue")
        assert len(published_messages) == 1
        assert published_messages[0] == "TEST-RESPONSE"


async def test_amqp_test_broker_publisher_instance_pydantic() -> None:
    class Response(BaseModel):
        message: str
        number: int

    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        def __init__(self, settings: TestSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.publisher = self.amqp.broker.publisher(
                queue="test-publisher-queue",
            )

        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self, message: str) -> None:
            response = Response(message="TEST-RESPONSE", number=42)
            await self.publisher.publish(response)

    service = TestService()

    async with TestAmqpBroker(service) as amqp_broker:
        await amqp_broker.publish(queue="test-subscriber-queue", message="TEST-REQUEST")

        published_messages = amqp_broker.get_published_messages(queue="test-publisher-queue")
        assert len(published_messages) == 1
        assert published_messages[0] == Response(message="TEST-RESPONSE", number=42).model_dump()


async def test_amqp_test_broker_publisher_instance_to_exchange() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        def __init__(self, settings: TestSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.publisher = self.amqp.broker.publisher(
                exchange="test-publisher-exchange",
            )

        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self, message: str) -> None:
            await self.publisher.publish("TEST-RESPONSE")

    service = TestService()

    async with TestAmqpBroker(service) as amqp_broker:
        await amqp_broker.publish(queue="test-subscriber-queue", message="TEST-REQUEST")

        published_messages = amqp_broker.get_published_messages(exchange="test-publisher-exchange")
        assert len(published_messages) == 1
        assert published_messages[0] == "TEST-RESPONSE"


async def test_amqp_test_broker_reset_published_messages() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        @amqp.subscriber(queue="test-subscriber-queue")
        @amqp.publisher(queue="test-publisher-queue")
        async def handle_test(self, message: str) -> str:
            return "TEST-RESPONSE"

    service = TestService()

    async with TestAmqpBroker(service) as amqp_broker:
        await amqp_broker.publish(queue="test-subscriber-queue", message="TEST-REQUEST")

        published_messages = amqp_broker.get_published_messages(queue="test-publisher-queue")
        assert len(published_messages) == 1

        amqp_broker.reset_published_messages()

        published_messages = amqp_broker.get_published_messages(queue="test-publisher-queue")
        assert len(published_messages) == 0

        await amqp_broker.publish(queue="test-subscriber-queue", message="TEST-REQUEST")

        published_messages = amqp_broker.get_published_messages(queue="test-publisher-queue")
        assert len(published_messages) == 1


async def test_amqp_test_broker_publisher_inside_http_handler() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        def __init__(self, settings: TestSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.publisher = self.amqp.broker.publisher(
                queue="test-publisher-queue",
            )

        @http.get(path="/test")
        async def handle_test(self, message: str) -> str:
            response = "TEST-RESPONSE"
            await self.publisher.publish(response)
            return response

    service = TestService()
    async with TestAmqpBroker(service) as amqp_broker, TestHttpClient(service) as http_client:
        response = await http_client.get("/test?message=TEST-REQUEST")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert response.text == "TEST-RESPONSE"

        published_messages = amqp_broker.get_published_messages(queue="test-publisher-queue")

        assert len(published_messages) == 1
        assert published_messages[0] == "TEST-RESPONSE"

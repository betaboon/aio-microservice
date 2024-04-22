from aio_microservice import Service, ServiceSettings, amqp, http
from aio_microservice.amqp import AmqpExtension, AmqpExtensionSettings, TestAmqpBroker
from aio_microservice.http import TestHttpClient


async def test_amqp_asyncapi_ui() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self, message: str) -> None:
            pass

    service = TestService()
    async with TestAmqpBroker(service=service), TestHttpClient(service=service) as http_client:
        response = await http_client.get("/schema/asyncapi")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert "test-subscriber-queue:_:HandleTest" in response.text


async def test_amqp_asyncapi_schema_download_json() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self, message: str) -> None:
            pass

    service = TestService()
    async with TestAmqpBroker(service=service), TestHttpClient(service=service) as http_client:
        response = await http_client.get("/schema/asyncapi.json")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert "test-subscriber-queue:_:HandleTest" in response.json()["channels"]


async def test_amqp_asyncapi_schema_download_yaml() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self, message: str) -> None:
            pass

    service = TestService()
    async with TestAmqpBroker(service=service), TestHttpClient(service=service) as http_client:
        response = await http_client.get("/schema/asyncapi.yaml")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert "test-subscriber-queue:_:HandleTest" in response.text


async def test_amqp_asyncapi_service_description() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        __description__ = "TEST SERVICE DESCRIPTION"

    service = TestService()
    async with TestAmqpBroker(service=service), TestHttpClient(service=service) as http_client:
        response = await http_client.get("/schema/asyncapi.json")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert response.json()["info"]["description"] == TestService.__description__


async def test_amqp_asyncapi_service_version() -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        __version__ = "1.2.3"

    service = TestService()
    async with TestAmqpBroker(service=service), TestHttpClient(service=service) as http_client:
        response = await http_client.get("/schema/asyncapi.json")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert response.json()["info"]["version"] == TestService.__version__

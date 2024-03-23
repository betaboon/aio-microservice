import asyncio

import pytest
from pytest_mock import MockerFixture

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


def test_amqp_asyncapi_schema_export_json(
    event_loop: asyncio.AbstractEventLoop,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self, message: str) -> None:
            pass

    mocker.patch.dict("os.environ", {"NO_COLOR": "1", "TERM": "dumb"})
    mocker.patch("sys.argv", ["test-service", "schema", "asyncapi", "--format", "json"])

    with pytest.raises(SystemExit):
        TestService.cli()

    captured = capsys.readouterr()
    assert "test-subscriber-queue:_:HandleTest" in captured.out


def test_amqp_asyncapi_schema_export_yaml(
    event_loop: asyncio.AbstractEventLoop,
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    class TestSettings(ServiceSettings, AmqpExtensionSettings): ...

    class TestService(Service[TestSettings], AmqpExtension):
        @amqp.subscriber(queue="test-subscriber-queue")
        async def handle_test(self, message: str) -> None:
            pass

    mocker.patch.dict("os.environ", {"NO_COLOR": "1", "TERM": "dumb"})
    mocker.patch("sys.argv", ["test-service", "schema", "asyncapi", "--format", "yaml"])

    with pytest.raises(SystemExit):
        TestService.cli()

    captured = capsys.readouterr()
    assert "test-subscriber-queue:_:HandleTest" in captured.out


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

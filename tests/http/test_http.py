from typing import Any

from litestar import Request
from litestar.events import listener
from pytest_mock import MockerFixture

from aio_microservice import Service, ServiceSettings, http
from aio_microservice.http import TestHttpClient


async def test_http_event_listener(mocker: MockerFixture) -> None:
    listener_stub = mocker.stub()

    class TestService(Service[ServiceSettings]):
        @http.get(path="/test")
        async def get_test(self, request: Request[Any, Any, Any]) -> str:
            request.app.emit("get_test_called", self)
            return "TEST"

        @listener("get_test_called")
        async def on_get_test_called(self) -> None:
            listener_stub()

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/test")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert response.text == "TEST"

    listener_stub.assert_called_once()

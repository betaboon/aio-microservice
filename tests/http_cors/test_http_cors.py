from typing import Any

from litestar import Request

from aio_microservice import Service, ServiceSettings, http
from aio_microservice.http import TestHttpClient
from aio_microservice.http_cors import HttpCorsExtension, HttpCorsExtensionSettings

# TODO add some more tests and asserts to check if settings actually apply


async def test_http_cors() -> None:
    class TestServiceSettings(ServiceSettings, HttpCorsExtensionSettings): ...

    class TestService(Service[TestServiceSettings], HttpCorsExtension):
        @http.get(path="/test")
        async def get_test(self, request: Request[Any, Any, Any]) -> str:
            return "TEST"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.options(
            url="/test",
            headers={
                "Origin": "https://example.com",
            },
        )
        assert "Access-Control-Allow-Origin" in response.headers

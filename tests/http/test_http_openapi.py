from aio_microservice import Service, ServiceSettings, http
from aio_microservice.http import TestHttpClient


async def test_http_openapi_swagger_ui() -> None:
    class TestService(Service[ServiceSettings]):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/schema/openapi")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert "/test" in response.text


async def test_http_openapi_json() -> None:
    class TestService(Service[ServiceSettings]):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/schema/openapi.json")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert "/test" in response.json()["paths"]


async def test_http_openapi_yaml() -> None:
    class TestService(Service[ServiceSettings]):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/schema/openapi.yaml")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert "/test" in response.text


async def test_http_openapi_service_description() -> None:
    class TestService(Service[ServiceSettings]):
        __description__ = "TEST SERVICE DESCRIPTION"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/schema/openapi.json")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert response.json()["info"]["description"] == TestService.__description__


async def test_http_openapi_service_version() -> None:
    class TestService(Service[ServiceSettings]):
        __version__ = "1.2.3"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/schema/openapi.json")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert response.json()["info"]["version"] == TestService.__version__

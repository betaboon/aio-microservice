from aio_microservice import Service, ServiceSettings, http
from aio_microservice.http import TestHttpClient


async def test_http_test_client() -> None:
    class TestService(Service[ServiceSettings]):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/test")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert response.text == "TEST"

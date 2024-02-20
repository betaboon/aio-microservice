from __future__ import annotations

from aio_microservice import (
    Service,
    ServiceSettings,
    http,
    liveness_probe,
    readiness_probe,
)
from aio_microservice.http import TestHttpClient


async def test_readiness_probe() -> None:
    class TestService(Service[ServiceSettings]):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.test_readiness = True

        @readiness_probe
        async def test_readiness_probe(self) -> bool:
            return self.test_readiness

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/readiness")
        assert response.status_code == http.status_codes.HTTP_200_OK

        service.test_readiness = False
        response = await client.get("/readiness")
        assert response.status_code == http.status_codes.HTTP_503_SERVICE_UNAVAILABLE


async def test_readiness_probe_stacking() -> None:
    class TestService(Service[ServiceSettings]):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.test_readiness_1 = True
            self.test_readiness_2 = True

        @readiness_probe
        async def test_readiness_probe_1(self) -> bool:
            return self.test_readiness_1

        @readiness_probe
        async def test_readiness_probe_2(self) -> bool:
            return self.test_readiness_2

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/readiness")
        assert response.status_code == http.status_codes.HTTP_200_OK

        service.test_readiness_2 = False
        response = await client.get("/readiness")
        assert response.status_code == http.status_codes.HTTP_503_SERVICE_UNAVAILABLE


async def test_liveness_probe() -> None:
    class TestService(Service[ServiceSettings]):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.test_liveness = True

        @liveness_probe
        async def test_liveness_probe(self) -> bool:
            return self.test_liveness

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/liveness")
        assert response.status_code == http.status_codes.HTTP_200_OK

        service.test_liveness = False
        response = await client.get("/liveness")
        assert response.status_code == http.status_codes.HTTP_503_SERVICE_UNAVAILABLE


async def test_liveness_probe_stacking() -> None:
    class TestService(Service[ServiceSettings]):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.test_liveness_1 = True
            self.test_liveness_2 = True

        @liveness_probe
        async def test_liveness_probe_1(self) -> bool:
            return self.test_liveness_1

        @liveness_probe
        async def test_liveness_probe_2(self) -> bool:
            return self.test_liveness_2

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/liveness")
        assert response.status_code == http.status_codes.HTTP_200_OK

        service.test_liveness_2 = False
        response = await client.get("/liveness")
        assert response.status_code == http.status_codes.HTTP_503_SERVICE_UNAVAILABLE

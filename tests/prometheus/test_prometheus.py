from __future__ import annotations

from typing import ClassVar

from aio_microservice import Service, ServiceSettings, http
from aio_microservice.http import TestHttpClient
from aio_microservice.prometheus import (
    Counter,
    PrometheusExtension,
    PrometheusExtensionSettings,
    PrometheusSettings,
)


async def test_prometheus_http_metrics() -> None:
    class TestSettings(ServiceSettings, PrometheusExtensionSettings): ...

    class TestService(Service[TestSettings], PrometheusExtension):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        await client.get("/test")

        response = await client.get("/metrics")
        assert response.status_code == http.status_codes.HTTP_200_OK
        metrics_lines = response.text.splitlines()
        assert (
            'http_requests_total{app_name="test-service",method="GET",path="/test",status_code="200"} 1.0'  # noqa: E501
            in metrics_lines
        )


async def test_prometheus_extra_labels() -> None:
    class TestSettings(ServiceSettings, PrometheusExtensionSettings): ...

    class TestService(Service[TestSettings], PrometheusExtension):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    settings = TestSettings(
        prometheus=PrometheusSettings(
            prefix="my_prefix",
            labels={"extra_label": "value"},
        ),
    )

    service = TestService(settings=settings)
    async with TestHttpClient(service=service) as client:
        await client.get("/test")

        response = await client.get("/metrics")
        assert response.status_code == http.status_codes.HTTP_200_OK
        metrics_lines = response.text.splitlines()
        assert (
            'my_prefix_requests_total{app_name="test-service",extra_label="value",method="GET",path="/test",status_code="200"} 1.0'  # noqa: E501
            in metrics_lines
        )


async def test_prometheus_default_exclude() -> None:
    class TestSettings(ServiceSettings, PrometheusExtensionSettings): ...

    class TestService(Service[TestSettings], PrometheusExtension): ...

    service = TestService()
    async with TestHttpClient(service=service) as client:
        await client.get("/readiness")
        await client.get("/liveness")

        response = await client.get("/metrics")
        assert response.status_code == http.status_codes.HTTP_200_OK
        metrics_lines = response.text.splitlines()
        assert (
            'http_requests_total{app_name="test-service",method="GET",path="/readiness",status_code="200"} 1.0'  # noqa: E501
            not in metrics_lines
        )
        assert (
            'http_requests_total{app_name="test-service",method="GET",path="/liveness",status_code="200"} 1.0'  # noqa: E501
            not in metrics_lines
        )
        assert (
            'http_requests_total{app_name="test-service",method="GET",path="/metrics",status_code="200"} 1.0'  # noqa: E501
            not in metrics_lines
        )


async def test_prometheus_custom_metrics() -> None:
    class Metrics:
        processing_test_requests: ClassVar[Counter] = Counter(
            name="processed_test_requests",
            documentation="Number of processed /test requests",
        )

    class TestSettings(ServiceSettings, PrometheusExtensionSettings): ...

    class TestService(Service[TestSettings], PrometheusExtension):
        def __init__(self, settings: TestSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.metrics = Metrics()

        @http.get(path="/test")
        async def get_test(self) -> str:
            self.metrics.processing_test_requests.inc()
            return "TEST"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        await client.get("/test")

        response = await client.get("/metrics")
        assert response.status_code == http.status_codes.HTTP_200_OK
        metrics_lines = response.text.split("\n")
        assert "processed_test_requests_total 1.0" in metrics_lines

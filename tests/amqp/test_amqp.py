from testcontainers_on_whales.rabbitmq import RabbitmqContainer

from aio_microservice import Service, ServiceSettings, http
from aio_microservice.amqp import (
    AmqpExtension,
    AmqpExtensionSettings,
    AmqpSettings,
)
from aio_microservice.http import TestHttpClient


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

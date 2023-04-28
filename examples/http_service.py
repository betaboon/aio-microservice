from dataclasses import dataclass
from datetime import datetime

from aio_microservice import HTTPConfig, HTTPMixin, Service, http


@dataclass
class HealthcheckRequest:
    some_attribute: bool = True


@dataclass
class HealthcheckResponse:
    alive: bool
    uptime: int


class HTTPService(Service, HTTPMixin):
    http_config = HTTPConfig(
        host="0.0.0.0",
        port=5000,
    )

    def __init__(self) -> None:
        super().__init__()
        self.started_at: datetime

    async def after_start(self) -> None:
        self.stated_at = datetime.now()

    @http(method="GET", route="/healthcheck")
    async def get_healthcheck(self, request: HealthcheckRequest) -> HealthcheckResponse:
        uptime = datetime.now() - self.started_at
        return HealthcheckResponse(
            alive=True,
            uptime=uptime.seconds,
        )


if __name__ == "__main__":
    service = HTTPService()
    # which run-api?
    service.run()
    # or
    aio_microservice.run(service)
    # or
    asyncio.run(service.run())

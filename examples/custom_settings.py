from __future__ import annotations

from loguru import logger
from pydantic import Field

from aio_microservice import Service, ServiceSettings


class MySettings(ServiceSettings):
    some: str = Field(
        default="value",
        description="sets some setting",
    )


class MyService(Service[MySettings]):
    def __init__(self, settings: MySettings | None = None) -> None:
        super().__init__(settings=settings)

        logger.debug(f"{self.settings.some=}")


if __name__ == "__main__":
    MyService.cli()

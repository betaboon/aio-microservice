from collections.abc import AsyncGenerator

from loguru import logger

from aio_microservice import (
    Service,
    ServiceSettings,
    lifespan_hook,
    shutdown_hook,
    startup_hook,
)


class MyService(Service[ServiceSettings]):
    @startup_hook
    async def my_startup_hook(self) -> None:
        logger.debug("my startup hook")

    @shutdown_hook
    async def my_shutdown_hook(self) -> None:
        logger.debug("my shutdown hook")

    @lifespan_hook
    async def my_lifespan_hook(self) -> AsyncGenerator[None, None]:
        logger.debug("my lifespan hook - startup")
        yield
        logger.debug("my lifespan hook - shutdown")


if __name__ == "__main__":
    MyService.cli()

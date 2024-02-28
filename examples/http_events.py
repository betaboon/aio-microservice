from typing import Any

from litestar import Request
from litestar.events import listener
from loguru import logger

from aio_microservice import Service, ServiceSettings, http


class MyService(Service[ServiceSettings]):
    @listener("greeting_requested")
    async def on_greeting_requested_event(self, name: str) -> None:
        logger.info(f"got greeting_requested event with '{name=}'")

    @http.get(path="/greeting")
    async def get_greeting(self, name: str, request: Request[Any, Any, Any]) -> None:
        request.app.emit("greeting_requested", self, name=name)


if __name__ == "__main__":
    MyService.cli()

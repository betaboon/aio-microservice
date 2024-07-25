from litestar.config.app import AppConfig
from pydantic import BaseModel, Field

from aio_microservice import Service, ServiceSettings, http, litestar_on_app_init
from aio_microservice.http import Controller


class GreetingRequest(BaseModel):
    name: str = Field(
        description="Name of person to greet",
        examples=["Jane", "John"],
    )


class GreetingResponse(BaseModel):
    message: str = Field(
        description="The greeting message",
        examples=["Hello world"],
    )


class MyController(Controller):
    @http.get(path="/greeting")
    async def get_greeting(self, name: str) -> GreetingResponse:
        return GreetingResponse(message=f"Hello {name}")


class MyService(Service[ServiceSettings]):
    @litestar_on_app_init
    def my_litestar_on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config.route_handlers.append(MyController)
        return app_config


if __name__ == "__main__":
    MyService.cli()

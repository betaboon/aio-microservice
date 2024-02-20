from litestar import Controller, get
from pydantic import BaseModel, Field

from aio_microservice import Service, ServiceSettings


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
    @get(path="/greeting")
    async def get_greeting(self, name: str) -> GreetingResponse:
        return GreetingResponse(message=f"Hello {name}")


class MyService(Service[ServiceSettings]):
    def __init__(self, settings: ServiceSettings) -> None:
        super().__init__(settings=settings)
        # FIXME
        self.register_http_controller(MyController)


if __name__ == "__main__":
    MyService.cli()

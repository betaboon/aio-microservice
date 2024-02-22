from typing import ClassVar

from pydantic import BaseModel, Field

from aio_microservice import Service, ServiceSettings, http
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
    __http_controllers__: ClassVar = [MyController]


if __name__ == "__main__":
    MyService.cli()

from pydantic import BaseModel, Field

from aio_microservice import Service, ServiceSettings, http


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


class MyService(Service[ServiceSettings]):
    @http.get(path="/greeting")
    async def get_greeting(self, name: str) -> GreetingResponse:
        return GreetingResponse(message=f"Hello {name}")

    @http.post(path="/greeting")
    async def post_greeting(self, data: GreetingRequest) -> GreetingResponse:
        return GreetingResponse(message=f"Hello {data.name}")


if __name__ == "__main__":
    MyService.cli()

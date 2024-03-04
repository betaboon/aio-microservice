from pydantic import BaseModel, Field

from aio_microservice import Service, ServiceSettings, http
from aio_microservice.core.abc import ExtensionABC


class MySettings(BaseModel):
    something: str = Field(default="value", description="some description")


class MyExtensionImpl:
    def __init__(self, settings: MySettings) -> None:
        self._settings = settings

    def do_something(self) -> str:
        return f"do {self._settings.something}"


class MyExtensionSettings(BaseModel):
    my: MySettings = MySettings()


class MyExtension(ExtensionABC):
    def __init__(self, settings: MyExtensionSettings) -> None:
        self.my = MyExtensionImpl(settings=settings.my)


class MyServiceSettings(ServiceSettings, MyExtensionSettings): ...


class MyService(Service[MyServiceSettings], MyExtension):
    @http.get(path="/something")
    async def get_something(self) -> str:
        return self.my.do_something()


if __name__ == "__main__":
    MyService.cli()

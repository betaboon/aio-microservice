from aio_microservice import Service, ServiceSettings, http
from aio_microservice.prometheus import PrometheusExtension, PrometheusExtensionSettings


class MyServiceSettings(ServiceSettings, PrometheusExtensionSettings): ...


class MyService(Service[MyServiceSettings], PrometheusExtension):
    @http.get(path="/greeting")
    async def get_greeting(self, name: str) -> str:
        return f"Hello {name}"


if __name__ == "__main__":
    MyService.cli()

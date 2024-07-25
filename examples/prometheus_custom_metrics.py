from aio_microservice import Service, ServiceSettings, http
from aio_microservice.prometheus import Counter, PrometheusExtension, PrometheusExtensionSettings

greetings_count = Counter(
    name="greetings_count",
    documentation="Number of greetings executed by name",
    labelnames=["name"],
)


class MyServiceSettings(ServiceSettings, PrometheusExtensionSettings): ...


class MyService(Service[MyServiceSettings], PrometheusExtension):
    @http.get(path="/greeting")
    async def get_greeting(self, name: str) -> str:
        greetings_count.labels(name=name).inc()
        return f"Hello {name}"


if __name__ == "__main__":
    MyService.cli()

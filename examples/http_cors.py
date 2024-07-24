from aio_microservice import Service, ServiceSettings
from aio_microservice.http_cors import HttpCorsExtension, HttpCorsExtensionSettings


class MyServiceSettings(ServiceSettings, HttpCorsExtensionSettings): ...


class MyService(Service[MyServiceSettings], HttpCorsExtension): ...


if __name__ == "__main__":
    MyService.cli()

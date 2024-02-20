from aio_microservice import Service, ServiceSettings


class MyService(Service[ServiceSettings]): ...


if __name__ == "__main__":
    MyService.cli()

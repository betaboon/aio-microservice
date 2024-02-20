from aio_microservice import Service, ServiceSettings


class MyService(Service[ServiceSettings]):
    __version__ = "1.2.3"
    __description__ = """
        Some description of this service.
    """


if __name__ == "__main__":
    MyService.cli()

from aio_microservice import Service, ServiceSettings, startup_message


class MyService(Service[ServiceSettings]):
    @startup_message
    async def my_startup_message(self) -> str:
        return """
            # MyService

            Hello world
        """


if __name__ == "__main__":
    MyService.cli()

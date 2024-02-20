from aio_microservice import Service, ServiceSettings, liveness_probe, readiness_probe


class MyService(Service[ServiceSettings]):
    @readiness_probe
    async def my_readiness_probe(self) -> bool:
        return True

    @liveness_probe
    async def my_liveness_probe(self) -> bool:
        return True


if __name__ == "__main__":
    MyService.cli()

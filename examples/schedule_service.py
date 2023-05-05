from aio_microservice import Service, schedule


class ScheduleService(Service):
    @schedule(interval=5)
    async def do_every_five_seconds(self) -> None:
        pass

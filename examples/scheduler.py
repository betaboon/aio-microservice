from __future__ import annotations

from loguru import logger

from aio_microservice import Service, ServiceSettings, scheduler
from aio_microservice.scheduler import SchedulerExtension


class MyService(Service[ServiceSettings], SchedulerExtension):
    def __init__(self, settings: ServiceSettings | None = None) -> None:
        super().__init__(settings=settings)

        self.scheduler.add_interval(fn=self.do_something_interval, seconds=5)
        self.scheduler.add_cron(fn=self.do_something_cron, second=10)
        self.scheduler.add_crontab(fn=self.do_something_crontab, expression="* * * * *")

    async def do_something_interval(self) -> None:
        logger.info("doing something interval")

    async def do_something_cron(self) -> None:
        logger.info("doing something cron")

    async def do_something_crontab(self) -> None:
        logger.info("doing something crontab")

    @scheduler.interval(seconds=5)
    async def my_interval_schedule(self) -> None:
        logger.info("running interval schedule")

    @scheduler.cron(second=10)
    async def my_cron_schedule(self) -> None:
        logger.info("running cron schedule")

    @scheduler.crontab(expression="* * * * *")
    async def my_crontab_schedule(self) -> None:
        logger.info("running crontab schedule")


if __name__ == "__main__":
    MyService.cli()

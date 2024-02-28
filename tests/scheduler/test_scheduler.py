from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aio_microservice import Service, ServiceSettings, scheduler
from aio_microservice.http import TestHttpClient
from aio_microservice.scheduler import SchedulerExtension

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


async def test_scheduler_interval(mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings], SchedulerExtension):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.do_every_second_stub = mocker.stub()

        @scheduler.interval(seconds=1)
        async def do_every_second(self) -> None:
            self.do_every_second_stub()

    service = TestService()
    async with TestHttpClient(service=service):
        await asyncio.sleep(2.5)

    assert 2 <= len(service.do_every_second_stub.call_args_list) <= 3


async def test_scheduler_cron(mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings], SchedulerExtension):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.do_every_second_stub = mocker.stub()

        @scheduler.cron(second="*/1")
        async def do_every_second(self) -> None:
            self.do_every_second_stub()

    service = TestService()
    async with TestHttpClient(service=service):
        await asyncio.sleep(2.5)

    assert 2 <= len(service.do_every_second_stub.call_args_list) <= 3


async def test_scheduler_crontab(mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings], SchedulerExtension):
        @scheduler.crontab(expression="* * * * *")
        async def do_every_minute(self) -> None:
            pass

    service = TestService()

    jobs = service.scheduler.scheduler.get_jobs()
    assert len(jobs) == 1

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from aio_microservice import Service, ServiceSettings, readiness_probe, scheduler
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

    assert len(service.do_every_second_stub.call_args_list) == 3


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


def test_scheduler_crontab() -> None:
    class TestService(Service[ServiceSettings], SchedulerExtension):
        @scheduler.crontab(expression="* * * * *")
        async def do_every_minute(self) -> None:
            pass

    service = TestService()

    jobs = service.scheduler.scheduler.get_jobs()
    assert len(jobs) == 1


@pytest.mark.xfail(reason="Needs custom service lifecycle hook")
async def test_scheduler_does_not_run_before_service_ready(mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings], SchedulerExtension):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.is_ready = False
            self.interval_method_stub = mocker.stub()

        @readiness_probe
        async def readiness_probe(self) -> bool:
            return self.is_ready

        @scheduler.interval(seconds=1)
        async def do_every_second(self) -> None:
            self.interval_method_stub(self.is_ready)

    service = TestService()
    async with TestHttpClient(service=service):
        assert service.is_ready is False

        # give enough time to "potentially" execute the interval twice
        await asyncio.sleep(2)

        assert service.interval_method_stub.call_count == 0

        service.is_ready = True

        # give enough time to "potentially" execute the interval twice
        await asyncio.sleep(2)

        assert service.interval_method_stub.call_count > 0
        assert service.interval_method_stub.call_args.args[0] is True

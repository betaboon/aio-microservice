from __future__ import annotations

import inspect
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, TypeVar

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore
from loguru import logger
from typing_extensions import Concatenate, ParamSpec

from aio_microservice.core.abc import ExtensionABC, shutdown_hook, startup_hook

if TYPE_CHECKING:
    from collections.abc import Awaitable


class SchedulerExtensionImpl:
    def __init__(self, service: SchedulerExtension) -> None:
        self._service = service
        self._scheduler = AsyncIOScheduler(timezone=timezone.utc)
        self._register_schedules()

    def _register_schedules(self) -> None:
        schedule_methods = inspect.getmembers(
            object=self._service,
            predicate=lambda obj: hasattr(obj, SchedulerDecorator.MARKER),
        )
        for schedule_name, _ in schedule_methods:
            schedule = getattr(self._service, schedule_name)
            schedule_settings = getattr(schedule, SchedulerDecorator.MARKER)
            for schedule_setting in schedule_settings:
                if isinstance(schedule_setting, interval):
                    self.add_interval(
                        fn=schedule,
                        weeks=schedule_setting.weeks,
                        days=schedule_setting.days,
                        hours=schedule_setting.hours,
                        minutes=schedule_setting.minutes,
                        seconds=schedule_setting.seconds,
                    )
                elif isinstance(schedule_setting, cron):
                    self.add_cron(
                        fn=schedule,
                        year=schedule_setting.year,
                        month=schedule_setting.month,
                        day=schedule_setting.day,
                        week=schedule_setting.week,
                        day_of_week=schedule_setting.day_of_week,
                        hour=schedule_setting.hour,
                        minute=schedule_setting.minute,
                        second=schedule_setting.second,
                    )
                elif isinstance(schedule_setting, crontab):  # pragma: no branch
                    self.add_crontab(
                        fn=schedule,
                        expression=schedule_setting.expression,
                    )

    @property
    def scheduler(self) -> AsyncIOScheduler:
        return self._scheduler

    def add_interval(
        self,
        fn: Callable[[], Awaitable[None]],
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> None:
        trigger = IntervalTrigger(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
        )
        self._scheduler.add_job(
            func=fn,
            trigger=trigger,
            # Note: v3.x only starts _after_ the interval passed, while v4.x will run now and after
            # every interval
            # See https://github.com/agronholm/apscheduler/issues/97#issuecomment-985035673
            # TODO remove this when upgrading to v4.x
            next_run_time=datetime.now(tz=timezone.utc),
        )

    def add_cron(
        self,
        fn: Callable[[], Awaitable[None]],
        year: int | str | None = None,
        month: int | str | None = None,
        day: int | str | None = None,
        week: int | str | None = None,
        day_of_week: int | str | None = None,
        hour: int | str | None = None,
        minute: int | str | None = None,
        second: int | str | None = None,
    ) -> None:
        trigger = CronTrigger(
            year=year,
            month=month,
            day=day,
            week=week,
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            second=second,
        )
        self._scheduler.add_job(func=fn, trigger=trigger)

    def add_crontab(
        self,
        fn: Callable[[], Awaitable[None]],
        expression: str,
    ) -> None:
        trigger = CronTrigger.from_crontab(expr=expression)
        self._scheduler.add_job(func=fn, trigger=trigger)


class SchedulerExtension(ExtensionABC):
    def __init__(self) -> None:
        self.scheduler = SchedulerExtensionImpl(service=self)

    @startup_hook
    async def _scheduler_startup_hook(self) -> None:
        logger.info("Starting scheduler")
        self.scheduler._scheduler.start()

    @shutdown_hook
    async def _scheduler_shutdown_hook(self) -> None:
        logger.info("Stopping scheduler")
        self.scheduler._scheduler.shutdown()


SchedulerExtensionT = TypeVar("SchedulerExtensionT", bound=SchedulerExtension)
P = ParamSpec("P")
R = TypeVar("R")


class SchedulerDecorator:
    MARKER = "_scheduler_decorator"


class interval(SchedulerDecorator):  # noqa: N801
    def __init__(
        self,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> None:
        self.weeks = weeks
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    def __call__(
        self,
        fn: Callable[Concatenate[SchedulerExtensionT, P], R],
    ) -> Callable[Concatenate[SchedulerExtensionT, P], R]:
        schedules = getattr(fn, self.MARKER, [])
        schedules.append(self)
        setattr(fn, self.MARKER, schedules)
        return fn


class cron(SchedulerDecorator):  # noqa: N801
    def __init__(
        self,
        year: int | str | None = None,
        month: int | str | None = None,
        day: int | str | None = None,
        week: int | str | None = None,
        day_of_week: int | str | None = None,
        hour: int | str | None = None,
        minute: int | str | None = None,
        second: int | str | None = None,
    ) -> None:
        self.year = year
        self.month = month
        self.day = day
        self.week = week
        self.day_of_week = day_of_week
        self.hour = hour
        self.minute = minute
        self.second = second

    def __call__(
        self,
        fn: Callable[Concatenate[SchedulerExtensionT, P], R],
    ) -> Callable[Concatenate[SchedulerExtensionT, P], R]:
        schedules = getattr(fn, self.MARKER, [])
        schedules.append(self)
        setattr(fn, self.MARKER, schedules)
        return fn


class crontab(SchedulerDecorator):  # noqa: N801
    def __init__(self, expression: str) -> None:
        self.expression = expression

    def __call__(
        self,
        fn: Callable[Concatenate[SchedulerExtensionT, P], R],
    ) -> Callable[Concatenate[SchedulerExtensionT, P], R]:
        schedules = getattr(fn, self.MARKER, [])
        schedules.append(self)
        setattr(fn, self.MARKER, schedules)
        return fn

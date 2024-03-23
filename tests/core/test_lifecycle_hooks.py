from __future__ import annotations

from typing import TYPE_CHECKING

from aio_microservice import (
    Service,
    ServiceSettings,
    lifespan_hook,
    shutdown_hook,
    startup_hook,
)
from aio_microservice.http import TestHttpClient

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from pytest_mock import MockerFixture


async def test_startup_hook(mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings]):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.startup_hook_stub = mocker.stub()

        @startup_hook
        async def test_startup_hook(self) -> None:
            self.startup_hook_stub()

    service = TestService()
    async with TestHttpClient(service=service):
        service.startup_hook_stub.assert_called_once()

    service.startup_hook_stub.assert_called_once()


async def test_startup_hook_stacking(mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings]):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.startup_hook_1_stub = mocker.stub()
            self.startup_hook_2_stub = mocker.stub()

        @startup_hook
        async def test_startup_hook_1(self) -> None:
            self.startup_hook_1_stub()

        @startup_hook
        async def test_startup_hook_2(self) -> None:
            self.startup_hook_2_stub()

    service = TestService()
    async with TestHttpClient(service=service):
        service.startup_hook_1_stub.assert_called_once()
        service.startup_hook_2_stub.assert_called_once()

    service.startup_hook_1_stub.assert_called_once()
    service.startup_hook_2_stub.assert_called_once()


async def test_shutdown_hook(mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings]):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.shutdown_hook_stub = mocker.stub()

        @shutdown_hook
        async def test_shutdown_hook(self) -> None:
            self.shutdown_hook_stub()

    service = TestService()
    async with TestHttpClient(service=service):
        service.shutdown_hook_stub.assert_not_called()

    service.shutdown_hook_stub.assert_called_once()


async def test_shutdown_hook_stacking(mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings]):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.shutdown_hook_1_stub = mocker.stub()
            self.shutdown_hook_2_stub = mocker.stub()

        @shutdown_hook
        async def test_shutdown_hook_1(self) -> None:
            self.shutdown_hook_1_stub()

        @shutdown_hook
        async def test_shutdown_hook_2(self) -> None:
            self.shutdown_hook_2_stub()

    service = TestService()
    async with TestHttpClient(service=service):
        service.shutdown_hook_1_stub.assert_not_called()
        service.shutdown_hook_2_stub.assert_not_called()

    service.shutdown_hook_1_stub.assert_called_once()
    service.shutdown_hook_2_stub.assert_called_once()


async def test_lifespan_hook(mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings]):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.startup_hook_stub = mocker.stub()
            self.shutdown_hook_stub = mocker.stub()

        @lifespan_hook
        async def test_lifespan_hook(self) -> AsyncGenerator[None, None]:
            self.startup_hook_stub()
            yield
            self.shutdown_hook_stub()

    service = TestService()
    async with TestHttpClient(service=service):
        service.startup_hook_stub.assert_called_once()
        service.shutdown_hook_stub.assert_not_called()

    service.startup_hook_stub.assert_called_once()
    service.shutdown_hook_stub.assert_called_once()


async def test_lifespan_hook_stacking(mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings]):
        def __init__(self, settings: ServiceSettings | None = None) -> None:
            super().__init__(settings=settings)
            self.startup_hook_1_stub = mocker.stub()
            self.startup_hook_2_stub = mocker.stub()
            self.shutdown_hook_1_stub = mocker.stub()
            self.shutdown_hook_2_stub = mocker.stub()

        @lifespan_hook
        async def test_lifespan_hook_1(self) -> AsyncGenerator[None, None]:
            self.startup_hook_1_stub()
            yield
            self.shutdown_hook_1_stub()

        @lifespan_hook
        async def test_lifespan_hook_2(self) -> AsyncGenerator[None, None]:
            self.startup_hook_2_stub()
            yield
            self.shutdown_hook_2_stub()

    service = TestService()
    async with TestHttpClient(service=service):
        service.startup_hook_1_stub.assert_called_once()
        service.startup_hook_2_stub.assert_called_once()
        service.shutdown_hook_1_stub.assert_not_called()
        service.shutdown_hook_2_stub.assert_not_called()

    service.startup_hook_1_stub.assert_called_once()
    service.startup_hook_2_stub.assert_called_once()
    service.shutdown_hook_1_stub.assert_called_once()
    service.shutdown_hook_2_stub.assert_called_once()

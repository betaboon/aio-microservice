import pytest

from aio_microservice import (
    Service,
    ServiceSettings,
    startup_message,
)
from aio_microservice.http import TestHttpClient


async def test_startup_message(capsys: pytest.CaptureFixture[str]) -> None:
    class TestService(Service[ServiceSettings]):
        @startup_message
        async def test_startup_message(self) -> str:
            return "TEST STARTUP MESSAGE"

    service = TestService()
    async with TestHttpClient(service=service):
        captured = capsys.readouterr()
        assert "TEST STARTUP MESSAGE" in captured.out


async def test_startup_message_stacking(capsys: pytest.CaptureFixture[str]) -> None:
    class TestService(Service[ServiceSettings]):
        @startup_message
        async def test_startup_message_1(self) -> str:
            return "TEST STARTUP MESSAGE 1"

        @startup_message
        async def test_startup_message_2(self) -> str:
            return "TEST STARTUP MESSAGE 2"

    service = TestService()
    async with TestHttpClient(service=service):
        captured = capsys.readouterr()
        assert "TEST STARTUP MESSAGE 1" in captured.out
        assert "TEST STARTUP MESSAGE 2" in captured.out

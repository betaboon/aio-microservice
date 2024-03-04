from typing import TypeVar

from aio_microservice import Service, ServiceSettings
from aio_microservice.core.abc import ExtensionABC


async def test_custom_base() -> None:
    TestBaseSettingsT = TypeVar("TestBaseSettingsT", bound=ServiceSettings)

    class TestBase(Service[TestBaseSettingsT]): ...

    class TestSettings(ServiceSettings):
        somethings: str = "else"

    class TestService(TestBase[TestSettings]): ...

    service = TestService()
    assert service.settings.somethings == "else"


async def test_custom_base_with_extensions() -> None:
    class TestExtension(ExtensionABC): ...

    TestBaseSettingsT = TypeVar("TestBaseSettingsT", bound=ServiceSettings)

    class TestBase(Service[TestBaseSettingsT], TestExtension): ...

    class TestSettings(ServiceSettings):
        somethings: str = "else"

    class TestService(TestBase[TestSettings]): ...

    service = TestService()
    assert service.settings.somethings == "else"

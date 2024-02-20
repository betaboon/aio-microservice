from aio_microservice import (
    Service,
    ServiceSettings,
)


async def test_custom_settings() -> None:
    class TestSettings(ServiceSettings):
        test_value: str = "TEST"

    class TestService(Service[TestSettings]): ...

    service = TestService()
    assert isinstance(service.settings, TestSettings)
    assert service.settings.test_value == "TEST"

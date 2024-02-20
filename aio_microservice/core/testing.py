from typing import TypeVar

from litestar import Litestar
from litestar.testing import AsyncTestClient

from aio_microservice.core.service import Service, ServiceSettingsT

ServiceT = TypeVar("ServiceT", bound=Service[ServiceSettingsT])  # type: ignore[valid-type]


class TestHttpClient(AsyncTestClient[Litestar]):
    def __init__(self, service: ServiceT) -> None:
        super().__init__(app=service._litestar_app)
        self._service = service

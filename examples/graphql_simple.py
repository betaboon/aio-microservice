from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import strawberry

from aio_microservice import Service, ServiceSettings
from aio_microservice.graphql import GraphqlContext, GraphqlExtension

if TYPE_CHECKING:
    from strawberry.types import Info


@strawberry.type
class Query:
    @strawberry.field
    async def hello(
        self,
        info: Info[GraphqlContext[MyService], None],
    ) -> str:
        return info.context.service.settings.welcome_message


class MySettings(ServiceSettings):
    welcome_message: str = "Hello World"


class MyService(Service[MySettings], GraphqlExtension):
    __graphql_schema__: ClassVar = strawberry.Schema(query=Query)


if __name__ == "__main__":
    MyService.cli()

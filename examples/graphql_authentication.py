from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

import strawberry

from aio_microservice import Service, ServiceSettings
from aio_microservice.graphql import GraphqlContext, GraphqlExtension

if TYPE_CHECKING:
    from strawberry.types import Info


class IsAuthenticated(strawberry.BasePermission):
    message = "User is not authenticated"

    def has_permission(
        self,
        source: Any,  # noqa: ANN401
        info: Info[GraphqlContext[MyService], None],
        **kwargs: Any,  # noqa: ANN401
    ) -> bool:
        request = info.context.request
        if request is None:
            return False
        if "authorization" not in request.headers:
            return False
        return "Bearer " in request.headers["authorization"]


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[misc]
    async def hello(
        self,
        info: Info[GraphqlContext[MyService], None],
    ) -> str:
        return "Hello World"


class MyService(Service[ServiceSettings], GraphqlExtension):
    __graphql_schema__: ClassVar = strawberry.Schema(query=Query)


if __name__ == "__main__":
    MyService.cli()

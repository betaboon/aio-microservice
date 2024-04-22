from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Generic

from strawberry.litestar import BaseContext, make_graphql_controller
from strawberry.printer import print_schema

from aio_microservice import http
from aio_microservice.core.abc import (
    CommonABC,
    CommonABCT,
    ExtensionABC,
    startup_message,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable

    from graphql import ExecutionResult as GraphQLExecutionResult
    from strawberry import Schema
    from strawberry.types import ExecutionResult
    from strawberry.types.graphql import OperationType


class GraphqlContext(Generic[CommonABCT], BaseContext):
    service: CommonABCT


class _SchemaWrapper:
    def __init__(self, service: GraphqlExtension) -> None:
        self._service = service
        self._schema = service.__graphql_schema__

    async def execute(
        self,
        query: str | None,
        variable_values: dict[str, Any] | None = None,
        context_value: BaseContext | None = None,
        root_value: Any | None = None,  # noqa: ANN401
        operation_name: str | None = None,
        allowed_operation_types: Iterable[OperationType] | None = None,
    ) -> ExecutionResult:
        wrapped_context_value: GraphqlContext[
            CommonABC
        ] = await self._service.graphql._context_getter()
        if context_value is not None:
            wrapped_context_value.request = context_value.request
            wrapped_context_value.websocket = context_value.websocket
            wrapped_context_value.response = context_value.response
        return await self._schema.execute(
            query=query,
            variable_values=variable_values,
            context_value=wrapped_context_value,
            root_value=root_value,
            operation_name=operation_name,
            allowed_operation_types=allowed_operation_types,
        )

    async def subscribe(
        self,
        query: str,
        variable_values: dict[str, Any] | None = None,
        context_value: BaseContext | None = None,
        root_value: Any | None = None,  # noqa: ANN401
        operation_name: str | None = None,
    ) -> AsyncIterator[GraphQLExecutionResult] | GraphQLExecutionResult:
        wrapped_context_value: GraphqlContext[
            CommonABC
        ] = await self._service.graphql._context_getter()
        if context_value is not None:
            wrapped_context_value.request = context_value.request
            wrapped_context_value.websocket = context_value.websocket
            wrapped_context_value.response = context_value.response
        return await self._schema.subscribe(
            query=query,
            variable_values=variable_values,
            context_value=wrapped_context_value,
            root_value=root_value,
            operation_name=operation_name,
        )


class GraphqlImpl:
    def __init__(self, service: GraphqlExtension) -> None:
        self._service = service
        self._graphql_controller = make_graphql_controller(
            schema=service.__graphql_schema__,
            path="/graphql",
            context_getter=self._context_getter,
        )

    async def _context_getter(self) -> GraphqlContext[CommonABCT]:
        return GraphqlContext(service=self._service)  # type: ignore

    @property
    def schema(self) -> _SchemaWrapper:
        return _SchemaWrapper(service=self._service)


class GraphqlExtension(ExtensionABC):
    __graphql_schema__: ClassVar[Schema]

    def __init__(self) -> None:
        self.graphql = GraphqlImpl(service=self)
        self.register_http_controller(self.graphql._graphql_controller)

    @startup_message
    async def _graphql_startup_message(self) -> str:
        return """
            # Graphql

            The following http-endpoints are available:
            - {scheme}://{host}:{port}/graphql
            - {scheme}://{host}:{port}/schema/graphql.graphql
        """

    @http.get(path="schema/graphql.graphql", include_in_schema=False)
    async def _graphql_get_schema(self) -> str:
        return print_schema(self.__graphql_schema__)

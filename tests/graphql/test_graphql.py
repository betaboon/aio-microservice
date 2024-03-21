from __future__ import annotations

import strawberry

from aio_microservice import Service, ServiceSettings, http
from aio_microservice.graphql import GraphqlExtension
from aio_microservice.http import TestHttpClient


async def test_graphql_schema_download() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        async def test(self) -> str:
            return "TEST RESPONSE"

    class TestService(Service[ServiceSettings], GraphqlExtension):
        __graphql_schema__ = strawberry.Schema(query=Query)

    service = TestService()
    async with TestHttpClient(service=service) as http_client:
        response = await http_client.get("/schema/graphql.graphql")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert "test: String!" in response.text

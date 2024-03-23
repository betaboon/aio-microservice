from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import strawberry

from aio_microservice import Service, ServiceSettings, http
from aio_microservice.graphql import GraphqlExtension
from aio_microservice.http import TestHttpClient

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


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


def test_graphql_schema_export(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        async def test(self) -> str:
            return "TEST RESPONSE"

    class TestService(Service[ServiceSettings], GraphqlExtension):
        __graphql_schema__ = strawberry.Schema(query=Query)

    mocker.patch.dict("os.environ", {"NO_COLOR": "1", "TERM": "dumb"})
    mocker.patch("sys.argv", ["test-service", "schema", "graphql"])

    with pytest.raises(SystemExit):
        TestService.cli()

    captured = capsys.readouterr()
    assert captured.out == "type Query {\n  test: String!\n}\n"

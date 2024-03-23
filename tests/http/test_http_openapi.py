import pathlib

import pytest
from pytest_mock import MockerFixture

from aio_microservice import Service, ServiceSettings, http
from aio_microservice.http import TestHttpClient


async def test_http_openapi_swagger_ui() -> None:
    class TestService(Service[ServiceSettings]):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/schema/openapi")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert "/test" in response.text


async def test_http_openapi_schema_download_json() -> None:
    class TestService(Service[ServiceSettings]):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/schema/openapi.json")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert "/test" in response.json()["paths"]


async def test_http_openapi_schema_download_yaml() -> None:
    class TestService(Service[ServiceSettings]):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/schema/openapi.yaml")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert "/test" in response.text


def test_http_openapi_schema_export_json(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    class TestService(Service[ServiceSettings]):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    mocker.patch.dict("os.environ", {"NO_COLOR": "1", "TERM": "dumb"})
    mocker.patch("sys.argv", ["test-service", "schema", "openapi", "--format", "json"])

    with pytest.raises(SystemExit):
        TestService.cli()

    captured = capsys.readouterr()
    assert "/test" in captured.out


def test_http_openapi_schema_export_with_output_json(
    tmp_path: pathlib.Path,
    mocker: MockerFixture,
) -> None:
    class TestService(Service[ServiceSettings]):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    output_file = tmp_path / "openapi.json"

    mocker.patch(
        "sys.argv",
        [
            "test-service",
            "schema",
            "openapi",
            "--format",
            "json",
            "--output",
            output_file,
        ],
    )

    with pytest.raises(SystemExit):
        TestService.cli()

    written_schema = output_file.read_text()
    assert "/test" in written_schema


def test_http_openapi_schema_export_yaml(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    class TestService(Service[ServiceSettings]):
        @http.get(path="/test")
        async def get_test(self) -> str:
            return "TEST"

    mocker.patch.dict("os.environ", {"NO_COLOR": "1", "TERM": "dumb"})
    mocker.patch("sys.argv", ["test-service", "schema", "openapi", "--format", "yaml"])

    with pytest.raises(SystemExit):
        TestService.cli()

    captured = capsys.readouterr()
    assert "/test" in captured.out


async def test_http_openapi_service_description() -> None:
    class TestService(Service[ServiceSettings]):
        __description__ = "TEST SERVICE DESCRIPTION"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/schema/openapi.json")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert response.json()["info"]["description"] == TestService.__description__


async def test_http_openapi_service_version() -> None:
    class TestService(Service[ServiceSettings]):
        __version__ = "1.2.3"

    service = TestService()
    async with TestHttpClient(service=service) as client:
        response = await client.get("/schema/openapi.json")
        assert response.status_code == http.status_codes.HTTP_200_OK
        assert response.json()["info"]["version"] == TestService.__version__

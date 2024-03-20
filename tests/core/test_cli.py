import multiprocessing
import re

import httpx
import pytest
from pydantic import Field
from pytest_mock import MockerFixture

from aio_microservice import (
    Service,
    ServiceSettings,
    http,
)


def test_cli_help(capsys: pytest.CaptureFixture[str], mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings]): ...

    mocker.patch.dict("os.environ", {"NO_COLOR": "1", "TERM": "dumb"})
    mocker.patch("sys.argv", ["test-service", "--help"])

    with pytest.raises(SystemExit):
        TestService.cli()

    captured = capsys.readouterr()
    assert "Usage: test-service [OPTIONS]" in captured.out


def test_cli_help_custom_settings(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    class TestSettings(ServiceSettings):
        test_value: str = Field(default="TEST", description="TEST DESCRIPTION")

    class TestService(Service[TestSettings]): ...

    mocker.patch.dict("os.environ", {"NO_COLOR": "1", "TERM": "dumb"})
    mocker.patch("sys.argv", ["test-service", "run", "--help"])

    with pytest.raises(SystemExit):
        TestService.cli()

    captured = capsys.readouterr()
    assert "Usage: test-service run [OPTIONS]" in captured.out
    matches = re.findall(r"--test-value\s+TEXT\s+TEST DESCRIPTION", captured.out)
    assert len(matches) == 1, "custom setting not found in help text"


def test_cli_help_service_description(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    class TestService(Service[ServiceSettings]):
        __description__ = "TEST SERVICE DESCRIPTION"

    mocker.patch.dict("os.environ", {"NO_COLOR": "1", "TERM": "dumb"})
    mocker.patch("sys.argv", ["test-service", "--help"])

    with pytest.raises(SystemExit):
        TestService.cli()

    captured = capsys.readouterr()
    assert "Usage: test-service [OPTIONS]" in captured.out
    assert "TEST SERVICE DESCRIPTION" in captured.out


def test_cli_help_service_version(
    capsys: pytest.CaptureFixture[str],
    mocker: MockerFixture,
) -> None:
    class TestService(Service[ServiceSettings]):
        __version__ = "1.2.3"

    mocker.patch.dict("os.environ", {"NO_COLOR": "1", "TERM": "dumb"})
    mocker.patch("sys.argv", ["test-service", "version"])

    with pytest.raises(SystemExit):
        TestService.cli()

    captured = capsys.readouterr()
    assert captured.out == "1.2.3\n"


def test_cli_run(mocker: MockerFixture) -> None:
    class TestService(Service[ServiceSettings]): ...

    mocker.patch.dict("os.environ", {"NO_COLOR": "1", "TERM": "dumb"})
    mocker.patch("sys.argv", ["test-service", "run", "--http-port=1234"])
    p = multiprocessing.Process(target=TestService.cli)
    p.start()

    transport = httpx.HTTPTransport(retries=5)
    client = httpx.Client(transport=transport)

    response = client.get("http://localhost:1234/readiness")
    assert response.status_code == http.status_codes.HTTP_200_OK

    p.terminate()
    p.join()

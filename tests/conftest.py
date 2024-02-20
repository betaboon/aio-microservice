from collections.abc import Iterator

import pytest
from _pytest.logging import LogCaptureFixture
from loguru import logger


# adopted from: https://loguru.readthedocs.io/en/stable/resources/migration.html#replacing-caplog-fixture-from-pytest-library
@pytest.fixture()
def caplog(caplog: LogCaptureFixture) -> Iterator[LogCaptureFixture]:
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=True,  # Set to 'True' if your test is spawning child processes.
    )
    yield caplog
    logger.remove(handler_id)

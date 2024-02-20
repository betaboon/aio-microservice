from __future__ import annotations

import inspect
import logging

from loguru import logger as loguru_logger


class InterceptHandler(logging.Handler):
    """Default handler from examples in loguru documentation.

    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Outputs the record through loguru.

        Args:
            record: The logging record.
        """
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:  # pragma: no cover
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _get_intercepting_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers = [InterceptHandler()]
    logger.propagate = False
    return logger


def _setup_warnings_logging() -> None:
    logging.captureWarnings(True)
    _get_intercepting_logger("py.warnings")


def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging through loguru.

    This tries its best to force all logs through loguru.
    To achieve this an InterceptionHandler is registered.

    Further warnings will be forced into loguru.

    Args:
        level: The loglevel to apply to the root logger.
    """
    logging.basicConfig(handlers=[InterceptHandler()], level=level)

    # reconfigure existing loggers
    for name in logging.root.manager.loggerDict:
        _get_intercepting_logger(name)

    _setup_warnings_logging()

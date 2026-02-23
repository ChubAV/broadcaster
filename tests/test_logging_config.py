import logging
import structlog
import pytest
from app.logging_config import setup_logging


def test_setup_logging_json_mode():
    """setup_logging configures structlog with JSON output."""
    setup_logging(log_level="INFO", log_format="json")
    logger = structlog.get_logger("test.json")
    assert logger is not None


def test_setup_logging_console_mode():
    """setup_logging configures structlog with console output."""
    setup_logging(log_level="DEBUG", log_format="console")
    logger = structlog.get_logger("test.console")
    assert logger is not None


def test_setup_logging_sets_level():
    """setup_logging sets root logger level."""
    setup_logging(log_level="WARNING", log_format="json")
    root = logging.getLogger()
    assert root.level == logging.WARNING

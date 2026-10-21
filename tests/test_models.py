from datetime import datetime
from typing import Any

import pytest

from streamstats.errors import (
    InvalidEventError,
    InvalidTimestampError,
    StreamStatsError,
)
from streamstats.models import Event


@pytest.mark.parametrize(
    ("timestamp", "level", "source", "message"),
    [
        ("2026-10-01T08:00:00.123Z", "ERROR", "вчера", "test1"),
        ("2026-02-28T00:00:00Z", "WARNING", "test", "test2"),
        ("2026-10-01T08:00:00+03:00", "INFO", "qqq", "test3"),
        ("2026-10-01T08:00:00Z", "DEBUG", "test", "test4"),
        ("2026-10-01T08:00:00Z", "CRITICAL", "test", "test5"),
    ]
)
def test_positive_model(timestamp: str, level: str, source: str, message: str):
    event = Event(timestamp, level, source, message)

    assert event.message == message
    assert event.level == level
    assert event.source == source
    assert event.timestamp == datetime.fromisoformat(timestamp)
    assert isinstance(event.timestamp, datetime)
    assert event.timestamp.tzinfo is not None


@pytest.mark.parametrize(
    ("timestamp", "level", "source", "message", "error_class", "error_code"),
    [
        ("вчера", "INFO", "test", "msg", InvalidTimestampError, "invalid_timestamp"),
        ("2026-02-30T00:00:00Z", "INFO", "test", "msg", InvalidTimestampError, "invalid_timestamp"),
        (123, "INFO", "test", "msg", InvalidTimestampError, "invalid_timestamp"),
        (None, "INFO", "test", "msg", InvalidTimestampError, "invalid_timestamp"),
        ("2026-10-01T08:00:00", "INFO", "test", "msg", InvalidTimestampError, "invalid_timezone"),
        ("2026-10-01T08:00:00Z", "info", "test", "msg", InvalidEventError, "unsupported_level"),
        ("2026-10-01T08:00:00Z", "FATAL", "test", "msg", InvalidEventError, "unsupported_level"),
        ("2026-10-01T08:00:00Z", 3, "test", "msg", InvalidEventError, "invalid_type"),
        ("2026-10-01T08:00:00Z", "INFO", "", "msg", InvalidEventError, "empty_source"),
        ("2026-10-01T08:00:00Z", "INFO", "   ", "msg", InvalidEventError, "empty_source"),
        ("2026-10-01T08:00:00Z", "INFO", None, "msg", InvalidEventError, "invalid_type"),
        ("2026-10-01T08:00:00Z", "INFO", "test", ["a"], InvalidEventError, "invalid_type"),
        ("2026-10-01T08:00:00Z", "INFO", "test", None, InvalidEventError, "invalid_type"),
    ],
)
def test_negative_model(timestamp: Any, level: Any, source: Any, message: Any,
                        error_class: Any, error_code: Any):
    with pytest.raises(StreamStatsError) as exc_info:
        Event(timestamp, level, source, message)
    assert exc_info.value.error_code == error_code
    assert isinstance(exc_info.value, error_class)

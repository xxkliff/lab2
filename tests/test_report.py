import json
from pathlib import Path

import pytest

from streamstats.errors import CliConfigurationError
from streamstats.analysis import Analysis, ParseStats, analyze
from streamstats.models import Event
from streamstats.report import build_report, save_report


EMPTY_REPORT = {
        "total_events": 0,
        "by_level": {},
        "by_source": {},
        "top_error_sources": [],
        "first_timestamp": None,
        "last_timestamp": None,
        "skipped_invalid": 0,
    }

EVENTS = [
    Event("2026-10-01T10:00:00Z", "INFO", "auth", "logged in"),
    Event("2026-10-01T08:00:00+03:00", "ERROR", "db", "timeout"),
    Event("2026-10-01T12:00:00Z", "DEBUG", "cache", ""),
    Event("2026-10-01T09:00:00Z", "ERROR", "db", ""),
    Event("2026-10-01T09:05:00Z", "ERROR", "db", "test"),
    Event("2026-10-01T09:10:00Z", "CRITICAL", "payments", "test"),
    Event("2026-10-01T09:11:00Z", "ERROR", "payments", "test"),
    Event("2026-10-01T09:20:00Z", "ERROR", "api", "тест, тест"),
    Event("2026-10-01T09:21:00Z", "ERROR", "api", "502"),
    Event("2026-10-01T09:30:00Z", "CRITICAL", "cache", "test"),
    Event("2026-10-01T09:40:00Z", "ERROR", "queue", "qqqq"),
    Event("2026-10-01T09:50:00Z", "ERROR", "test", ""),
    Event("2026-10-01T09:55:00Z", "CRITICAL", "test", "test"),
    Event("2026-10-01T10:30:00Z", "WARNING", "auth", "password"),
]


def test_report():
    report = build_report(analyze(EVENTS), ParseStats())

    assert report == {
        "total_events": 14,
        "by_level": {"INFO": 1, "ERROR": 8, "DEBUG": 1, "CRITICAL": 3, "WARNING": 1},
        "by_source": {"auth": 2, "db": 3, "cache": 2, "payments": 2, "api": 2, "queue": 1, "test": 2},
        "top_error_sources": [ {"source": "db", "count": 3},
                               {"source": "api", "count": 2},
                               {"source": "payments", "count": 2},
                               {"source": "test", "count": 2},
                               {"source": "cache", "count": 1},
        ],
        "first_timestamp": "2026-10-01T08:00:00+03:00",
        "last_timestamp": "2026-10-01T12:00:00+00:00",
        "skipped_invalid": 0,
    }


def test_report_skipped_invalid():
    report = build_report(Analysis(), ParseStats(skipped_invalid=3))

    assert report["skipped_invalid"] == 3


def test_empty_report():
    report = build_report(Analysis(), ParseStats())

    assert report == EMPTY_REPORT


def test_write_report(tmp_path: Path):
    report = build_report(Analysis(), ParseStats())
    save_report(report, tmp_path / "report.json")

    with open(tmp_path / "report.json", "r") as f:
        report = json.loads(f.read())

    assert report == EMPTY_REPORT


def test_invalid_directory(tmp_path: Path):
    path = tmp_path / "invalid/report.json"

    with pytest.raises(CliConfigurationError) as exc_info:
        save_report(build_report(Analysis(), ParseStats()), path)

    assert exc_info.value.error_code == "directory_not_found"
    assert exc_info.value.path == path.parent

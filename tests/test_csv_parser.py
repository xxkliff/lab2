import logging

import pytest

from pathlib import Path

from streamstats.errors import StreamStatsError, CliConfigurationError
from streamstats.models import ParseStats
from streamstats.parsers import parse_csv

HEADER = "timestamp,level,source,message\n"
INVALID_HEADER = "level,source,message,test\n"


def write_csv(tmp_path: Path, header: str, body: str, name: str = "events.csv",) -> Path:
    file = tmp_path / name
    file.write_text(header + body, encoding="utf-8")
    return file


def test_parse_positive(tmp_path: Path):
    file = write_csv(
        tmp_path,
        HEADER,
        '2026-10-01T08:00:00Z,INFO,auth,logged in\n'
        '2026-10-01T08:00:05Z,ERROR,db,timeout\n'
        '2026-10-01T08:01:10+03:00,WARNING,auth,неправильный пароль\n'
        '2026-10-01T08:02:00.250Z,ERROR,db,failed\n'
        '2026-10-01T08:03:30Z,CRITICAL,payments,unavailable\n'
        '2026-10-01T08:04:00Z,DEBUG,cache,\n',
    )

    events = list(parse_csv(file))

    assert len(events) == 6
    assert events[0].message == "logged in"
    assert events[1].level == "ERROR"
    assert events[5].message == ""


@pytest.mark.parametrize(
    ("row", "error_code"),
    [
        ("вчера,INFO,a,m", "invalid_timestamp"),
        ("2026-10-01T08:00:00,INFO,a,m", "invalid_timezone"),
        ("2026-10-01T08:00:00Z,FATAL,a,m", "unsupported_level"),
        ("2026-10-01T08:00:00Z,info,a,m", "unsupported_level"),
        ("2026-10-01T08:00:00Z,INFO,,m", "empty_source"),
        ("2026-10-01T08:00:00Z,INFO,   ,m", "empty_source"),
        ("2026-10-01T08:00:00Z,", "value_missing"),
    ],
)
def test_parse_invalid_line(tmp_path: Path, row: str, error_code: str):
    file = write_csv(tmp_path, HEADER, row + "\n")

    with pytest.raises(StreamStatsError) as exc_info:
        list(parse_csv(file))

    assert exc_info.value.error_code == error_code
    assert exc_info.value.line == 2
    assert exc_info.value.path == file


def test_error_line_number(tmp_path: Path):
    file = write_csv(
        tmp_path,
        HEADER,
        '2026-10-01T08:00:00Z,INFO,a,m\n'
        '2026-10-01T08:00:01Z,INFO,a,m\n'
        '2026-10-01T08:00:02Z,FATAL,a,m\n',
    )

    with pytest.raises(StreamStatsError) as exc_info:
        list(parse_csv(file))

    assert exc_info.value.line == 4
    assert "строка 4" in str(exc_info.value)


def test_parse_skip_invalid(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    file = write_csv(
        tmp_path,
        HEADER,
        '2026-10-01T08:00:00Z,INFO,auth,logged in\n'
        '2026-10-01T08:00:01Z,FATAL,auth,test\n'
        'вчера,INFO,auth,test2\n',
    )
    stats = ParseStats()

    with caplog.at_level(logging.WARNING):
        events = list(parse_csv(file, skip_invalid=True, parse_stats=stats))

    assert len(events) == 1
    assert len(caplog.records) == 2
    assert "строка 3" in caplog.text
    assert "строка 4" in caplog.text
    assert stats.skipped_invalid == 2


def test_extra_column(tmp_path: Path):
    file = tmp_path / "extra_column.csv"
    file.write_text(
        "timestamp,level,source,message,host\n"
        "2026-10-01T08:00:00Z,INFO,auth,logged in,testtt\n",
        encoding="utf-8",
    )

    events = list(parse_csv(file))

    assert len(events) == 1
    assert events[0].source == "auth"


def test_cyrillic(tmp_path: Path):
    file = write_csv(tmp_path, HEADER,"2026-10-01T08:00:00Z,INFO,тест1,тест2\n")

    event = list(parse_csv(file))[0]

    assert event.source == "тест1"
    assert event.message == "тест2"


def test_file_not_found(tmp_path: Path):
    file = tmp_path / "missing.csv"

    with pytest.raises(CliConfigurationError) as exc_info:
        list(parse_csv(file))

    assert exc_info.value.error_code == "file_not_found"


def test_parse_empty(tmp_path: Path):
    file = tmp_path / "empty.csv"
    file.touch()

    assert list(parse_csv(file)) == []


def test_comma(tmp_path: Path):
    file = write_csv(tmp_path, HEADER, '2026-10-01T08:00:00Z,INFO,auth,"слабый пароль, повторите"\n')
    event = list(parse_csv(file))[0]

    assert event.source == "auth"
    assert event.message == "слабый пароль, повторите"


@pytest.mark.parametrize(
    "skip_invalid",
    [True, False],
)
def test_invalid_header(tmp_path: Path, skip_invalid: bool):
    file = write_csv(tmp_path, INVALID_HEADER, '2026-10-01T08:00:05Z,ERROR,db,timeout\n')

    with pytest.raises(StreamStatsError) as exc_info:
        list(parse_csv(file, skip_invalid=skip_invalid))

    assert exc_info.value.line == 1
    assert exc_info.value.error_code == "invalid_header"


def test_empty_header(tmp_path: Path):
    file = write_csv(tmp_path, HEADER, "")
    event = list(parse_csv(file))

    assert event == []

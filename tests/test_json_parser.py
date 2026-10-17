from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from streamstats.errors import CliConfigurationError, StreamStatsError
from streamstats.analysis import ParseStats
from streamstats.parsers import parse_jsonl


def test_parse_positive(tmp_path: Path):
    file = tmp_path / "positive_events.jsonl"
    file.write_text(
        '{"timestamp": "2026-10-01T08:00:00Z", "level": "INFO", "source": "auth", "message": "user logged"}\n'
        '{"timestamp": "2026-10-01T08:00:05Z", "level": "ERROR", "source": "db", "message": "timeout"}\n'
        '{"timestamp": "2026-10-01T08:01:10+03:00", "level": "WARNING", "source": "auth", "message": "test"}\n'
        '{"timestamp": "2026-10-01T08:02:00.250Z", "level": "ERROR", "source": "db", "message": "failed"}\n'
        '{"timestamp": "2026-10-01T08:03:30Z", "level": "CRITICAL", "source": "payments", "message": "test"}\n'
        '{"timestamp": "2026-10-01T08:04:00Z", "level": "DEBUG", "source": "cache", "message": "", "host": "hello"}\n',
        encoding='utf-8')

    events = list(parse_jsonl(file))

    assert len(events) == 6
    assert events[0].message == "user logged"
    assert events[1].level == "ERROR"


@pytest.mark.parametrize(
    ("content", "error_code"),
    [
        ('{"timestamp": "2026-10-01T08:00:00Z", "level": "INFO"', "json_decode_error"),
        ('\n', "json_decode_error"),
        ('[1, 2, 3]', "invalid_object"),
        ('{"timestamp": "2026-10-01T08:00:00Z", "level": "INFO", "source": "a"}', "missing_key"),
        ('{"timestamp": "2026-10-01T08:00:00Z", "level": "FATAL", "source": "a", "message": "m"}', "unsupported_level"),
        ('{"timestamp": "2026-10-01T08:00:00Z", "level": 3, "source": "a", "message": "m"}', "invalid_type"),
        ('{"timestamp": "2026-10-01T08:00:00Z", "level": "INFO", "source": "", "message": "m"}', "empty_source"),
        ('{"timestamp": "2026-10-01T08:00:00Z", "level": "INFO", "source": "a", "message": null}', "invalid_type"),
        ('{"timestamp": "вчера", "level": "INFO", "source": "a", "message": "m"}', "invalid_timestamp"),
        ('{"timestamp": "2026-10-01T08:00:00", "level": "INFO", "source": "a", "message": "m"}', "invalid_timezone"),
    ],
)
def test_parse_invalid_line(tmp_path: Path, content: str, error_code: str):
    file = tmp_path / "bad.jsonl"
    file.write_text(content + "\n", encoding="utf-8")

    with pytest.raises(StreamStatsError) as exc_info:
        list(parse_jsonl(file))

    assert exc_info.value.error_code == error_code
    assert exc_info.value.line == 1


def test_parse_skip_invalid(tmp_path: Path, caplog: LogCaptureFixture):
    file = tmp_path / "bad.jsonl"
    file.write_text(
        '{"timestamp": "2026-10-01T08:00:00Z", "level": "INFO", "source": "auth", "message": "user logged"}\n'
        '{"timestamp": "2026-10-01T08:00:00Z", "level": "INFO", "source": "a"}\n'
        '[1, 2, 3]\n',
        encoding='utf-8')

    parse_stats = ParseStats()
    events = list(parse_jsonl(file, skip_invalid=True, parse_stats=parse_stats))

    assert len(events) == 1
    assert 'строка 2' in caplog.text
    assert parse_stats.skipped_invalid == 2



def test_extra_key(tmp_path: Path):
    file = tmp_path / "empty.jsonl"
    file.write_text(
        '{"timestamp": "2026-10-01T08:00:00Z", "level": "INFO", "source": "auth", "message": "user logged", "key": 1234}\n',
        encoding='utf-8')

    assert len(list(parse_jsonl(file))) == 1


def test_cyrillic(tmp_path: Path):
    file = tmp_path / "cyrillic.jsonl"
    file.write_text(
        '{"timestamp": "2026-10-01T08:00:00Z", "level": "INFO", "source": "тест1", "message": "тест2"}\n',
        encoding='utf-8')

    event = next(iter(parse_jsonl(file)))

    assert event.source == 'тест1'
    assert event.message == 'тест2'


def test_file_not_found(tmp_path: Path):
    file = tmp_path / "test.jsonl"

    with pytest.raises(CliConfigurationError) as exc_info:
        list(parse_jsonl(file))

    assert exc_info.value.error_code == "file_not_found"


def test_parse_empty(tmp_path: Path):
    file = tmp_path / "empty.jsonl"
    file.touch()

    assert list(parse_jsonl(file)) == []

from datetime import UTC, datetime

from streamstats.analysis import analyze
from streamstats.models import Event


def make_event(level: str = "INFO",
               source: str = "auth", ts: str = "2026-10-01T08:00:00Z", message: str = "m") -> Event:
    return Event(ts, level, source, message)


def test_empty():
    analysis = analyze([])

    assert analysis.total_events == 0
    assert analysis.levels == {}
    assert analysis.sources == {}
    assert analysis.error_sources == {}
    assert analysis.first_timestamp is None
    assert analysis.last_timestamp is None


def test_event():
    event = make_event()
    analysis = analyze([event])

    assert analysis.total_events == 1
    assert analysis.levels == {"INFO": 1}
    assert analysis.sources == {"auth": 1}
    assert analysis.error_sources == {}
    assert analysis.first_timestamp == datetime.fromisoformat("2026-10-01T08:00:00Z")
    assert analysis.last_timestamp == datetime.fromisoformat("2026-10-01T08:00:00Z")


def test_counters():
    events = [
        make_event(level="INFO", source="auth"),
        make_event(level="INFO", source="auth"),
        make_event(level="ERROR", source="db"),
        make_event(level="DEBUG", source="db")
    ]
    analysis = analyze(events)

    assert analysis.total_events == 4
    assert analysis.levels == {"INFO": 2, "ERROR": 1, "DEBUG": 1}
    assert analysis.sources == {"auth": 2, "db": 2}
    assert analysis.error_sources == {"db": 1}


def test_errors():
    events = [
        make_event(level="WARNING", source="auth"),
        make_event(level="DEBUG", source="auth"),
        make_event(level="ERROR", source="db"),
        make_event(level="ERROR", source="db"),
        make_event(level="ERROR", source="qqq"),
        make_event(level="ERROR", source="qqqq"),
        make_event(level="ERROR", source="qqqqq"),
        make_event(level="ERROR", source="db"),
        make_event(level="CRITICAL", source="login")
    ]
    analysis = analyze(events)

    assert analysis.total_events == 9
    assert analysis.error_sources == {"db": 3, "login": 1, "qqq": 1, "qqqq": 1, "qqqqq": 1}
    assert analysis.top_error_sources(n=3) == [("db", 3), ("login", 1), ("qqq", 1)]


def test_min_max_timestamp():
    events = [
        make_event(ts="2026-10-01T06:00:00Z"),  # Раньше
        make_event(ts="2026-10-01T09:00:00Z"),  # Позже
    ]

    analysis = analyze(events)

    assert analysis.first_timestamp == datetime(2026, 10, 1, 6, 0, tzinfo=UTC)
    assert analysis.last_timestamp == datetime(2026, 10, 1, 9, 0, tzinfo=UTC)

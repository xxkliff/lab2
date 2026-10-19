import json
from pathlib import Path

import pytest

from streamstats.__main__ import main


LINES = (
    '{"timestamp": "2026-10-01T08:00:00Z", "level": "INFO", "source": "auth", "message": "ok"}\n'
    '{"timestamp": "2026-10-01T08:00:05Z", "level": "ERROR", "source": "db", "message": "nook"}\n'
)


def test_cli_positive(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / 'test.jsonl'
    path.write_text(LINES, encoding='utf-8')
    report_path = tmp_path / 'report.json'

    code = main(["analyze", str(path), "--format", "jsonl", "--output", str(report_path)])
    out, err = capsys.readouterr()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert code == 0
    assert out == ""
    assert err == ""
    assert report["total_events"] == 2
    assert report["by_level"] == {"INFO": 1, "ERROR": 1}
    assert report["skipped_invalid"] == 0


def test_cli_negative(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["analyze", "no_exist.json", "--format", "jsonl", "--output", "no_exist.json"])
    out, err = capsys.readouterr()

    assert code == 2
    assert out == ""
    assert "Ошибка" in err


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert "analyze" in capsys.readouterr().out

import json
from pathlib import Path

from streamstats.analysis import Analysis, ParseStats
from streamstats.decorators import file_errors


def build_report(analysis: Analysis, parse_stats: ParseStats, top_n: int = 5) -> dict:
    first_timestamp = None
    last_timestamp = None

    if analysis.first_timestamp is not None: first_timestamp = analysis.first_timestamp.isoformat()
    if analysis.last_timestamp is not None: last_timestamp = analysis.last_timestamp.isoformat()

    return {
        "total_events": analysis.total_events,
        "by_level": dict(analysis.levels),
        "by_source": dict(analysis.sources),
        "top_error_sources": [
            {"source": source, "count": count}
            for source, count in analysis.top_error_sources(n=top_n)
        ],
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "skipped_invalid": parse_stats.skipped_invalid,
    }


@file_errors
def save_report(report: dict, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4, sort_keys=False)

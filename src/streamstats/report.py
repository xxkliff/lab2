import json
from pathlib import Path

from streamstats.analysis import Analysis, ParseStats
from streamstats.decorators import file_errors


@file_errors
def save_report(analyse: Analysis, parse_stats: ParseStats, path: Path, top_error_sources_count: int = 5):
    top_error_sources = [{"source": source[0], "count": source[1]}
                         for source in analyse.top_error_sources(n=top_error_sources_count)]

    first_timestamp = None
    last_timestamp = None

    if analyse.first_timestamp is not None:  first_timestamp = analyse.first_timestamp.isoformat()
    if analyse.last_timestamp is not None:  last_timestamp = analyse.last_timestamp.isoformat()

    report = {
        "total_events":  analyse.total_events,
        "by_level": dict(analyse.levels),
        "by_source": dict(analyse.sources),
        "top_error_sources": top_error_sources,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "skipped_invalid": parse_stats.skipped_invalid,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4, sort_keys=False)

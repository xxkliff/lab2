import json
from pathlib import Path

from streamstats.analysis import Analysis, ParseStats
from streamstats.decorators import file_errors


@file_errors
def save_report(analise: Analysis, parse_stats: ParseStats, path: Path, top_error_sources_count: int = 5):
    top_error_sources = [{"source": source[0], "count": source[1]}
                         for source in analise.top_error_sources(n=top_error_sources_count)]

    report = {
        "total_events":  analise.total_events,
        "by_level": dict(analise.levels),
        "by_source": dict(analise.sources),
        "top_error_sources": top_error_sources,
        "first_timestamp": analise.first_timestamp.isoformat(),
        "last_timestamp": analise.last_timestamp.isoformat(),
        "skipped_invalid": parse_stats.skipped_invalid,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4, sort_keys=False)

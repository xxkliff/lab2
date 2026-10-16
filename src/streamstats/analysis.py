from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from streamstats.constants import ERROR_LEVELS
from streamstats.models import Event


@dataclass
class ParseStats:
    skipped_invalid: int = 0


@dataclass
class Analysis:
    total_events: int = 0
    levels: Counter[str] = field(default_factory=Counter)
    sources: Counter[str] = field(default_factory=Counter)
    error_sources: Counter[str] = field(default_factory=Counter)
    first_timestamp: datetime | None = None
    last_timestamp: datetime | None = None

    def add(self, event: Event):
        self.total_events += 1
        self.levels[event.level] += 1
        self.sources[event.source] += 1

        if event.level in ERROR_LEVELS:
            self.error_sources[event.source] += 1

        if self.first_timestamp is None or event.timestamp < self.first_timestamp:
            self.first_timestamp = event.timestamp

        if self.last_timestamp is None or event.timestamp > self.last_timestamp:
            self.last_timestamp = event.timestamp

    def top_error_sources(self, n: int = 5) -> list[tuple[str, int]]:
        return sorted(self.error_sources.items(), key=lambda item: (-item[1], item[0]))[:n]


def analyze(events: Iterable[Event]) -> Analysis:
    analysis = Analysis()
    for event in events:
        analysis.add(event)
    return analysis

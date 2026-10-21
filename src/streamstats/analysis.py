from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import cast

from streamstats.constants import ERROR_LEVELS
from streamstats.models import Event


@dataclass
class ParseStats:
    """
    Статистика разбора файлов, общая для всех входных файлов

    skipped_invalid - количество строк, пропущенных в режиме --skip-invalid
    """
    skipped_invalid: int = 0


@dataclass
class Analysis:
    """
    Статистика по событиям. Сами события не хранятся, только счётчики,
    поэтому память не зависит от числа строк
    """

    total_events: int = 0
    levels: Counter[str] = field(default_factory=Counter)
    sources: Counter[str] = field(default_factory=Counter)
    error_sources: Counter[str] = field(default_factory=Counter)
    first_timestamp: datetime | None = None
    last_timestamp: datetime | None = None

    def add(self, event: Event) -> None:
        """
        Обновляет счётчики по одному событию

        :param event: валидное событие
        """
        self.total_events += 1
        self.levels[event.level] += 1
        self.sources[event.source] += 1
        timestamp = cast(datetime, event.timestamp)

        if event.level in ERROR_LEVELS:
            self.error_sources[event.source] += 1

        if self.first_timestamp is None or timestamp < self.first_timestamp:
            self.first_timestamp = timestamp

        if self.last_timestamp is None or timestamp > self.last_timestamp:
            self.last_timestamp = timestamp

    def top_error_sources(self, n: int = 5) -> list[tuple[str, int]]:
        """
        Возвращает источники с наибольшим числом событий ERROR и CRITICAL

        При равном количестве источники сортируются по имени

        :param n: сколько источников вернуть
        :return: список пар, не длиннее n
        """
        return sorted(self.error_sources.items(), key=lambda item: (-item[1], item[0]))[:n]


def analyze(events: Iterable[Event]) -> Analysis:
    """
    Считает статистику по событиям, обрабатывая их по одному

    :param events: итерируемый объект событий, например генератор парсера
    :return: накопленная статистика
    """
    analysis = Analysis()
    for event in events:
        analysis.add(event)
    return analysis

import csv
import json
import logging
from collections.abc import Iterator
from pathlib import Path

from streamstats.analysis import ParseStats
from streamstats.decorators import file_errors_generator
from streamstats.errors import (
    InvalidEventError,
    InvalidTimestampError,
    StreamStatsError,
)
from streamstats.models import Event

logger = logging.getLogger(__name__)

def _parse_line(line: str) -> Event:
    """
    Разбирает одну строку JSONL в Event

    :param line: строка файла
    :return: событие Event
    :raises InvalidEventError: строка не является JSON объектом или событие невалидно
    :raises InvalidTimestampError: невалидный timestamp
    """
    try:
        json_line = json.loads(line)
    except json.JSONDecodeError as e:
        raise InvalidEventError(
            message="JSON объект не читается.",
            error_code="json_decode_error") from e

    if not isinstance(json_line, dict):
        raise InvalidEventError(message="Объект не dict.", error_code="invalid_object")

    return _build_event(json_line)


def _handle_invalid(e: StreamStatsError, path: Path, number: int, skip_invalid: bool, stats: ParseStats | None) -> None:
    """
    Обрабатывает невалидную строку в зависимости от режима

    Добавляет к ошибке путь и номер строки. Без skip_invalid пробрасывает ошибку дальше,
    со skip_invalid пишет WARNING в лог и увеличивает счётчик пропущенных строк

    :param e: ошибка валидации строки
    :param path: путь к файлу
    :param number: номер строки в файле
    :param skip_invalid: режим --skip-invalid
    :param stats: статистика разбора, может быть None
    :raises StreamStatsError: та же ошибка e, если skip_invalid выключен
    """
    e.path = path
    e.line = number
    if not skip_invalid:
        raise e
    logger.warning("%s", e)
    if stats is not None:
        stats.skipped_invalid += 1


def _build_event(raw: dict) -> Event:
    """
    Создаёт Event из словаря с полями строки

    :param raw: словарь из JSON объекта или строки CSV
    :return: событие Event
    :raises InvalidEventError: нет обязательного поля или событие невалидно
    :raises InvalidTimestampError: невалидный timestamp
    """
    try:
        timestamp = raw['timestamp']
        level = raw['level']
        source = raw['source']
        message = raw['message']
    except KeyError as e:
        raise InvalidEventError(message=F"Отсутствует ключ {e.args[0]}.",
                                error_code="missing_key") from e

    return Event(timestamp, level, source, message)


@file_errors_generator
def parse_jsonl(path: Path, skip_invalid: bool = False, parse_stats: ParseStats | None = None) -> Iterator[Event]:
    """
    Построчно читает файл JSONL и отдаёт события по одному

    :param path: путь к файлу
    :param skip_invalid: пропускать невалидные строки с предупреждением в лог
    :param parse_stats: статистика, в которую добавляется число пропущенных строк
    :return: генератор событий Event
    :raises InvalidEventError: невалидная строка без skip_invalid
    :raises InvalidTimestampError: невалидный timestamp без skip_invalid
    :raises CliConfigurationError: файл не найден, не UTF-8 или нет прав
    """
    with open(path, 'r', encoding='utf-8') as file:
        for number, line in enumerate(file, start=1):
            try:
                event = _parse_line(line)
            except (InvalidEventError, InvalidTimestampError) as e:
                _handle_invalid(e, path, number, skip_invalid, parse_stats)
                continue

            yield event


@file_errors_generator
def parse_csv(path: Path, skip_invalid: bool = False, parse_stats: ParseStats | None = None) -> Iterator[Event]:
    """
    Построчно читает файл CSV с заголовком и отдаёт события по одному

    Номер строки считается с учётом заголовка. Неверный заголовок считается ошибкой всего файла,
    она не пропускается даже со skip_invalid

    :param path: путь к файлу
    :param skip_invalid: пропускать невалидные строки с предупреждением в лог
    :param parse_stats: статистика, в которую добавляется число пропущенных строк
    :return: генератор событий Event
    :raises InvalidEventError: неверный заголовок или невалидная строка без skip_invalid
    :raises InvalidTimestampError: невалидный timestamp без skip_invalid
    :raises CliConfigurationError: файл не найден, не UTF-8 или нет прав
    """
    with open(path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            return

        required = {'timestamp', 'level', 'source', 'message'}
        missing = list(required - set(reader.fieldnames))

        if missing:
            raise InvalidEventError(message=f"В заголовке нет колонок: {', '.join(sorted(missing))}.",
                                    error_code="invalid_header", path=path, line=1)

        for row in reader:
            try:
                if None in row:
                    raise InvalidEventError(message="лишние значения в строке", error_code="extra_value",
                                            path=path, line=reader.line_num)
                if None in row.values():
                    raise InvalidEventError(message="не хватает значений в строке", error_code="value_missing",
                                            path=path, line=reader.line_num)

                event = _build_event(row)
            except (InvalidEventError, InvalidTimestampError) as e:
                _handle_invalid(e, path, reader.line_num, skip_invalid, parse_stats)
                continue

            yield event

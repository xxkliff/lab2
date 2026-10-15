
import inspect
import json
import logging
import csv

from functools import wraps
from pathlib import Path
from streamstats.models import Event, ParseStats
from streamstats.errors import InvalidEventError, InvalidTimestampError, CliConfigurationError
from streamstats.constants import PROJECT_DIR

logger = logging.getLogger(__name__)

def _parse_line(line: str) -> Event:
    try:
        json_line = json.loads(line)
    except json.JSONDecodeError as e:
        raise InvalidEventError(
            message=f"JSON объект не читается.",
            error_code="json_decode_error") from e

    if not isinstance(json_line, dict):
        raise InvalidEventError(message=f"Объект не dict.", error_code="invalid_object")

    return _build_event(json_line)


def _handle_invalid(e, path, number, skip_invalid, stats) -> None:
    e.path = path
    e.line = number
    if not skip_invalid:
        raise e
    logger.warning("%s", e)
    if stats is not None:
        stats.skipped_invalid += 1


def _build_event(raw: dict) -> Event:
    try:
        timestamp = raw['timestamp']
        level = raw['level']
        source = raw['source']
        message = raw['message']
    except KeyError as e:
        raise InvalidEventError(message=F"Отсутствует ключ {e.args[0]}.",
                                error_code="missing_key") from e

    return Event(timestamp, level, source, message)


def file_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        path = args[0] if args else kwargs.get('path', 'путь не определён')

        try:
            yield from func(*args, **kwargs)
        except FileNotFoundError as e:
            raise CliConfigurationError(message=f"Файл {path} не найден", error_code="file_not_found") from e
        except UnicodeDecodeError as e:
            raise CliConfigurationError(message=f"Файл {path} не в кодировке UTF-8", error_code="invalid_encoding") from e
        except OSError as e:
            raise CliConfigurationError(message=f"Нет прав на чтение файла {path} или путь неверный",
                                        error_code="permission_error") from e
    return wrapper


@file_errors
def parse_jsonl(path: Path, skip_invalid: bool = False, parse_stats: ParseStats | None = None):
    with open(path, 'r', encoding='utf-8') as file:
        for number, line in enumerate(file, start=1):
            try:
                event = _parse_line(line)
            except (InvalidEventError, InvalidTimestampError) as e:
                _handle_invalid(e, path, number, skip_invalid, parse_stats)
                continue

            yield event


@file_errors
def parse_csv(path: Path, skip_invalid: bool = False, parse_stats: ParseStats | None = None):
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
                    raise InvalidEventError(message=f"лишние значения в строке", error_code="extra_value",
                                            path=path, line=reader.line_num)
                if None in row.values():
                    raise InvalidEventError(message=f"не хватает значений в строке", error_code="value_missing",
                                            path=path, line=reader.line_num)

                event = _build_event(row)
            except (InvalidEventError, InvalidTimestampError) as e:
                _handle_invalid(e, path, reader.line_num, skip_invalid, parse_stats)
                continue

            yield event


import json
import logging

from pathlib import Path
from streamstats.models import Event, ParseStats
from streamstats.errors import InvalidEventError, InvalidTimestampError, CliConfigurationError

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

    try:
        timestamp = json_line['timestamp']
        level = json_line['level']
        source = json_line['source']
        message = json_line['message']
    except KeyError as e:
        raise InvalidEventError(message=F"Отсутствует ключ {e.args[0]}.",
                                error_code="missing_key") from e

    return Event(timestamp, level, source, message)


def parse_jsonl(path: Path, skip_invalid: bool = False, parse_stats: ParseStats | None = None):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            for number, line in enumerate(file, start=1):
                try:
                    event = _parse_line(line)
                except (InvalidEventError, InvalidTimestampError) as e:
                    e.path = path
                    e.line = number

                    if skip_invalid:
                        logger.warning("%s", e)
                        if parse_stats is not None:
                            parse_stats.skipped_invalid += 1
                        continue
                    else:
                        raise

                yield event
    except FileNotFoundError as e:
        raise CliConfigurationError(message=f"Файл {path} не найден", error_code="file_not_found") from e
    except UnicodeDecodeError as e:
        raise CliConfigurationError(message="JSON файл не в кодировке UTF-8", error_code="invalid_encoding") from e
    except OSError as e:
        raise CliConfigurationError(message=f"Нет прав на чтение файла {path} или путь неверный",
                                    error_code="permission_error") from e

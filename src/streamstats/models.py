from dataclasses import dataclass
from datetime import datetime

from .constants import LEVEL_TYPES
from .errors import InvalidEventError, InvalidTimestampError


@dataclass(frozen=True, slots=True)
class Event:
    """
    Одно событие из входного файла

    timestamp - ISO 8601 с часовым поясом, после создания всегда datetime
    level - один из LEVEL_TYPES
    source - непустая строка
    message - строка, может быть пустой
    """
    timestamp: str | datetime
    level: str
    source: str
    message: str

    def __post_init__(self) -> None:
        """
        Проверяет поля Event'а и переводит timestamp из строки в datetime

        :raises InvalidEventError: неверный тип поля, неизвестный уровень, пустой source
        :raises InvalidTimestampError: timestamp не в формате ISO 8601 или без часового пояса
        """
        only_str = {"level": self.level, "source": self.source, "message": self.message}

        # только строковые поля
        for key, value in only_str.items():
            if not isinstance(value, str):
                raise InvalidEventError(message=f"Значение {value} для {key} должно быть строковым",
                                        error_code="invalid_type")

        # проверка datetime
        try:
            if not isinstance(self.timestamp, datetime):
                new_timestamp = datetime.fromisoformat(self.timestamp)
            else:
                new_timestamp = self.timestamp
        except (ValueError, TypeError) as e:
            raise InvalidTimestampError(message=f"timestamp {self.timestamp} введен не в формате ISO 8601",
                                    error_code="invalid_timestamp") from e
        if new_timestamp.tzinfo is None:
            raise InvalidTimestampError(message=f"В timestamp {self.timestamp} не указан timezone",
                                        error_code="invalid_timezone")

        # проверки level
        if self.level not in LEVEL_TYPES:
            raise InvalidEventError(message=f"Неподдерживаемый уровень: {self.level}",
                                         error_code="unsupported_level")

        # проверки source
        if len(self.source.strip()) == 0:
            raise InvalidEventError(message=f"Строка source: {self.source} не может быть пустой",
                                    error_code="empty_source")

        object.__setattr__(self, "timestamp", new_timestamp)

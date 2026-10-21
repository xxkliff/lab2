from dataclasses import dataclass
from datetime import datetime

from .constants import LEVEL_TYPES
from .errors import InvalidEventError, InvalidTimestampError


@dataclass(frozen=True, slots=True)
class Event:
    timestamp: str | datetime
    level: str
    source: str
    message: str

    def __post_init__(self):
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

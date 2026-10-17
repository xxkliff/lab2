
from pathlib import Path


class StreamStatsError(Exception):
    def __init__(self, error_code, message, path: Path | str = "", line: int | None = None):
        super().__init__(message)
        self.path = path
        self.line = line
        self.message = message
        self.error_code = error_code

    def __str__(self):
        parts = []

        if self.line is not None:
            parts.append(f"(строка {self.line})")
        if self.path:
            parts.append(f"(путь {self.path})")
        parts.append(self.message)
        return " ".join(parts)


class UnsupportedFormatError(StreamStatsError):
    pass


class InvalidEventError(StreamStatsError):
    pass


class InvalidTimestampError(StreamStatsError):
    pass


class CliConfigurationError(StreamStatsError):
    pass

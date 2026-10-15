
from pathlib import Path

class StreamStatsError(Exception):
    def __init__(self, error_code, message, path: Path | str = "", line: int | None = None):
        super().__init__(message)
        self.path = path
        self.line = line
        self.message = message
        self.error_code = error_code

    def __str__(self):
        if self.path is not None and self.line is not None:
            return f"{self.path} строка {self.line}: {self.message}"
        return self.message


class UnsupportedFormatError(StreamStatsError):
    pass


class InvalidEventError(StreamStatsError):
    pass


class InvalidTimestampError(StreamStatsError):
    pass


class CliConfigurationError(StreamStatsError):
    pass

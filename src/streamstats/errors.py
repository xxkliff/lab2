from pathlib import Path


class StreamStatsError(Exception):
    """
    Базовая ошибка пакета streamstats

    Хранит код ошибки, сообщение и, если известно, путь к файлу и номер строки
    """
    def __init__(self, error_code: str, message: str, path: Path | str = "", line: int | None = None) -> None:
        """
        :param error_code: код ошибки для тестов и обработки
        :param message: сообщение для пользователя
        :param path: путь к файлу, в котором возникла ошибка
        :param line: номер строки в файле
        """
        super().__init__(message)
        self.path = path
        self.line = line
        self.message = message
        self.error_code = error_code

    def __str__(self) -> str:
        """
        :return: сообщение с номером строки и путём, если они известны
        """
        parts: list[str] = []

        if self.line is not None:
            parts.append(f"(строка {self.line})")
        if self.path:
            parts.append(f"(путь {self.path})")
        parts.append(self.message)
        return " ".join(parts)


class UnsupportedFormatError(StreamStatsError):
    """Неподдерживаемый формат входных файлов"""


class InvalidEventError(StreamStatsError):
    """Строка не является корректным событием"""


class InvalidTimestampError(StreamStatsError):
    """timestamp не в формате ISO 8601 или без часового пояса"""


class CliConfigurationError(StreamStatsError):
    """Ошибка CLI: файл не найден, нет прав, нет директории, неверная кодировка"""

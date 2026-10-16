from functools import wraps
from pathlib import Path
from typing import Callable

from streamstats.errors import CliConfigurationError


def handle_file_exception(e: Exception, path: Path | str):
    if isinstance(e, FileNotFoundError):
        raise CliConfigurationError(message=f"Файл {path} не найден", error_code="file_not_found") from e
    elif isinstance(e, UnicodeDecodeError):
        raise CliConfigurationError(message=f"Файл {path} не в кодировке UTF-8", error_code="invalid_encoding") from e
    elif isinstance(e, PermissionError):
        raise CliConfigurationError(f"Нет хватает прав для выполнения действий с {path}.",
                                    "permission_error") from e
    elif isinstance(e, OSError):
        raise CliConfigurationError(message=f"{path} Системная ошибка: {e}", error_code="os_error") from e
    raise e


def file_errors_generator(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        path = kwargs.get('path', 'путь не определён')

        try:
            yield from func(*args, **kwargs)
        except Exception as e:
            handle_file_exception(e, path)

    return wrapper


def file_errors(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        path = kwargs.get('path', 'путь не определён')

        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_file_exception(e, path)

    return wrapper
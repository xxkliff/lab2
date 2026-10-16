import inspect
from collections.abc import Callable
from functools import wraps
from pathlib import Path

from streamstats.errors import CliConfigurationError


def handle_file_exception(e: Exception, path: Path | str):
    if isinstance(e, FileNotFoundError):
        raise CliConfigurationError(message="Файл не найден", error_code="file_not_found", path=path) from e
    elif isinstance(e, UnicodeDecodeError):
        raise CliConfigurationError(message="Файл не в кодировке UTF-8", error_code="invalid_encoding", path=path) from e
    elif isinstance(e, PermissionError):
        raise CliConfigurationError(message="Не хватает прав для выполнения действий с файлом.",
                                    error_code="permission_error", path=path) from e
    elif isinstance(e, OSError):
        raise CliConfigurationError(message=f"Системная ошибка: {e}", error_code="os_error", path=path) from e
    raise e


def _find_path(func: Callable, *args, **kwargs):
    bound = inspect.signature(func).bind_partial(*args, **kwargs)
    return bound.arguments.get("path", "путь не определён")


def file_errors_generator(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        path = _find_path(func, *args, **kwargs)

        try:
            yield from func(*args, **kwargs)
        except (OSError, UnicodeDecodeError) as e:
            handle_file_exception(e, path)

    return wrapper


def file_errors(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        path = _find_path(func, *args, **kwargs)

        try:
            return func(*args, **kwargs)
        except (OSError, UnicodeDecodeError) as e:
            handle_file_exception(e, path)

    return wrapper
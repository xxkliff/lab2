import inspect
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import NoReturn

from streamstats.errors import CliConfigurationError


def handle_file_exception(e: Exception, path: Path | str) -> NoReturn:
    """
    Переводит системную файловую ошибку в CliConfigurationError

    :param e: исходная ошибка OSError или UnicodeDecodeError
    :param path: путь к файлу, с которым произошла ошибка
    :raises CliConfigurationError: всегда, с error_code по типу ошибки
    """
    if not Path(path).resolve().parent.exists():
        raise CliConfigurationError(message="Директории не существует", error_code="directory_not_found",
                                    path=Path(path).parent.resolve()) from e
    elif isinstance(e, FileNotFoundError):
        raise CliConfigurationError(message="Файл не найден", error_code="file_not_found", path=Path(path).resolve()) from e
    elif isinstance(e, UnicodeDecodeError):
        raise CliConfigurationError(message="Файл не в кодировке UTF-8", error_code="invalid_encoding", path=path) from e
    elif isinstance(e, PermissionError):
        raise CliConfigurationError(message="Не хватает прав для выполнения действий с файлом.",
                                    error_code="permission_error", path=path) from e
    elif isinstance(e, OSError):
        raise CliConfigurationError(message=f"Системная ошибка: {e}", error_code="os_error", path=path) from e
    raise e


def _find_path(func: Callable, *args: object, **kwargs: object) -> Path | str:
    """
    Находит path в вызове функции (по имени либо позиционно)

    :param func: обёрнутая функция, у которой есть параметр path
    :return: путь из вызова или строка-заглушка
    """
    bound = inspect.signature(func).bind_partial(*args, **kwargs)
    return bound.arguments.get("path", "путь не определён")


def file_errors_generator(func: Callable) -> Callable:
    """
    Декоратор для функций-генераторов, работающих с файлами

    Ошибки, возникшие во время итерации, переводятся в CliConfigurationError (только связанные с файлами)

    :param func: функция-генератор с параметром path
    :return: обёрнутый генератор
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        path = _find_path(func, *args, **kwargs)

        try:
            yield from func(*args, **kwargs)
        except (OSError, UnicodeDecodeError) as e:
            handle_file_exception(e, path)

    return wrapper


def file_errors(func: Callable) -> Callable:
    """
    Декоратор для обычных функций, работающих с файлами

    Ошибки переводятся в CliConfigurationError (только связанные с файлами)

    :param func: функция с параметром path
    :return: обёрнутая функция
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        path = _find_path(func, *args, **kwargs)

        try:
            return func(*args, **kwargs)
        except (OSError, UnicodeDecodeError) as e:
            handle_file_exception(e, path)

    return wrapper

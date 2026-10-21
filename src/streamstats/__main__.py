import argparse
import json
import logging
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

from streamstats.analysis import ParseStats, analyze
from streamstats.errors import (
    CliConfigurationError,
    StreamStatsError,
    UnsupportedFormatError,
)
from streamstats.models import Event
from streamstats.parsers import parse_csv, parse_jsonl
from streamstats.report import build_report, save_report

PARSERS: dict[str, Callable] = {
    "csv": parse_csv,
    "jsonl": parse_jsonl,
}


def _all_events(args: argparse.Namespace, parser: Callable, parse_stats: ParseStats) -> Iterator[Event]:
    """
    Последовательно читает все входные файлы

    :param args: аргументы команды analyze, используются inputs и skip_invalid
    :param parser: функция-парсер для выбранного формата из PARSERS
    :param parse_stats: общая статистика пропущенных строк для всех файлов
    :return: генератор событий Event из всех файлов по очереди
    """
    for path in args.inputs:
        yield from parser(path, args.skip_invalid, parse_stats)


def _analyze_func(args: argparse.Namespace) -> None:
    """
    Выполняет команду analyze: проверяет аргументы, считает статистику и выводит отчёт

    Если --output не указан, отчёт печатается в stdout

    :param args: аргументы команды analyze
    :raises UnsupportedFormatError: формат не поддерживается
    :raises CliConfigurationError: файл отчёта совпадает с входным
    :raises InvalidEventError: невалидная строка без --skip-invalid
    :raises InvalidTimestampError: невалидный timestamp без --skip-invalid
    """
    parser = PARSERS.get(args.format)
    if parser is None:
        raise UnsupportedFormatError(message=f"Неподдерживаемый формат: {args.format}",
                                     error_code="unsupported_format")

    if args.output is not None:
        for path in args.inputs:
            if path.resolve() == args.output.resolve():
                raise CliConfigurationError(message="Файл отчета совпадает с входным файлом",
                                            error_code="output_is_input", path=args.output)

    parse_stats = ParseStats()
    events = _all_events(args, parser, parse_stats)
    analysis = analyze(events)
    report = build_report(analysis, parse_stats)

    if args.output is None:
        print(json.dumps(report, ensure_ascii=False, indent=4))
    else:
        save_report(report, args.output)


def main(argv: list[str] | None = None) -> int:
    """
    CLI, разбирает аргументы и запускает выбранную команду

    Ошибки StreamStatsError выводятся в stderr. Остальные ошибки, не перехватываются

    :param argv: аргументы команды. Если None - берутся из командной строки
    :return: 0 при успехе, 2 при ошибке
    """
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        prog="streamstats",
        description="Потоковый анализатор файлов с событиями")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="посчитать статистику по файлам")
    analyze_parser.add_argument("inputs", type=Path, nargs="+", metavar="INPUT", help="входные файлы")
    analyze_parser.add_argument("--format", type=str, dest="format", metavar="FORMAT", required=True,
                                help="формат входных файлов (csv или jsonl)")
    analyze_parser.add_argument("--output", type=Path, dest="output", metavar="REPORT.json",
                                help="файл для отчета. Если не указан, напечатается в stdout")
    analyze_parser.add_argument("--skip-invalid", action="store_true", dest="skip_invalid",
                                help="пропускать ошибочные строки с предупреждением в лог")
    analyze_parser.set_defaults(func=_analyze_func)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except StreamStatsError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

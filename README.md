
# Лабораторная работа 2. Потоковый анализатор файлов

Козинов Степан Андреевич, М8О-102БВ-26

## Возможности

- **`analyze`** - читает ивенты из файлов формата CSV и JSONL построчно и пишет отчёт в JSON

## Установка

Нужен Python 3.12 или новее

**Windows (PowerShell)**
```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Тесты и проверки

```bash
python -m pytest
ruff check .
mypy src tests
python -m streamstats --help
pre-commit run --all-files
```

68 тестов, покрытие streamstats > 93%

## Использование

```bash
python -m streamstats --help
python -m streamstats analyze INPUT [INPUT ...] --format csv|jsonl --output REPORT.json
python -m streamstats analyze INPUT --format jsonl --skip-invalid
```

Все входные файлы должны быть одного формата. Если `--output` не указан, отчёт выводится в stdout

### События

Каждая строка файла преобразуется в объект `Event`:

```text
timestamp: ISO 8601 с часовым поясом
level:     DEBUG | INFO | WARNING | ERROR | CRITICAL
source:    непустая строка
message:   строка (может быть пустой)
```

### Примеры
`python -m streamstats analyze examples/events.jsonl --format jsonl`
```text
{
    "total_events": 6,
    "by_level": {
        "INFO": 1,
        "ERROR": 2,
        "WARNING": 1,
        "CRITICAL": 1,
        "DEBUG": 1
    },
    "by_source": {
        "auth": 2,
        "db": 2,
        "payments": 1,
        "cache": 1
    },
    "top_error_sources": [
        {
            "source": "db",
            "count": 2
        },
        {
            "source": "payments",
            "count": 1
        }
    ],
    "first_timestamp": "2026-10-01T08:01:10+03:00",
    "last_timestamp": "2026-10-01T08:04:00+00:00",
    "skipped_invalid": 0
}
```

`python -m streamstats analyze bad.jsonl --format jsonl --output report.json`

Ошибка: (строка 3) (путь bad.jsonl) JSON объект не читается.

Коды возврата: `0` успех, `2` ошибка входных данных или CLI

## Структура проекта

```text
src/streamstats/
├── __init__.py
├── __main__.py      # CLI: вывод и команды
├── models.py        # Event и проверка полей
├── parsers.py       # парсеры CSV и JSONL
├── analysis.py      # Analysis - статистика для вывода, ParseStats
├── report.py        # build_report и save_report
├── decorators.py    # перевод файловых ошибок в CliConfigurationError
├── constants.py     # уровни
└── errors.py        # StreamStatsError и его наследники
tests/
├── test_analysis.py
├── test_cli.py
├── test_csv_parser.py
├── test_json_parser.py
├── test_models.py
└── test_report.py
examples/
└── events.jsonl
```

**Обработка** выполняется по следующим шагам:

1. **Парсер** - генератор, читает файл построчно и отдаёт по одному объекту `Event`.
2. **Объединение файлов** - `_all_events` по каждому файлу.
3. **Анализ** каждое событие передаётся в `Analysis.add`, которое увеличивает счётчики и обновляет timestamp'ы. Само событие после этого не хранится.
4. **Отчёт** из `Analysis` собирается словарь, `save_report` записывает его в JSON.

`readlines()` и `read()` не используются, список всех событий не создаётся.

Все исключения наследуются от `StreamStatsError`

CLI выводит только `StreamStatsError`, в формате сообщения с файлом и строкой, программа возвращает код `2`.

## Принятые решения

- часовой пояс в `timestamp` обязателен, иначе метки из разных файлов не получится сравнивать.
- уровень зависит от регистра: `info` считается ошибкой `unsupported_level`.
- лишние колонки CSV и ключи JSONL игнорируются
- пустой `message` разрешён, пустой или из пробелов `source` - нет.
- неверный заголовок CSV - ошибка файла, поэтому она не пропускается даже с `--skip-invalid`.
- пустой файл даёт нулевой отчёт, в timestamp кладутся null
- top-5 при равенстве сортируется по имени источника.
- отчёт не может совпадать с входным файлом, исходные файлы никогда не изменяются.
- номер строки в CSV считается с учётом заголовка
- пустая строка в JSONL считается невалидной

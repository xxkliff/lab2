
from pathlib import Path

CURRENT_DIR: Path = Path(__file__).resolve().parent
PROJECT_DIR: Path = CURRENT_DIR.parents[1]
EVENTS_PATH: Path = PROJECT_DIR / "examples" / "events.jsonl"

LEVEL_TYPES: tuple[str, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

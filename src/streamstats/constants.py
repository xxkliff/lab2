
from pathlib import Path

CURRENT_DIR: Path = Path(__file__).resolve().parent
PROJECT_DIR: Path = CURRENT_DIR.parents[1]

LEVEL_TYPES: tuple[str, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

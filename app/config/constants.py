from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

DATA_DIR = Path("data")
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
RAW_JSON = INPUT_DIR / "raw_input.json"
OUTPUT_JSON = OUTPUT_DIR / "output.json"


def get_int_env(key: str, default: Optional[int] = None) -> Optional[int]:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


__all__ = [
    "RAW_JSON",
    "OUTPUT_JSON",
    "get_int_env",
]

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_camera_profile(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

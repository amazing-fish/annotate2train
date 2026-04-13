from __future__ import annotations

from typing import Iterable


def normalize_scores(values: Iterable[float]) -> list[float]:
    values = list(values)
    if not values:
        return []
    max_value = max(values)
    if max_value <= 0:
        return [0.0 for _ in values]
    return [value / max_value for value in values]

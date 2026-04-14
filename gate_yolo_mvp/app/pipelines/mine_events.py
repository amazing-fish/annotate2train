from __future__ import annotations

from typing import Iterable


def find_candidate_windows(
    scores: Iterable[tuple[int, float]],
    threshold: float,
    max_gap_ms: int,
) -> list[tuple[int, int]]:
    active_timestamps = [timestamp for timestamp, score in scores if score >= threshold]
    if not active_timestamps:
        return []

    windows: list[tuple[int, int]] = []
    start = previous = active_timestamps[0]
    for timestamp in active_timestamps[1:]:
        if timestamp - previous > max_gap_ms:
            windows.append((start, previous))
            start = timestamp
        previous = timestamp
    windows.append((start, previous))
    return windows

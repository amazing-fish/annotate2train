from __future__ import annotations

from typing import Iterable


def build_frame_records(messages: Iterable[dict]) -> list[dict]:
    return sorted(messages, key=lambda item: item["timestamp_ms"])

from __future__ import annotations


ROLES = [
    "closed_like",
    "opening_early",
    "opening_mid",
    "max_open",
    "late_or_return",
]


def select_representative_frames(candidates: list[dict]) -> list[dict]:
    sorted_items = sorted(candidates, key=lambda item: item["open_angle_deg"])
    return [{**item, "selection_role": ROLES[index]} for index, item in enumerate(sorted_items[:5])]

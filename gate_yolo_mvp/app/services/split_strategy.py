from __future__ import annotations

import random


def assign_split_by_group(
    items: list[dict],
    group_key: str,
    train_ratio: float,
    seed: int,
) -> dict[str, str]:
    groups = sorted({item[group_key] for item in items})
    random.Random(seed).shuffle(groups)
    cut = max(1, int(round(len(groups) * train_ratio)))
    if cut >= len(groups):
        cut = len(groups) - 1
    train_groups = set(groups[:cut])
    return {
        item["frame_id"]: ("train" if item[group_key] in train_groups else "val")
        for item in items
    }

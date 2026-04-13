from __future__ import annotations

from app.services.split_strategy import assign_split_by_group


def build_dataset_items(
    items: list[dict],
    group_key: str = "event_id",
    train_ratio: float = 0.8,
    seed: int = 42,
) -> list[dict]:
    splits = assign_split_by_group(items, group_key=group_key, train_ratio=train_ratio, seed=seed)
    return [{**item, "split": splits[item["frame_id"]]} for item in items]

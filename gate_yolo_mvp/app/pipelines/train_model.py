from __future__ import annotations


def build_train_command(dataset_root: str, recipe_path: str) -> str:
    return f"python scripts/train_pose.py --data {dataset_root}/data.yaml --recipe {recipe_path}"

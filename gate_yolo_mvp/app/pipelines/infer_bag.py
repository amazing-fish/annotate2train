from __future__ import annotations


def build_infer_command(model_version_path: str, source_bag: str) -> str:
    return f"python scripts/infer_pose.py --weights {model_version_path} --source {source_bag}"

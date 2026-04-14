#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def load_runtime_cfg(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def compute_padded_box(pivot: Tuple[int, int], tip: Tuple[int, int], w: int, h: int, pad_px: int, min_box: int):
    x1 = min(pivot[0], tip[0]) - pad_px
    y1 = min(pivot[1], tip[1]) - pad_px
    x2 = max(pivot[0], tip[0]) + pad_px
    y2 = max(pivot[1], tip[1]) + pad_px

    if x2 - x1 < min_box:
        cx = (x1 + x2) / 2.0
        x1 = int(cx - min_box / 2)
        x2 = int(cx + min_box / 2)
    if y2 - y1 < min_box:
        cy = (y1 + y2) / 2.0
        y1 = int(cy - min_box / 2)
        y2 = int(cy + min_box / 2)

    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w - 1, x2)
    y2 = min(h - 1, y2)
    return x1, y1, x2, y2


def to_yolo_pose_line(pivot, tip, w, h, pad_px, min_box, cls_idx=0):
    x1, y1, x2, y2 = compute_padded_box(pivot, tip, w, h, pad_px, min_box)
    xc = ((x1 + x2) / 2.0) / w
    yc = ((y1 + y2) / 2.0) / h
    bw = (x2 - x1) / w
    bh = (y2 - y1) / h
    p1x = pivot[0] / w
    p1y = pivot[1] / h
    p2x = tip[0] / w
    p2y = tip[1] / h
    values = [cls_idx, xc, yc, bw, bh, p1x, p1y, p2x, p2y]
    return " ".join(f"{v:.6f}" if isinstance(v, float) else str(v) for v in values)


def find_pairs(image_dir: Path, ann_dir: Path) -> List[Tuple[Path, Path]]:
    pairs = []
    for image_path in sorted(image_dir.iterdir()):
        if image_path.suffix.lower() not in IMAGE_EXTS:
            continue
        ann_path = ann_dir / f"{image_path.stem}.json"
        if ann_path.exists():
            pairs.append((image_path, ann_path))
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Legacy YOLO dataset builder. Event-grouped dataset versions now live under app.pipelines."
    )
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--ann-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("data/yolo_pose"))
    parser.add_argument("--runtime-cfg", type=Path, default=Path("configs/runtime.yaml"))
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cfg = load_runtime_cfg(args.runtime_cfg)
    pad_px = int(cfg.get("bbox_pad_px", 24))
    min_box = int(cfg.get("min_bbox_size_px", 32))

    pairs = find_pairs(args.image_dir, args.ann_dir)
    if len(pairs) < 2:
        raise RuntimeError("Need at least 2 labeled images to build train/val dataset")

    random.Random(args.seed).shuffle(pairs)
    train_count = max(1, int(len(pairs) * args.train_ratio))
    if train_count >= len(pairs):
        train_count = len(pairs) - 1

    splits = {
        "train": pairs[:train_count],
        "val": pairs[train_count:],
    }

    for split, items in splits.items():
        img_out = args.out_dir / "images" / split
        lbl_out = args.out_dir / "labels" / split
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        for image_path, ann_path in items:
            shutil.copy2(image_path, img_out / image_path.name)
            with ann_path.open("r", encoding="utf-8") as f:
                ann = json.load(f)
            instances = ann.get("instances", [])
            if not instances:
                continue
            inst = instances[0]
            w = int(ann["image_width"])
            h = int(ann["image_height"])
            pivot = tuple(inst["pivot"])
            tip = tuple(inst["tip"])
            line = to_yolo_pose_line(pivot, tip, w, h, pad_px, min_box)
            with (lbl_out / f"{image_path.stem}.txt").open("w", encoding="utf-8") as f:
                f.write(line + "\n")

    data_yaml = {
        "path": str(args.out_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "kpt_shape": [2, 2],
        "flip_idx": [0, 1],
        "names": {0: cfg.get("class_name", "gate_arm")},
        "kpt_names": {0: ["pivot", "tip"]},
    }
    with (args.out_dir / "data.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(data_yaml, f, sort_keys=False, allow_unicode=True)

    print(f"[OK] Dataset built at: {args.out_dir}")
    print(f"[INFO] train={len(splits['train'])}, val={len(splits['val'])}")


if __name__ == "__main__":
    main()

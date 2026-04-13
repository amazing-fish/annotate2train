#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="从一张已标注的关闭闸机图片生成 closed_ref.json")
    parser.add_argument("--ann-json", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, default=Path("data/reference/closed_ref.json"))
    args = parser.parse_args()

    with args.ann_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] closed reference saved to: {args.out_json}")


if __name__ == "__main__":
    main()

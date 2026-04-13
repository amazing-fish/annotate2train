#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--format", type=str, default="onnx", choices=["onnx", "engine"])
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--half", action="store_true")
    parser.add_argument("--dynamic", action="store_true")
    parser.add_argument("--device", type=str, default="0")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Please install ultralytics first: pip install -r requirements.txt") from exc

    model = YOLO(str(args.weights))
    model.export(
        format=args.format,
        imgsz=args.imgsz,
        half=args.half,
        dynamic=args.dynamic,
        device=args.device,
    )


if __name__ == "__main__":
    main()

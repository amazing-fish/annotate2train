#!/usr/bin/env python3
"""轻量级闸杆关键点标注工具。

用法：
python scripts/annotate_gate_points.py \
  --image-dir data/raw \
  --ann-dir data/ann

操作：
- 左键：先点 pivot，再点 tip
- r：重置当前标注
- s：保存当前标注
- n：保存并下一张
- b：上一张
- q / ESC：退出
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
WINDOW_NAME = "gate-annotator"


class Annotator:
    def __init__(self, image_dir: Path, ann_dir: Path) -> None:
        self.image_dir = image_dir
        self.ann_dir = ann_dir
        self.ann_dir.mkdir(parents=True, exist_ok=True)
        self.images = sorted([p for p in image_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS])
        if not self.images:
            raise FileNotFoundError(f"No images found under {image_dir}")
        self.index = 0
        self.current_points: List[Tuple[int, int]] = []
        self.current_image = None
        self.current_canvas = None

    def ann_path(self, image_path: Path) -> Path:
        return self.ann_dir / f"{image_path.stem}.json"

    def load_existing(self, image_path: Path) -> None:
        self.current_points = []
        ann_path = self.ann_path(image_path)
        if not ann_path.exists():
            return
        with ann_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        instances = data.get("instances", [])
        if instances:
            inst = instances[0]
            pivot = inst.get("pivot")
            tip = inst.get("tip")
            if pivot and tip:
                self.current_points = [(int(pivot[0]), int(pivot[1])), (int(tip[0]), int(tip[1]))]

    def load_image(self) -> None:
        image_path = self.images[self.index]
        self.current_image = cv2.imread(str(image_path))
        if self.current_image is None:
            raise RuntimeError(f"Failed to read image: {image_path}")
        self.load_existing(image_path)
        self.redraw()

    def redraw(self) -> None:
        assert self.current_image is not None
        canvas = self.current_image.copy()
        h, w = canvas.shape[:2]
        image_path = self.images[self.index]
        text = f"[{self.index + 1}/{len(self.images)}] {image_path.name}"
        cv2.putText(canvas, text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, "L-click: pivot -> tip | r:reset s:save n:next b:prev q:quit", (20, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2, cv2.LINE_AA)

        if len(self.current_points) >= 1:
            cv2.circle(canvas, self.current_points[0], 6, (0, 255, 0), -1)
            cv2.putText(canvas, "pivot", (self.current_points[0][0] + 8, self.current_points[0][1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        if len(self.current_points) >= 2:
            cv2.circle(canvas, self.current_points[1], 6, (0, 0, 255), -1)
            cv2.putText(canvas, "tip", (self.current_points[1][0] + 8, self.current_points[1][1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.line(canvas, self.current_points[0], self.current_points[1], (255, 0, 255), 2, cv2.LINE_AA)

        self.current_canvas = canvas

    def save_current(self) -> None:
        if len(self.current_points) != 2:
            print("[WARN] Need exactly 2 points: pivot and tip")
            return
        image_path = self.images[self.index]
        h, w = self.current_image.shape[:2]
        pivot, tip = self.current_points
        x1 = min(pivot[0], tip[0])
        y1 = min(pivot[1], tip[1])
        x2 = max(pivot[0], tip[0])
        y2 = max(pivot[1], tip[1])
        data: Dict = {
            "version": "gate-mvp-1.0",
            "image_file": image_path.name,
            "image_width": w,
            "image_height": h,
            "instances": [
                {
                    "id": 1,
                    "class_name": "gate_arm",
                    "pivot": [int(pivot[0]), int(pivot[1])],
                    "tip": [int(tip[0]), int(tip[1])],
                    "bbox_xyxy": [int(x1), int(y1), int(x2), int(y2)],
                    "status": "labeled",
                }
            ],
        }
        out = self.ann_path(image_path)
        with out.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] Saved: {out}")

    def on_mouse(self, event: int, x: int, y: int, flags: int, param: object) -> None:
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        if len(self.current_points) >= 2:
            self.current_points = []
        self.current_points.append((int(x), int(y)))
        self.redraw()

    def run(self) -> None:
        self.load_image()
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, 1400, 900)
        cv2.setMouseCallback(WINDOW_NAME, self.on_mouse)
        while True:
            assert self.current_canvas is not None
            cv2.imshow(WINDOW_NAME, self.current_canvas)
            key = cv2.waitKey(30) & 0xFF
            if key in (27, ord("q")):
                break
            if key == ord("r"):
                self.current_points = []
                self.redraw()
            elif key == ord("s"):
                self.save_current()
                self.redraw()
            elif key == ord("n"):
                self.save_current()
                self.index = min(self.index + 1, len(self.images) - 1)
                self.load_image()
            elif key == ord("b"):
                self.index = max(self.index - 1, 0)
                self.load_image()
        cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--ann-dir", type=Path, required=True)
    args = parser.parse_args()
    annotator = Annotator(args.image_dir, args.ann_dir)
    annotator.run()


if __name__ == "__main__":
    main()

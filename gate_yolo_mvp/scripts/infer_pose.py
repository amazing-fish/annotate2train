#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import yaml

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def normalize_angle_deg(angle: float) -> float:
    angle %= 360.0
    if angle < 0:
        angle += 360.0
    return angle


def circular_diff_deg(a: float, b: float) -> float:
    d = abs(normalize_angle_deg(a) - normalize_angle_deg(b))
    return min(d, 360.0 - d)


def line_angle_deg(pivot: Tuple[float, float], tip: Tuple[float, float]) -> float:
    dx = tip[0] - pivot[0]
    dy = pivot[1] - tip[1]  # 图像坐标转常规笛卡尔坐标
    return normalize_angle_deg(math.degrees(math.atan2(dy, dx)))


def load_cfg(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_closed_ref_angle(cfg: Dict, root: Path) -> float:
    ref_json = cfg.get("closed_reference_json")
    if ref_json:
        ref_path = (root / ref_json).resolve() if not Path(ref_json).is_absolute() else Path(ref_json)
        if ref_path.exists():
            with ref_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            inst = data["instances"][0]
            return line_angle_deg(tuple(inst["pivot"]), tuple(inst["tip"]))
    angle = cfg.get("closed_reference_angle_deg")
    if angle is None:
        raise RuntimeError("Need either closed_reference_json or closed_reference_angle_deg in runtime.yaml")
    return float(angle)


def classify_state(open_angle: float, cfg: Dict) -> str:
    closed_th = float(cfg.get("closed_threshold_deg", 10.0))
    open_th = float(cfg.get("open_threshold_deg", 75.0))
    if open_angle <= closed_th:
        return "closed"
    if open_angle >= open_th:
        return "open"
    return "partial"


def list_images(source: Path):
    if source.is_file():
        return [source]
    return sorted([p for p in source.iterdir() if p.suffix.lower() in IMAGE_EXTS])


def draw_result(image, pivot, tip, state, open_angle, conf):
    canvas = image.copy()
    pivot_i = (int(pivot[0]), int(pivot[1]))
    tip_i = (int(tip[0]), int(tip[1]))
    cv2.circle(canvas, pivot_i, 6, (0, 255, 0), -1)
    cv2.circle(canvas, tip_i, 6, (0, 0, 255), -1)
    cv2.line(canvas, pivot_i, tip_i, (255, 0, 255), 2, cv2.LINE_AA)
    text = f"state={state} angle={open_angle:.1f} conf={conf:.3f}"
    cv2.putText(canvas, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--runtime-cfg", type=Path, default=Path("configs/runtime.yaml"))
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--conf", type=float, default=None)
    parser.add_argument("--save-vis-dir", type=Path, default=Path("outputs/infer_vis"))
    parser.add_argument("--save-json", type=Path, default=Path("outputs/infer_results.json"))
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Please install ultralytics first: pip install -r requirements.txt") from exc

    project_root = Path(__file__).resolve().parents[1]
    cfg = load_cfg(args.runtime_cfg if args.runtime_cfg.is_absolute() else project_root / args.runtime_cfg)
    closed_angle = load_closed_ref_angle(cfg, project_root)
    predict_conf = float(cfg.get("predict_conf", 0.25)) if args.conf is None else args.conf

    model = YOLO(str(args.weights))
    args.save_vis_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for image_path in list_images(args.source):
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"[WARN] failed to read image: {image_path}")
            continue
        results = model.predict(source=str(image_path), imgsz=args.imgsz, conf=predict_conf, verbose=False)
        result = results[0]

        if result.keypoints is None or len(result.keypoints.xy) == 0:
            records.append({
                "image": str(image_path),
                "gate_detected": False,
                "state": "unknown",
                "open_angle_deg": None,
                "confidence": 0.0,
            })
            continue

        kpts = result.keypoints.xy[0].cpu().numpy()
        pivot = tuple(float(v) for v in kpts[0])
        tip = tuple(float(v) for v in kpts[1])
        raw_angle = line_angle_deg(pivot, tip)
        open_angle = circular_diff_deg(raw_angle, closed_angle)
        conf = float(result.boxes.conf[0].cpu().item()) if result.boxes is not None and len(result.boxes) else 0.0
        state = classify_state(open_angle, cfg)

        vis = draw_result(image, pivot, tip, state, open_angle, conf)
        out_vis = args.save_vis_dir / image_path.name
        cv2.imwrite(str(out_vis), vis)

        records.append({
            "image": str(image_path),
            "gate_detected": True,
            "state": state,
            "open_angle_deg": round(open_angle, 3),
            "image_angle_deg": round(raw_angle, 3),
            "closed_reference_angle_deg": round(closed_angle, 3),
            "pivot": [round(pivot[0], 2), round(pivot[1], 2)],
            "tip": [round(tip[0], 2), round(tip[1], 2)],
            "confidence": round(conf, 4),
            "vis_path": str(out_vis),
        })

    args.save_json.parent.mkdir(parents=True, exist_ok=True)
    with args.save_json.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved results to {args.save_json}")


if __name__ == "__main__":
    main()

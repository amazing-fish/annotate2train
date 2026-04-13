#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path
from typing import Dict, Tuple

import cv2
import numpy as np
import yaml
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse


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
    dy = pivot[1] - tip[1]
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
        raise RuntimeError("Need either closed_reference_json or closed_reference_angle_deg")
    return float(angle)


def classify_state(open_angle: float, cfg: Dict) -> str:
    closed_th = float(cfg.get("closed_threshold_deg", 10.0))
    open_th = float(cfg.get("open_threshold_deg", 75.0))
    if open_angle <= closed_th:
        return "closed"
    if open_angle >= open_th:
        return "open"
    return "partial"


def create_app(weights: Path, runtime_cfg: Path) -> FastAPI:
    from ultralytics import YOLO

    root = Path(__file__).resolve().parents[1]
    cfg = load_cfg(runtime_cfg if runtime_cfg.is_absolute() else root / runtime_cfg)
    closed_angle = load_closed_ref_angle(cfg, root)
    predict_conf = float(cfg.get("predict_conf", 0.25))
    model = YOLO(str(weights))

    app = FastAPI(title="gate-yolo-mvp")

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.post("/predict")
    async def predict(file: UploadFile = File(...)):
        content = await file.read()
        image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            return JSONResponse(status_code=400, content={"error": "invalid image"})
        results = model.predict(source=image, conf=predict_conf, verbose=False)
        result = results[0]
        if result.keypoints is None or len(result.keypoints.xy) == 0:
            return {"gate_detected": False, "state": "unknown", "open_angle_deg": None, "confidence": 0.0}
        kpts = result.keypoints.xy[0].cpu().numpy()
        pivot = tuple(float(v) for v in kpts[0])
        tip = tuple(float(v) for v in kpts[1])
        raw_angle = line_angle_deg(pivot, tip)
        open_angle = circular_diff_deg(raw_angle, closed_angle)
        conf = float(result.boxes.conf[0].cpu().item()) if result.boxes is not None and len(result.boxes) else 0.0
        state = classify_state(open_angle, cfg)
        return {
            "gate_detected": True,
            "state": state,
            "open_angle_deg": round(open_angle, 3),
            "image_angle_deg": round(raw_angle, 3),
            "closed_reference_angle_deg": round(closed_angle, 3),
            "pivot": [round(pivot[0], 2), round(pivot[1], 2)],
            "tip": [round(tip[0], 2), round(tip[1], 2)],
            "confidence": round(conf, 4),
        }

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--runtime-cfg", type=Path, default=Path("configs/runtime.yaml"))
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    import uvicorn
    app = create_app(args.weights, args.runtime_cfg)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

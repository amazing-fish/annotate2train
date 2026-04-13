from __future__ import annotations


def build_machine_annotation(
    frame_id: str,
    model_version_id: str,
    pivot: tuple[float, float],
    tip: tuple[float, float],
    image_angle_deg: float,
    open_angle_deg: float,
    confidence: float,
) -> dict:
    return {
        "frame_id": frame_id,
        "model_version_id": model_version_id,
        "pivot_x": pivot[0],
        "pivot_y": pivot[1],
        "tip_x": tip[0],
        "tip_y": tip[1],
        "image_angle_deg": image_angle_deg,
        "open_angle_deg": open_angle_deg,
        "confidence": confidence,
    }

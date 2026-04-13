from __future__ import annotations


def to_review_status(machine_angle: float, human_angle: float, delta_threshold: float) -> str:
    if abs(machine_angle - human_angle) > delta_threshold:
        return "adjusted"
    return "accepted"

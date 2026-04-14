from __future__ import annotations


def should_flag_result(
    confidence: float,
    angle_jump_deg: float,
    conf_threshold: float,
    jump_threshold: float,
) -> bool:
    return confidence < conf_threshold or angle_jump_deg > jump_threshold

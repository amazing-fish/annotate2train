from app.pipelines.select_five_frames import select_representative_frames


def test_select_representative_frames_returns_five_unique_roles():
    candidates = [
        {"frame_id": "f1", "open_angle_deg": 0, "blur_score": 1},
        {"frame_id": "f2", "open_angle_deg": 15, "blur_score": 1},
        {"frame_id": "f3", "open_angle_deg": 40, "blur_score": 1},
        {"frame_id": "f4", "open_angle_deg": 80, "blur_score": 1},
        {"frame_id": "f5", "open_angle_deg": 55, "blur_score": 1},
    ]
    picked = select_representative_frames(candidates)
    assert len(picked) == 5
    assert len({item["selection_role"] for item in picked}) == 5

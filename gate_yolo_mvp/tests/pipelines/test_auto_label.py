from app.services.angle_logic import to_review_status


def test_to_review_status_marks_large_delta_as_adjusted():
    assert to_review_status(machine_angle=10, human_angle=30, delta_threshold=5) == "adjusted"

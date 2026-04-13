from app.pipelines.enqueue_review import should_flag_result


def test_should_flag_result_for_low_confidence_and_angle_jump():
    assert should_flag_result(
        confidence=0.2,
        angle_jump_deg=40,
        conf_threshold=0.5,
        jump_threshold=20,
    ) is True

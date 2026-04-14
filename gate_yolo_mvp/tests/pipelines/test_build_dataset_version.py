from app.services.split_strategy import assign_split_by_group


def test_assign_split_by_group_keeps_same_event_together():
    items = [
        {"frame_id": "a1", "event_id": "evt1"},
        {"frame_id": "a2", "event_id": "evt1"},
        {"frame_id": "b1", "event_id": "evt2"},
    ]
    splits = assign_split_by_group(items, group_key="event_id", train_ratio=0.5, seed=42)
    assert splits["a1"] == splits["a2"]

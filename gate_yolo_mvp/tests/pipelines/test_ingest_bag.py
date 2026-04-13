from app.pipelines.ingest_bag import build_frame_records


def test_build_frame_records_keeps_timestamp_order():
    messages = [{"timestamp_ms": 30}, {"timestamp_ms": 10}, {"timestamp_ms": 20}]
    frames = build_frame_records(messages)
    assert [f["timestamp_ms"] for f in frames] == [10, 20, 30]

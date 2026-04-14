from app.pipelines.mine_events import find_candidate_windows


def test_find_candidate_windows_merges_adjacent_active_frames():
    scores = [(0, 0.1), (1000, 0.8), (2000, 0.9), (5000, 0.2)]
    windows = find_candidate_windows(scores, threshold=0.5, max_gap_ms=1500)
    assert windows == [(1000, 2000)]

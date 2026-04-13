from pathlib import Path

from app.config import load_camera_profile


def test_load_camera_profile_reads_fixed_roi(tmp_path: Path):
    cfg = tmp_path / "cam.yaml"
    cfg.write_text(
        "name: cam1\nbag_topic: /front/image\nroi: [10, 20, 110, 220]\n",
        encoding="utf-8",
    )
    profile = load_camera_profile(cfg)
    assert profile["bag_topic"] == "/front/image"
    assert profile["roi"] == [10, 20, 110, 220]

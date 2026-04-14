from app.pipelines.train_model import build_train_command


def test_build_train_command_uses_dataset_version_root():
    cmd = build_train_command(
        dataset_root="data/datasets/ds1",
        recipe_path="configs/recipes/pose_default.yaml",
    )
    assert "data/datasets/ds1/data.yaml" in cmd

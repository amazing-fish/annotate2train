from app.db.repo import init_db, list_tables


def test_init_db_creates_core_tables(tmp_path):
    db_path = tmp_path / "gate.db"
    init_db(db_path)
    names = set(list_tables(db_path))
    assert {"bags", "frames", "events", "human_annotations", "dataset_versions"} <= names

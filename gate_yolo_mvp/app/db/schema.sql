CREATE TABLE IF NOT EXISTS bags (
    bag_id TEXT PRIMARY KEY,
    camera_profile_id TEXT,
    bag_path TEXT NOT NULL,
    bag_sha256 TEXT,
    captured_at TEXT,
    duration_sec REAL,
    ingest_status TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS frames (
    frame_id TEXT PRIMARY KEY,
    bag_id TEXT NOT NULL,
    timestamp_ms INTEGER NOT NULL,
    frame_index INTEGER,
    full_frame_path TEXT,
    roi_frame_path TEXT,
    blur_score REAL,
    brightness_score REAL,
    candidate_score REAL
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    bag_id TEXT NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    mining_version TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS machine_annotations (
    machine_annotation_id TEXT PRIMARY KEY,
    frame_id TEXT NOT NULL,
    model_version_id TEXT,
    pivot_x REAL,
    pivot_y REAL,
    tip_x REAL,
    tip_y REAL,
    image_angle_deg REAL,
    open_angle_deg REAL,
    confidence REAL,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS human_annotations (
    human_annotation_id TEXT PRIMARY KEY,
    frame_id TEXT NOT NULL,
    source_machine_annotation_id TEXT,
    pivot_x REAL,
    pivot_y REAL,
    tip_x REAL,
    tip_y REAL,
    open_angle_deg REAL,
    review_status TEXT,
    review_note TEXT,
    reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS dataset_versions (
    dataset_version_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT,
    source_filter_json TEXT,
    split_strategy TEXT,
    split_group_key TEXT,
    dataset_root TEXT,
    sample_count INTEGER DEFAULT 0
);

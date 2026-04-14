# Anchor 文档（技术路径与日志对齐）

## 技术路径锚点
- 项目阶段：固定前视 bag 到训练/推理的一体化 MVP 骨架。
- 关键流程：`ingest_bag -> mine_events -> select_five_frames -> auto_label -> enqueue_review -> build_dataset_version -> train_model -> infer_bag`。
- API 侧能力：`/api/review/queue` 与 `/api/run/ingest` 等轻量流程入口。
- 测试策略：以 `pytest` 覆盖配置、管线、存储和 API 烟雾路径。

## 版本策略
- 版本号格式：`v主.次.修`。
- 变更类型：`feature`、`refactor`、`bugfix`。

## 修改日志

### v0.1.1 (bugfix)
- 修复：补齐 `httpx` 依赖，解决 `fastapi.testclient` 在测试收集阶段报错导致 API 测试无法运行的问题。
- 验证：`pytest -q` 全量通过。

### v0.1.0 (feature)
- 初始 MVP 骨架：完成 bag 管线、数据集构建、训练/推理命令组装、FastAPI 路由与基础测试。

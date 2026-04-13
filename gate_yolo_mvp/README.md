# Gate YOLO MVP（A4000 / Linux）

这是一个最小可跑通版本，用于识别**汽车前视图中闸机是否开启，以及开启角度**。

当前 MVP 方案：
- 模型：**YOLO Pose**
- 标注：每张图 2 个关键点（`pivot`, `tip`）
- 输出：`closed / partial / open` + `open_angle_deg`

> 说明：你目前只有 10 张图，这一版主要用于**流程打通与样本过拟合验证**，不是量产精度版本。

---

## 1. 目录

```text
.
├── configs/
│   ├── runtime.yaml
│   └── manual_labeling_spec.md
├── data/
│   ├── raw/            # 原始图片放这里
│   ├── ann/            # 标注结果 json
│   ├── reference/      # 闭合参考图 json
│   └── yolo_pose/      # 构建后的 YOLO pose 数据集
├── outputs/
├── scripts/
│   ├── annotate_gate_points.py
│   ├── build_dataset.py
│   ├── train_pose.py
│   ├── infer_pose.py
│   ├── export_model.py
│   ├── make_closed_reference.py
│   └── service.py
├── requirements.txt
└── setup.sh
```

---

## 2. 环境安装

```bash
cd gate_yolo_mvp
bash setup.sh
```

Ultralytics 官方支持 pose 任务训练、推理与导出，且支持导出 ONNX / TensorRT 等格式。YOLO pose 的自定义数据集需提供 `kpt_shape` 和 YOLO pose 标签格式。citeturn947360search1turn410610search4turn956859search4

---

## 3. 放入原始图片

把你的 10 张图放到：

```bash
data/raw/
```

---

## 4. 人工标注

运行轻量标注工具：

```bash
python scripts/annotate_gate_points.py \
  --image-dir data/raw \
  --ann-dir data/ann
```

### 操作方法
- 鼠标左键：按顺序点 2 次
  - 第 1 次：`pivot`
  - 第 2 次：`tip`
- `r`：重置当前图
- `s`：保存当前图
- `n`：保存并下一张
- `b`：上一张
- `q` / `ESC`：退出

### 标注原则
详见：

```text
configs/manual_labeling_spec.md
```

Labelme 支持 point/line/polygon 等多种形状，说明“点标注”是常规、成熟的标注方式；Ultralytics 对 pose 标签格式也要求按关键点坐标组织。citeturn956859search1turn410610search4

---

## 5. 生成“闭合参考方向”

你需要至少 1 张**闸杆关闭状态**图片作为基准，用来把图像方向转换成“开启角度”。

假设 `data/ann/img_0001.json` 是关闭状态：

```bash
python scripts/make_closed_reference.py \
  --ann-json data/ann/img_0001.json \
  --out-json data/reference/closed_ref.json
```

若没有参考图，也可以直接在 `configs/runtime.yaml` 里手工填写：

```yaml
closed_reference_angle_deg: 0.0
```

---

## 6. 构建 YOLO Pose 数据集

```bash
python scripts/build_dataset.py \
  --image-dir data/raw \
  --ann-dir data/ann \
  --out-dir data/yolo_pose \
  --runtime-cfg configs/runtime.yaml
```

Ultralytics pose 标签格式为：

```text
<class> <x_center> <y_center> <width> <height> <px1> <py1> <px2> <py2> ...
```

坐标需要归一化；数据集 YAML 中要声明 `kpt_shape` 和 `flip_idx`。citeturn869467search0turn410610search4

---

## 7. 训练

```bash
python scripts/train_pose.py \
  --data data/yolo_pose/data.yaml \
  --model yolo11n-pose.pt \
  --epochs 200 \
  --imgsz 960 \
  --batch 8 \
  --device 0
```

### 当前训练策略
针对 10 张图的 MVP：
- 使用预训练 pose 权重
- 关闭 mosaic / mixup / flip 等强增强
- 只保留轻微亮度与缩放扰动

目的不是泛化，而是先看：
- 是否能快速收敛
- 是否能稳定回归杆根部与杆端
- 角度逻辑是否跑通

Ultralytics 官方支持直接用 pose 预训练权重进行自定义训练。citeturn410610search1turn947360search0turn947360search14

---

## 8. 推理

```bash
python scripts/infer_pose.py \
  --weights outputs/train_runs/gate_pose_mvp/weights/best.pt \
  --source data/raw \
  --runtime-cfg configs/runtime.yaml
```

输出：
- 可视化图：`outputs/infer_vis/`
- 结构化结果：`outputs/infer_results.json`

结果字段示例：

```json
{
  "gate_detected": true,
  "state": "partial",
  "open_angle_deg": 37.5,
  "confidence": 0.92
}
```

---

## 9. 导出部署模型

### 导出 ONNX

```bash
python scripts/export_model.py \
  --weights outputs/train_runs/gate_pose_mvp/weights/best.pt \
  --format onnx \
  --imgsz 960
```

### 导出 TensorRT

```bash
python scripts/export_model.py \
  --weights outputs/train_runs/gate_pose_mvp/weights/best.pt \
  --format engine \
  --imgsz 960 \
  --half \
  --device 0
```

Ultralytics 官方提供 `export` 模式，可导出 ONNX、TensorRT 等格式；TensorRT 是 NVIDIA 侧的高性能推理路径。citeturn956859search4turn956859search0

---

## 10. 启动在线服务

```bash
python scripts/service.py \
  --weights outputs/train_runs/gate_pose_mvp/weights/best.pt \
  --runtime-cfg configs/runtime.yaml \
  --host 0.0.0.0 \
  --port 8000
```

接口：
- `GET /health`
- `POST /predict`，表单字段名：`file`

示例：

```bash
curl -X POST \
  -F "file=@data/raw/xxx.jpg" \
  http://127.0.0.1:8000/predict
```

---

## 11. 当前 MVP 的已知限制

1. 只支持单图单闸杆。
2. 依赖一个“关闭状态基准方向”。
3. 10 张图只能做流程验证，不能证明真实场景鲁棒性。
4. 对严重遮挡、夜间反光、远距离小目标，当前精度不可靠。

---

## 12. 下一阶段建议

MVP 跑通后，下一步应升级为：
- 样本扩充到 100~300 张
- 加入夜间/逆光/雨天/遮挡分桶
- 按闸机型号分桶评估
- 视频流时间平滑
- 必要时升级为 `detect -> roi -> pose/segment` 两阶段


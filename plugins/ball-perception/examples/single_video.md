# 示例：单视频羽毛球检测

## 场景

用户有一段羽毛球比赛视频，想提取球的 3D 轨迹。只有一台相机（单目），需要利用场地几何约束恢复深度。

## 输入

```bash
python scripts/pipeline.py \
  --config assets/config.yaml \
  --video data/badminton_match.mp4 \
  --camera cam0 \
  --display
```

## 配置文件（单目简化版）

```yaml
detector:
  type: "yolo"
  model_path: "yolov8n.pt"
  input_size: 1024
  confidence_threshold: 0.25
  max_det: 1
  device: "cpu"

tracker:
  window_size: 5
  max_gap: 3
  max_velocity: 500.0
  use_prediction: true

filter:
  dt: 0.016
  dim: 2
  model: "CV"
  process_noise: 1.0
  measurement_noise: 10.0

geometry:
  method: "DLT"

cameras:
  - id: "cam0"
    width: 1920
    height: 1080
    K:
      - [1200, 0, 960]
      - [0, 1200, 540]
      - [0, 0, 1]
    dist_coeffs: [0, 0, 0, 0, 0]
    R:
      - [1, 0, 0]
      - [0, 1, 0]
      - [0, 0, 1]
    t: [0, 0, 0]
```

## 预期输出

```json
{
  "status": "ok",
  "states": [
    {"x": 0.12, "y": 1.55, "z": 5.20, "vx": 2.1, "vy": -0.3, "vz": -4.5, "timestamp": 0.000},
    {"x": 0.15, "y": 1.54, "z": 5.13, "vx": 2.3, "vy": -0.4, "vz": -4.3, "timestamp": 0.016}
  ],
  "stats": {
    "frames_processed": 2500,
    "avg_latency_ms": 12.5,
    "max_latency_ms": 18.3,
    "detection_rate": 0.91
  }
}
```

## 关键参数说明

- `max_velocity: 500.0`：羽毛球在 1080p 画面中帧间位移通常 < 300px，500 是安全上限
- `window_size: 5`：5 帧滑动窗口，在 60fps 视频中覆盖约 83ms
- `max_gap: 3`：允许连续 3 帧丢失（约 50ms），超过则重置 tracker

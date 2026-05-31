# 示例：双目乒乓球感知（DeepMind 风格）

## 场景

参考 DeepMind 乒乓球系统：两台 Ximea MQ013CG-ON 相机，硬件同步，125 FPS，1280×1024 分辨率，2.74m 基线（球台宽度），对侧放置。

## 配置文件

```yaml
detector:
  type: "yolo"
  model_path: "models/table_tennis_ball.pt"
  input_size: 1024
  confidence_threshold: 0.25
  max_det: 1
  device: "cuda:0"

tracker:
  window_size: 5
  max_gap: 2
  max_velocity: 300.0
  use_prediction: true

filter:
  dt: 0.008
  dim: 2
  model: "CV"
  process_noise: 0.5
  measurement_noise: 5.0
  process_noise_3d: 0.1
  measurement_noise_3d: 2.0

geometry:
  method: "DLT"
  T_cam_to_world:
    - [1, 0, 0, 0]
    - [0, 1, 0, 0]
    - [0, 0, 1, 0]
    - [0, 0, 0, 1]

cameras:
  - id: "cam_left"
    width: 1280
    height: 1024
    K:
      - [1050, 0, 640]
      - [0, 1050, 512]
      - [0, 0, 1]
    dist_coeffs: [-0.05, 0.1, 0, 0, 0]
    R:
      - [0.866, 0, 0.5]
      - [0, 1, 0]
      - [-0.5, 0, 0.866]
    t: [-1.37, 0, 2.0]

  - id: "cam_right"
    width: 1280
    height: 1024
    K:
      - [1050, 0, 640]
      - [0, 1050, 512]
      - [0, 0, 1]
    dist_coeffs: [-0.05, 0.1, 0, 0, 0]
    R:
      - [0.866, 0, -0.5]
      - [0, 1, 0]
      - [0.5, 0, 0.866]
    t: [1.37, 0, 2.0]
```

## 运行

```bash
python scripts/pipeline.py --config assets/stereo_tt_config.yaml
```

## 预期输出

```json
{
  "status": "ok",
  "states": [
    {"x": 0.0, "y": 0.15, "z": 1.5, "vx": 3.2, "vy": -0.1, "vz": -2.8, "timestamp": 0.000},
    {"x": 0.026, "y": 0.149, "z": 1.478, "vx": 3.1, "vy": -0.1, "vz": -2.9, "timestamp": 0.008}
  ],
  "stats": {
    "frames_processed": 5000,
    "avg_latency_ms": 6.8,
    "max_latency_ms": 9.1,
    "detection_rate": 0.98
  }
}
```

## 关键设计决策

- `dt: 0.008`：125 Hz 对应 8ms 时间步长
- `max_gap: 2`：125 FPS 下 2 帧 = 16ms，乒乓球飞行快，不允许长丢失
- `max_velocity: 300.0`：乒乓球在画面中移动较慢（远距离拍摄），300px/frame 足够
- 对侧放置：减少三角化 bias（DeepMind 论文关键发现，可降低 10 倍误差）
- 相机 R 矩阵：cam_left 绕 Y 轴 +30°，cam_right 绕 Y 轴 -30°，形成对侧视角

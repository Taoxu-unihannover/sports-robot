# Ball Perception 开发规范

> 本文档是编码规范、工程配置、测试标准和精度验证的单一参考源（Single Source of Truth）。

---

## 1. 编码规范

### 1.1 文件与命名

**文件扩展名**：Python 代码文件必须为 `.py`。

**命名规范**：

| 类型 | 规范 | 示例 |
|-----|------|------|
| 模块名 | 小写下划线 | `ball_detector`, `trajectory_tracker` |
| 类名 | 大驼峰 | `BallDetector`, `TrajectoryTracker` |
| 函数名 | 小写下划线 | `detect`, `update_2d`, `triangulate` |
| 变量名 | 小写下划线 | `confidence_threshold`, `max_gap` |
| 常量 | 全大写 | `MAX_DET`, `DEFAULT_DT` |

### 1.2 代码结构

每个模块的标准结构：

```python
"""
Module N: Module Name

Responsibility: ...
"""

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class ModuleResult:
    """模块输出数据结构"""
    ...


class ModuleClass:
    """模块主类"""

    def __init__(self, ...):
        """初始化，参数通过配置文件传入"""

    def process(self, ...) -> Optional[ModuleResult]:
        """核心处理方法"""

    def reset(self):
        """重置内部状态"""
```

**关键规范**：

| 规范 | 说明 |
|------|------|
| 类型注解 | 所有公开方法必须有完整类型注解 |
| 文档字符串 | 每个类和公开方法必须有 docstring |
| Lazy import | cv2, torch, ultralytics 等重依赖使用 lazy import |
| 参数化 | 所有参数通过 `__init__` 传入，禁止写死 |
| 无状态泄漏 | `reset()` 方法必须完全清除内部状态 |

### 1.3 模块间接口

**数据流**：

```
Image → Detector → (x, y, conf) → Tracker → (x_smooth, y_smooth) → Filter → BallState → Geometry → (X, Y, Z) → SpinEstimator → (wx, wy, wz)
```

**接口约定**：

| 接口 | 输入类型 | 输出类型 | 坐标系 |
|------|---------|---------|--------|
| Detector → Tracker | `Optional[DetectionResult]` | — | 像素坐标 |
| Tracker → Filter | `Optional[TrackPoint]` | — | 像素坐标 |
| Filter → Geometry | `BallState` | — | 归一化坐标 |
| Geometry → SpinEstimator | `np.ndarray` | — | 世界坐标 (米) |
| SpinEstimator → 外部 | `dict` | — | 世界坐标 (rad/s) |

---

## 2. 测试规范

### 2.1 单元测试

每个模块必须有独立的单元测试，覆盖：

- 正常输入输出
- 边界条件（None 输入、空输入、极值输入）
- 失败恢复（reset 后重新处理）
- 性能基准（延迟上限）

### 2.2 集成测试

流水线集成测试覆盖：

- 四模块串联端到端测试
- 检测丢失恢复测试
- 长时间运行稳定性测试

### 2.3 精度测试

| 模块 | 指标 | 目标值 | 测试方法 |
|------|------|--------|---------|
| Detector | mAP@0.5 | > 0.8 | 标注数据集 |
| Detector | 召回率 | > 0.9 | 标注数据集 |
| Tracker | 平滑度提升 | > 30% | 合成噪声轨迹 |
| Filter | 位置 RMSE | < 5 px | 合成轨迹 + 噪声 |
| Filter | 速度 RMSE | < 50 px/s | 合成轨迹 + 噪声 |
| Geometry | 重投影误差 | < 2 px | 标定板验证 |
| Geometry | 3D 位置误差 | < 5 cm | 已知位置目标 |
| SpinEstimator | 角速度置信度 | > 0.5 | 合成旋转轨迹 |
| SpinEstimator | Magnus 可检测转速 | > 5 rev/s | 已知旋转数据 |

---

## 3. 性能规范

| 模块 | 延迟目标 | 测量方法 |
|------|---------|---------|
| Detector (YOLO) | < 10 ms | GPU 推理时间 |
| Detector (HSV) | < 2 ms | CPU 处理时间 |
| Tracker | < 1 ms | update() 耗时 |
| Filter | < 0.5 ms | predict + update 耗时 |
| Geometry | < 1 ms | triangulate() 耗时 |
| SpinEstimator (Magnus) | < 1 ms | estimate() 耗时 |
| Pipeline (端到端) | < 20 ms | 单帧全流程耗时 |

---

## 4. 配置文件规范

```yaml
# config.yaml 标准结构
cameras:
  cam0:
    width: 1920
    height: 1080
    K: [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]
    dist_coeffs: [k1, k2, p1, p2, k3]
    R: [[r11, r12, r13], [r21, r22, r23], [r31, r32, r33]]
    t: [tx, ty, tz]

detector:
  type: yolo  # yolo | hsv | onnx
  model_path: yolov8n.pt
  confidence_threshold: 0.25
  input_size: 1024

tracker:
  window_size: 5
  max_gap: 3
  max_velocity: 500.0

filter:
  model: CV  # CV | CA | EKF
  dt: 0.008
  process_noise: 1.0
  measurement_noise: 10.0

geometry:
  method: DLT  # DLT | midpoint
  max_reprojection_error: 5.0

spin_estimator:
  method: trajectory_magnus  # trajectory_magnus | event_camera | marker_pose
  ball_radius: 0.02
  air_density: 1.225
  lift_coefficient: 0.4
```

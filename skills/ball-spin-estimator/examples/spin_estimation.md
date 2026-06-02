# 示例：事件相机旋转估计

## 场景

使用事件相机的异步事件流估计乒乓球的角速度。

## 代码

```python
import numpy as np
from skills.ball_spin_estimator.scripts.spin import EventCameraSpin

estimator = EventCameraSpin(
    ball_radius=0.02,
    focal_length=800.0,
    accumulation_window_ms=1.0,
)

events = np.array([
    [320.5, 240.3, 0.000001, 1],
    [321.0, 240.5, 0.000002, 1],
    [319.8, 239.9, 0.000003, -1],
])

result = estimator.estimate_angular_velocity(
    events=events,
    ball_center_2d=(320.0, 240.0),
    ball_radius_px=50.0,
)

if result:
    print(f"角速度: ({result.wx:.1f}, {result.wy:.1f}, {result.wz:.1f}) rad/s")
    print(f"转速: {result.spin_rpm:.0f} RPM")
    print(f"置信度: {result.confidence:.2f}")
```

## 示例：带标记球旋转估计

```python
from skills.ball_spin_estimator.scripts.spin import MarkerPoseSpin
import numpy as np

K = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=float)

estimator = MarkerPoseSpin(
    ball_radius=0.02,
    camera_matrix=K,
)

marker_3d = np.array([
    [0.01, 0.0, 0.0173],
    [-0.01, 0.0, 0.0173],
    [0.0, 0.01, 0.0173],
    [0.0, -0.01, 0.0173],
    [0.005, 0.005, -0.018],
    [-0.005, -0.005, -0.018],
])

for frame_idx in range(10):
    angle = frame_idx * 0.05
    c, s = np.cos(angle), np.sin(angle)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    rotated = (R @ marker_3d.T).T
    projected = (K @ rotated.T).T
    pts_2d = projected[:, :2] / projected[:, 2:3]

    result = estimator.update(pts_2d, marker_3d, timestamp=frame_idx * 0.008)
    if result and result.confidence > 0:
        print(f"帧 {frame_idx}: RPM={result.spin_rpm:.0f}, "
              f"ω=({result.wx:.1f}, {result.wy:.1f}, {result.wz:.1f})")
```

## 示例：轨迹倒推旋转（Magnus 效应）

```python
from skills.ball_spin_estimator.scripts.spin import TrajectoryMagnusSpin
import numpy as np

estimator = TrajectoryMagnusSpin(
    ball_radius=0.02,
    ball_mass=0.0027,
    lift_coefficient=0.2,
)

v_before = np.array([5.0, 0.0, -3.0])
v_after = np.array([5.8, 0.0, 2.7])
result = estimator.estimate_from_bounce(
    velocity_before=v_before,
    velocity_after=v_after,
    surface_normal=np.array([0.0, 0.0, 1.0]),
)

if result:
    print(f"弹跳推断转速: {result.spin_rpm:.0f} RPM")
    print(f"角速度: ({result.wx:.1f}, {result.wy:.1f}, {result.wz:.1f}) rad/s")
```

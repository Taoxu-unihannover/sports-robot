# 示例：双目 DLT 三角化

## 场景

从双目相机的 2D 检测结果恢复球的 3D 位置。

## 代码

```python
import numpy as np
from skills.ball_geometry.scripts.geometry import Triangulator, CameraConfig

cam0 = CameraConfig(
    camera_id="cam0",
    width=1920, height=1080,
    K=np.array([[1200, 0, 960], [0, 1200, 540], [0, 0, 1]]),
    dist_coeffs=np.zeros(5),
    R=np.eye(3),
    t=np.array([0, 0, 0]),
)

cam1 = CameraConfig(
    camera_id="cam1",
    width=1920, height=1080,
    K=np.array([[1200, 0, 960], [0, 1200, 540], [0, 0, 1]]),
    dist_coeffs=np.zeros(5),
    R=np.eye(3),
    t=np.array([2.74, 0, 0]),  # 2.74m 基线（乒乓球台宽度）
)

triangulator = Triangulator(
    camera_configs=[cam0, cam1],
    method="DLT",
)

point_3d = triangulator.triangulate({
    "cam0": (320.5, 240.3),
    "cam1": (315.2, 238.7),
})

print(f"3D 位置: ({point_3d[0]:.3f}, {point_3d[1]:.3f}, {point_3d[2]:.3f})")

# 计算重投影误差
error = triangulator.reprojection_error(point_3d, {
    "cam0": (320.5, 240.3),
    "cam1": (315.2, 238.7),
})
print(f"重投影误差: {error:.2f} px")
```

## 示例：Midpoint 三角化

```python
triangulator = Triangulator(
    camera_configs=[cam0, cam1],
    method="midpoint",  # 对噪声更鲁棒
)
```

## 示例：坐标变换

```python
from skills.ball_geometry.scripts.geometry import CoordinateTransformer

T_cam_to_world = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 1.5],
    [0, 0, 0, 1],
])

transformer = CoordinateTransformer(T_cam_to_world)
world_point = transformer.cam_to_world(point_3d)
print(f"世界坐标: ({world_point[0]:.3f}, {world_point[1]:.3f}, {world_point[2]:.3f})")
```

# 运动学建模示例

本示例展示如何用 `scripts/kinematic_model.py` 为击球机械臂建立最小运动学模型。

```python
from kinematic_model import PlanarArmModel

arm = PlanarArmModel(link_lengths=[0.45, 0.35, 0.18])
q = [0.2, -0.4, 0.7]
pose = arm.forward(q)
jacobian = arm.jacobian(q)
```

典型接入流程：

1. 将 URDF/标定得到的连杆长度或 DH 参数转成模型配置。
2. 用正运动学计算球拍中心位姿。
3. 用雅可比把关节速度映射为球拍线速度，用于击球速度约束。
4. 在控制层只暴露 `pose`、`jacobian`、`workspace_margin` 三类接口。


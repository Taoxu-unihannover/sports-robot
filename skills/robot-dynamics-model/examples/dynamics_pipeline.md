# 机器人动力学示例

本示例展示如何用 `scripts/robot_dynamics.py` 为击球机械臂建立动力学模型。

```python
from robot_dynamics import FrictionParams, LinkParams, PlanarDynamicsModel

links = [
    LinkParams(mass=2.0, length=0.45),
    LinkParams(mass=1.0, length=0.35),
    LinkParams(mass=0.3, length=0.18),
]

model = PlanarDynamicsModel(links, gravity=9.81)

q = [0.3, -0.5, 0.2]
qd = [0.5, -0.2, 0.1]
qdd = [1.0, -0.5, 0.3]

tau = model.inverse_dynamics(q, qd, qdd)
qdd_recovered = model.forward_dynamics(q, qd, tau)

friction = FrictionParams(
    viscous=np.array([0.1, 0.08, 0.05]),
    coulomb=np.array([0.05, 0.03, 0.02]),
)

tau_with_friction = model.inverse_dynamics(q, qd, qdd, friction=friction)

feasibility = model.torque_feasibility(q, qd, qdd, tau_max=[20.0, 15.0, 10.0])
```

典型接入流程：

1. 从 URDF 提取连杆质量、长度和惯量参数。
2. 用逆动力学计算前馈力矩，叠加反馈校正。
3. 用力矩可行性检查验证规划轨迹是否可执行。
4. 在线运行时，每步调用 ABA 预测下一时刻状态。

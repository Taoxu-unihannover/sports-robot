# MPC / LQR 跟踪示例

```python
from mpc_controller import finite_horizon_lqr

gains = finite_horizon_lqr(A, B, Q, R, horizon=20)
u = -gains[0] @ (x - x_ref)
```

该参考实现不处理约束，适合作为 acados/OSQP 等求解器接入前的基线控制器。


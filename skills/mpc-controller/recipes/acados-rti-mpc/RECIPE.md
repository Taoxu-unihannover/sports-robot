---
name: acados-rti-mpc
skill: mpc-controller
description: 使用 acados/RTI-SQP 思路实现球类机器人快速 NMPC。
source:
  repo: https://github.com/acados/acados
sport: [table_tennis, badminton, tennis]
difficulty: advanced
requires_training: false
---

# acados RTI-MPC Recipe

## 工作流

1. 将击球终端约束写成 OCP。
2. 离线生成求解器代码。
3. 在线每周期 warm-start 上一解。
4. 每周期执行一次 RTI/SQP 更新。
5. 超时或不可行时输出 last-safe trajectory。

## 适用场景

固定臂、直线平台、移动底盘和低维全身协调均可使用。若平台自由度过高，应先做任务空间降阶。


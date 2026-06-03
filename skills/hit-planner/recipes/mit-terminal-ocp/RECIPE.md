---
name: mit-terminal-ocp
skill: hit-planner
description: MIT 高速乒乓平台的终端拍面约束 OCP 击球规划。
source:
  paper_url: https://arxiv.org/html/2505.01617v1
sport: [table_tennis]
difficulty: intermediate
requires_training: false
---

# MIT Terminal OCP Recipe

## 思路

将击球任务写成终端约束：在 $t_h$ 时刻，拍面位置、姿态和速度满足目标，而不是强制整条轨迹贴合预设模板。

## 流程

1. 预测球路并生成候选 $t_h$。
2. 根据目标落点反推拍面法向和拍速。
3. 写入 OCP 终端条件。
4. 用固定时域 MPC 在执行中持续修正。
5. 若求解失败，退回上一条可行轨迹。


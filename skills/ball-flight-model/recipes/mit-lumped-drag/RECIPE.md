---
name: mit-lumped-drag
skill: ball-flight-model
description: MIT 高速乒乓平台风格的 lumped drag/反弹参数飞行预测，用于固定时域 MPC 前端。
source:
  paper_url: https://arxiv.org/html/2505.01617v1
sport: [table_tennis]
difficulty: intermediate
requires_training: false
---

# MIT Lumped Drag 飞行预测 Recipe

## 思路

将复杂空气动力学压缩为少量可辨识参数，在线只保留击球点预测所需状态，使 MPC 能在毫秒级响应来球更新。

## 步骤

1. 采集固定发球机/视觉轨迹日志。
2. 拟合阻力参数 $k_d$ 和台面反弹参数。
3. 在线积分球路，预测候选击球时刻。
4. 将击球时刻拍面状态作为 OCP/MPC 终端约束。
5. 每次换球、换台、换灯光后重新验证参数。

## 适用与限制

适用于飞行时间短、场地受控、球体模型较稳定的乒乓球。若来球旋转强或反弹误差显著，需要引入旋转状态或残差修正。


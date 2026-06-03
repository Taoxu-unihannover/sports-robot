---
name: mit-lightweight-arm
skill: high-speed-manipulator
description: MIT 高速轻量乒乓机械臂路线，强调低转子惯量、高加速度和终端约束。
source:
  paper_url: https://arxiv.org/html/2505.01617v1
sport: [table_tennis]
difficulty: advanced
requires_training: false
---

# MIT Lightweight Arm Recipe

## 思路

用低自由度、低惯量、高带宽硬件降低控制难度，使 OCP/MPC 能在击球窗口内稳定工作。

## 工程要点

1. 优先降低腕部和拍面附近质量。
2. 近端关节承担大力矩，远端关节承担精细姿态。
3. 避免高减速比带来的回差和弹性。
4. 单次命中和连续会话都要测热。


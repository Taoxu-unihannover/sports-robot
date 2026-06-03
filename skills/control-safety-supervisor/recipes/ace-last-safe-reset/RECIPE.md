---
name: ace-last-safe-reset
skill: control-safety-supervisor
description: Ace 风格的安全轨迹片段、碰撞检查和 reset trajectory 回退机制。
source:
  paper_url: https://arxiv.org/html/2505.06285v1
sport: [table_tennis]
difficulty: intermediate
requires_training: false
---

# Ace Last-safe Reset Recipe

## 思路

策略输出不直接驱动执行器，而是先形成短时轨迹段，经过碰撞和约束检查。若检查失败，则执行上一条已知安全的 reset trajectory。

## 流程

1. 接收策略目标。
2. 生成候选 segment trajectory。
3. 并行检查碰撞、限位和时序。
4. 通过则执行；失败则执行 reset。
5. 记录失败原因和回退轨迹 ID。


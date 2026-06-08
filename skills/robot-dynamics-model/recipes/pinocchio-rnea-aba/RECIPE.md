---
name: pinocchio-rnea-aba
skill: robot-dynamics-model
description: 使用 Pinocchio 实现机器人前向动力学(ABA)、逆动力学(RNEA)和质量矩阵(CRBA)。
source:
  docs: https://github.com/stack-of-tasks/pinocchio
  report: docs/tech-report/002-建模层.md
sport: [table_tennis, badminton, tennis]
difficulty: intermediate
requires_training: false
---

# Pinocchio ABA/RNEA 动力学 Recipe

## 目标

使用 Pinocchio 的 ABA/RNEA/CRBA 接口为球类机器人建立在线动力学模型，支撑前馈力矩计算、轨迹预测和力矩可行性检查。

## 工作流

1. 从 URDF 加载模型，构建 Pinocchio `Model` 和 `Data`。
2. 前向动力学：`pin.aba(model, data, q, v, tau)` → `ddq`，用于轨迹预测。
3. 逆动力学：`pin.rnea(model, data, q, v, ddq)` → `tau`，用于前馈力矩。
4. 质量矩阵：`pin.crba(model, data, q)` → `M(q)`，用于控制律设计。
5. 力矩可行性：用 RNEA 计算所需力矩，与电机限制比较。

## 验收指标

| 指标 | 建议 |
|---|---|
| ABA 单次耗时 | < 5 μs（6-7 DoF） |
| RNEA 单次耗时 | < 5 μs |
| 前向-逆动力学一致性 | qdd 误差 < 1e-10 |
| 质量矩阵对称正定 | 所有特征值 > 0 |

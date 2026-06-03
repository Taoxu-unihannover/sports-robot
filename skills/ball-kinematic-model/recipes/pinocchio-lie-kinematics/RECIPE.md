---
name: pinocchio-lie-kinematics
skill: ball-kinematic-model
description: 使用 Pinocchio/Lie-group 维护球类机器人坐标链、FK、Jacobian 和可达性检查。
source:
  docs: https://github.com/stack-of-tasks/pinocchio
  report: docs/tech-report/002-建模层.md
sport: [table_tennis, badminton, tennis]
difficulty: intermediate
requires_training: false
---

# Pinocchio / Lie-group 运动学建模 Recipe

## 目标

将 CAD/URDF/MJCF 中的机器人结构转化为统一坐标链，并向控制层输出末端位姿、雅可比和可达性判断。

## 工作流

1. 从 URDF 读取模型，明确 `base_link`、`ee_link`、`paddle_link`。
2. 为相机、场地和拍面建立外参文件，例如 `extrinsics.yaml`。
3. 计算 FK：输入 $q$，输出 ${}^WT_{paddle}$。
4. 计算 Jacobian：输入 $q$，输出 $J_{paddle}(q)$。
5. 对候选击球时刻 $t_h$ 执行 IK/OCP，检查关节、速度、碰撞和奇异性。

## 验收指标

| 指标 | 建议 |
|---|---|
| FK 数值一致性 | 单元测试误差 < 1e-6 |
| TCP 静态误差 | 显著小于拍面半径 |
| IK 成功率 | 在主击球区稳定通过 |
| Jacobian 条件数 | 奇异区可检测并降级 |


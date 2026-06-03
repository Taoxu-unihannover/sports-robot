---
name: mit-paddle-impact
skill: ball-impact-contact
description: 基于 MIT 高速乒乓平台的终端拍面速度/姿态约束和接触参数辨识方案。
source:
  paper_url: https://arxiv.org/html/2505.01617v1
sport: [table_tennis]
difficulty: intermediate
requires_training: false
---

# MIT Paddle Impact Recipe

## 目标

把期望出球方向、速度和拍型转化为击球时刻的拍面位置、法向和速度约束。

## 步骤

1. 固定来球速度和方向，采集不同拍面速度/角度下的出球结果。
2. 拟合法向恢复系数和切向摩擦参数。
3. 将击球约束写入 OCP 终端条件。
4. 用真实击球日志验证落点和出球速度误差。

## 验收

命中点预测误差应小于拍面半径的三分之一；接触参数换胶皮、换球后必须复验。


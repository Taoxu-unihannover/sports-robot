---
name: hamlet-mobile-manipulator
skill: mobile-base-executor
description: Hamlet 轮式底盘 + 上肢击球的移动操作路线。
source:
  paper: "Hamlet: A Mobile Manipulator for Robot Table Tennis, ICRA 2025"
sport: [table_tennis, badminton]
difficulty: advanced
requires_training: true
---

# Hamlet Mobile Manipulator Recipe

## 工作流

1. 底盘根据球路预测移动到优质击球区。
2. 上肢执行拍面末端约束。
3. 协调器同时读取底盘位姿、速度、滑移估计和上肢状态。
4. 若底盘未能及时到位，则缩拍、改防守或放弃击球。

## 验收

分别报告底盘定位误差、上肢 TCP 误差和最终击球误差，避免总命中率掩盖误差来源。


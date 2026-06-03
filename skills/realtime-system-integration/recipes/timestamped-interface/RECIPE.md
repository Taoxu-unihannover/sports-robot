---
name: timestamped-interface
skill: realtime-system-integration
description: 统一 BallState、RobotState、StrikePlan、JointCommand 的时间戳接口方案。
source:
  report: docs/tech-report/005-工程层.md
sport: [table_tennis, badminton, tennis]
difficulty: beginner
requires_training: false
---

# Timestamped Interface Recipe

## 消息最小集

- `BallState(stamp, frame_id, p, v, spin, covariance, confidence)`
- `RobotState(stamp, base_pose, base_twist, joint_state, health)`
- `StrikePlan(stamp, hit_time, hit_pose, paddle_normal, paddle_speed)`
- `JointCommand(stamp, mode, q_ref, dq_ref, tau_ff, limit_flags)`

## 失败策略

过期球状态不允许直接击球；应切换模型外推、保守击球或放弃。


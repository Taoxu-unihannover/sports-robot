---
name: log-replay-hil
skill: hil-verification
description: 球类机器人日志回放、HIL 和故障注入验证流程。
source:
  report: docs/tech-report/005-工程层.md
sport: [table_tennis, badminton, tennis]
difficulty: intermediate
requires_training: false
---

# Log Replay + HIL Recipe

## 流程

1. 记录感知、估计、规划、驱动反馈和安全事件。
2. 离线回放同一批球路。
3. 对比不同版本控制器的命中窗口和求解时间。
4. 注入延迟、丢包、编码器错误和电源故障。
5. 验证安全状态机不输出危险动作。


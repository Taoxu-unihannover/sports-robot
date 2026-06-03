---
name: control-stack
plugin: ball-control
description: 控制层完整工作流：击球规划 -> MPC/技能策略 -> 安全监督 -> 日志回放。
---

# Control Stack Recipe

1. 读取 `ModelState` 和球路预测。
2. 生成击球窗口和终端拍面目标。
3. 用 MPC/QP 求可行轨迹。
4. 策略层只输出技能或低维目标。
5. 安全层检查并执行 fallback。


---
name: 48v-power-chain
skill: power-electronics-bms
description: 中型球类机器人 48V 主母线、电池、预充、回生和隔离供电设计。
source:
  report: docs/tech-report/005-工程层.md
sport: [table_tennis, badminton, tennis]
difficulty: intermediate
requires_training: false
---

# 48V Power Chain Recipe

## 估算

若平均功耗 220 W、运行 45 min、DOD 0.8、电源效率 0.92、20% 裕量，电池需求约 270 Wh。

## 验收

1. 预充无冲击。
2. 急停能切断驱动使能。
3. 回生不会触发母线过压。
4. SoC 和相机不会因驱动瞬态复位。


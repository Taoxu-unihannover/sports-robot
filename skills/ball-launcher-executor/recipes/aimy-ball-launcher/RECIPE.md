---
name: aimy-ball-launcher
skill: ball-launcher-executor
description: AIMY 开源三轮发球机作为球类机器人训练、辨识和回归测试基础设施。
source:
  repo: https://github.com/robot-perception-group/aimy
sport: [table_tennis]
difficulty: intermediate
requires_training: false
---

# AIMY Ball Launcher Recipe

## 工作流

1. 标定轮速到球速/旋转的映射表。
2. 用数字触发对齐相机和控制日志。
3. 固定参数重复发球，测球速、方向和旋转离散度。
4. 将来球配置写入回归测试集。

## 验收

球速标准差、方向误差、触发抖动和卡球率都必须记录；否则来球源不可作为系统辨识输入。


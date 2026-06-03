---
name: ros2-lifecycle-tracing
skill: ros2-rtos-middleware
description: ROS 2 生命周期、launch_testing 和 ros2_tracing 的球类机器人 bring-up 流程。
source:
  docs: https://docs.ros.org
sport: [table_tennis, badminton, tennis]
difficulty: intermediate
requires_training: false
---

# ROS 2 Lifecycle + Tracing Recipe

## 流程

1. 用 lifecycle 节点管理未配置、待机、运行和退出。
2. 用 `launch_testing` 测试 bring-up 顺序。
3. 用 `ros2_tracing` 记录回调和 DDS 时序。
4. 伺服主环不放在 Linux 用户态闭环。
5. CI 中运行 `colcon test` 验证接口和故障码映射。


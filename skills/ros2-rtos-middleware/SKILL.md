---
name: ros2-rtos-middleware
description: 用于球类机器人的 ROS 2 / RTOS 中间件架构，覆盖 DDS QoS、实时调度、零拷贝传输、节点生命周期和通信拓扑设计。适用于用户需要实现 ROS 2 实时通信、DDS QoS 配置、RTOS 集成、零拷贝、节点生命周期；不用于控制算法或感知算法。
when_to_use: 用户提到 ROS 2、DDS、QoS、RTOS、实时、零拷贝、lifecycle node、通信拓扑、middleware、Xenomai、PREEMPT_RT 时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [system_requirements, node_specification]
  properties:
    system_requirements:
      type: object
      description: 系统实时性需求
      properties:
        control_period_ms: { type: number }
        max_latency_ms: { type: number }
        message_size_bytes: { type: integer }
        node_count: { type: integer }
    node_specification:
      type: array
      description: 节点规格列表
      items:
        type: object
        properties:
          name: { type: string }
          priority: { type: integer }
          cpu_affinity: { type: integer }
          period_ms: { type: number }
    transport:
      type: string
      enum: [udp, shared_memory, zero_copy]
      description: 传输方式，默认 shared_memory
output_schema:
  type: object
  required: [architecture, qos_profiles, scheduling_config]
  properties:
    architecture:
      type: object
      description: 推荐的通信架构
    qos_profiles:
      type: array
      description: 各话题的 QoS 配置
    scheduling_config:
      type: object
      description: RTOS 调度配置
    latency_estimate:
      type: object
      description: 各链路的延迟估计
---

# ROS 2 / RTOS 中间件架构

## 何时使用

当用户需要设计或配置球类机器人的实时通信中间件时使用。典型场景：

- ROS 2 节点拓扑和 QoS 设计
- RTOS 调度策略和优先级配置
- 零拷贝传输配置
- 节点生命周期管理
- 通信延迟分析和优化

不适用于：控制算法设计、感知算法设计。

## 输入约束

- control_period_ms 必须大于最大链路延迟的 3 倍
- 高优先级节点必须绑定独立 CPU 核心
- QoS 配置必须与数据特性匹配
- 零拷贝需要共享内存支持

## 执行步骤

### 步骤 1：通信拓扑设计

- 动作：根据节点规格设计通信拓扑
- 输入：node_specification, system_requirements
- 成功标准：拓扑满足延迟和带宽需求
- 失败处理：不满足时建议减少节点或优化数据流

### 步骤 2：QoS 配置

- 动作：为每个话题配置 QoS 策略
- 输入：数据特性 + 实时性需求
- 成功标准：QoS 配置满足实时性和可靠性需求
- 失败处理：冲突时优先保证实时性

### 步骤 3：调度配置

- 动作：配置 RTOS 调度策略和优先级
- 输入：节点优先级 + 周期 + CPU 核数
- 成功标准：所有节点在截止时间内完成
- 失败处理：不满足时建议增加 CPU 核或降低负载

## 输出格式

```json
{
  "architecture": {
    "topology": "star",
    "transport": "shared_memory",
    "discovery": "manual"
  },
  "qos_profiles": [
    {
      "topic": "/ball_state",
      "reliability": "best_effort",
      "history": "keep_last",
      "depth": 1,
      "deadline_ms": 8
    }
  ],
  "scheduling_config": {
    "scheduler": "SCHED_FIFO",
    "priorities": {"control": 90, "perception": 70, "planning": 50}
  },
  "latency_estimate": {
    "perception_to_control": 2.5,
    "control_to_actuation": 0.5
  }
}
```

## 可用方法与代表性系统

### 实时通信架构

| 层级 | 组件 | 延迟目标 |
|------|------|---------|
| 感知→控制 | 共享内存 + best_effort | < 3 ms |
| 控制→驱动 | 共享内存 + reliable | < 1 ms |
| 规划→控制 | UDP + best_effort | < 10 ms |
| 安全→所有 | 广播 + reliable | < 0.5 ms |

### QoS 策略选择

| 数据类型 | Reliability | History | Deadline |
|---------|-------------|---------|----------|
| 球状态 | best_effort | keep_last(1) | 8 ms |
| 关节指令 | reliable | keep_last(1) | 1 ms |
| 安全命令 | reliable | keep_all | 0.5 ms |
| 日志 | best_effort | keep_last(10) | - |

### RTOS 集成选项

| 选项 | 实时性 | 生态 | 难度 |
|------|--------|------|------|
| PREEMPT_RT | 好 | ROS 2 原生 | 低 |
| Xenomai | 优秀 | 需适配 | 高 |
| 双核分离 | 优秀 | 灵活 | 中 |

## 可用方案（Recipes）

| Recipe | 适用场景 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [eth-ros2-realtime](recipes/eth-ros2-realtime/RECIPE.md) | 全系统 | ETH ROS 2 架构 | advanced | 否 | 400Hz 状态估计 |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 延迟超限 | 端到端延迟 > deadline | 优化拓扑或降低负载 |
| QoS 不兼容 | 发布/订阅 QoS 冲突 | 调整为兼容配置 |
| CPU 过载 | 调度分析不通过 | 增加 CPU 核或降低频率 |
| 共享内存不足 | 内存分配失败 | 减少消息大小或使用 UDP |
| 节点崩溃 | lifecycle 状态异常 | 自动重启或降级 |

---
name: realtime-system-integration
description: 用于球类机器人的实时系统集成，覆盖端到端延迟分析、时钟同步、计算平台选型、GPU/CPU 资源分配和性能基准测试。适用于用户需要实现延迟分析、时钟同步、计算平台选型、性能基准；不用于控制算法或通信协议。
when_to_use: 用户提到延迟分析、端到端延迟、时钟同步、PTP、计算平台、GPU、CPU、性能基准、benchmark、实时集成时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [pipeline_spec, platform_spec]
  properties:
    pipeline_spec:
      type: array
      description: 处理管线各阶段规格
      items:
        type: object
        properties:
          name: { type: string }
          latency_budget_ms: { type: number }
          compute_type: { type: string, enum: [cpu, gpu, fpga] }
    platform_spec:
      type: object
      description: 计算平台规格
      properties:
        cpu_cores: { type: integer }
        gpu_model: { type: string }
        memory_gb: { type: number }
        os: { type: string }
    target_period_ms:
      type: number
      description: 目标控制周期（ms），默认 8
output_schema:
  type: object
  required: [feasibility, latency_breakdown, recommendations]
  properties:
    feasibility:
      type: string
      enum: [feasible, marginal, infeasible]
    latency_breakdown:
      type: array
      description: 各阶段延迟分析
      items:
        type: object
        properties:
          name: { type: string }
          estimated_ms: { type: number }
          budget_ms: { type: number }
          margin_ms: { type: number }
    total_latency_ms:
      type: number
    recommendations:
      type: array
      description: 优化建议
---

# 实时系统集成

## 何时使用

当用户需要分析或优化球类机器人的端到端实时性能时使用。典型场景：

- 端到端延迟预算分配
- 计算平台选型（CPU/GPU/FPGA）
- 时钟同步方案设计
- 性能基准测试和瓶颈分析

不适用于：控制算法设计、通信协议设计。

## 输入约束

- pipeline_spec 必须覆盖从感知到执行的完整链路
- 各阶段延迟预算之和必须小于目标周期
- 时钟同步精度必须优于最大允许延迟抖动
- GPU 推理延迟必须包含数据传输时间

## 执行步骤

### 步骤 1：延迟预算分配

- 动作：将目标周期分配给各处理阶段
- 输入：pipeline_spec, target_period_ms
- 成功标准：各阶段预算合理且有余量
- 失败处理：预算不足时建议降低目标频率或优化瓶颈

### 步骤 2：平台能力评估

- 动作：评估计算平台是否满足延迟需求
- 输入：platform_spec + 延迟预算
- 成功标准：各阶段在平台上可满足预算
- 失败处理：不满足时建议升级平台或优化算法

### 步骤 3：时钟同步与基准测试

- 动作：设计时钟同步方案并执行基准测试
- 输入：平台 + 管线 + 同步需求
- 成功标准：同步精度和实际延迟满足需求
- 失败处理：不满足时优化同步方案或调整预算

## 输出格式

```json
{
  "feasibility": "feasible",
  "latency_breakdown": [
    {"name": "camera_capture", "estimated_ms": 1.0, "budget_ms": 2.0, "margin_ms": 1.0},
    {"name": "detection", "estimated_ms": 2.0, "budget_ms": 3.0, "margin_ms": 1.0},
    {"name": "prediction", "estimated_ms": 1.5, "budget_ms": 2.0, "margin_ms": 0.5},
    {"name": "planning", "estimated_ms": 1.0, "budget_ms": 2.0, "margin_ms": 1.0},
    {"name": "control", "estimated_ms": 0.5, "budget_ms": 1.0, "margin_ms": 0.5}
  ],
  "total_latency_ms": 6.0,
  "recommendations": []
}
```

## 可用方法与代表性系统

### 典型延迟预算

| 阶段 | 乒乓球 (125Hz) | 羽毛球 (400Hz) |
|------|---------------|---------------|
| 相机采集 | 1-2 ms | 0.5-1 ms |
| 球检测 | 2-3 ms | 1-2 ms |
| 状态估计 | 0.5-1 ms | 0.2-0.5 ms |
| 飞行预测 | 0.5-1 ms | 0.2-0.5 ms |
| 击球规划 | 0.5-1 ms | 0.2-0.5 ms |
| MPC 求解 | 2-4 ms | 1-2 ms |
| 指令下发 | 0.2-0.5 ms | 0.1-0.2 ms |
| **总计** | **7-13 ms** | **3-7 ms** |

### 时钟同步方案

| 方案 | 精度 | 适用场景 |
|------|------|---------|
| NTP | ~1 ms | 非实时 |
| PTP (IEEE 1588) | ~1 μs | 实时系统 |
| 硬件触发 | ~1 ns | 高速同步 |
| 共享内存时间戳 | ~100 ns | 同机进程 |

### 计算平台选型

| 平台 | CPU | GPU | 适用场景 |
|------|-----|-----|---------|
| Jetson Orin NX | 8核 ARM | 1024 CUDA | 移动平台 |
| Intel NUC + RTX | x86 | 独立GPU | 固定基座 |
| Xilinx Zynq | ARM + FPGA | - | 极低延迟 |

## 可用方案（Recipes）

| Recipe | 适用场景 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [deepmind-end2end](recipes/deepmind-end2end/RECIPE.md) | 乒乓球 | DeepMind 端到端 | advanced | 是 | 125Hz 闭环 |
| [eth-400hz-pipeline](recipes/eth-400hz-pipeline/RECIPE.md) | 羽毛球 | ETH 400Hz 管线 | advanced | 否 | 400Hz 状态估计 |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 延迟超预算 | 实测 > budget | 优化瓶颈阶段或降低频率 |
| 平台能力不足 | 评估不通过 | 升级平台或简化算法 |
| 同步精度不足 | 抖动 > 允许值 | 优化同步方案或使用硬件触发 |
| GPU 推理延迟高 | 含传输超预算 | 使用 TensorRT 优化或换模型 |
| 内存不足 | 分配失败 | 减少缓冲区或优化数据结构 |

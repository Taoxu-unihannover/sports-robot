---
name: servo-drive-safety
description: 用于伺服驱动层的安全功能设计，包括 STO/SS1/SS2/SBC、安全转矩关断、制动器管理、过流保护和硬件看门狗。适用于用户需要实现伺服安全功能、STO、制动器、过流保护、硬件看门狗；不用于软件层安全逻辑或控制算法。
when_to_use: 用户提到伺服安全、STO、SS1、SS2、SBC、制动器、过流保护、看门狗、IEC 61800-5-2、safe torque off 时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [safety_request, drive_status]
  properties:
    safety_request:
      type: string
      enum: [normal_operation, safe_stop_1, safe_stop_2, safe_torque_off, safe_brake_control]
      description: 安全功能请求
    drive_status:
      type: object
      description: 驱动器状态
      properties:
        motor_temperature: { type: number }
        current_rms: { type: number }
        current_peak: { type: number }
        bus_voltage: { type: number }
        encoder_valid: { type: boolean }
        brake_engaged: { type: boolean }
        watchdog_ok: { type: boolean }
output_schema:
  type: object
  required: [safety_response, drive_command]
  properties:
    safety_response:
      type: string
      enum: [executing, completed, fault, rejected]
    drive_command:
      type: object
      description: 驱动器控制命令
      properties:
        torque_enable: { type: boolean }
        brake_command: { type: string, enum: [engage, release, hold] }
        current_limit: { type: number }
    fault_code:
      type: string
      description: 故障码（若有）
---

# 伺服驱动与安全功能

## 何时使用

当用户需要设计或实现伺服驱动层的安全功能时使用。典型场景：

- STO（安全转矩关断）功能实现
- SS1/SS2（安全停止）功能实现
- SBC（安全制动控制）功能实现
- 过流保护和温度监控
- 硬件看门狗和双通道安全

不适用于：软件层安全逻辑（用 control-safety-supervisor）、控制算法设计。

## 输入约束

- STO 请求必须通过双通道硬件信号
- 制动器释放前必须确认电机已建立保持力矩
- 过流保护阈值必须小于电机和驱动器的最大承受值
- 看门狗超时时间必须小于机械系统危险响应时间

## 执行步骤

### 步骤 1：安全请求验证

- 动作：验证安全请求的合法性和优先级
- 输入：safety_request, drive_status
- 成功标准：请求合法且可执行
- 失败处理：请求非法时拒绝并报告 fault

### 步骤 2：安全功能执行

- 动作：根据请求类型执行对应安全功能
- 输入：验证后的请求 + 驱动器状态
- 成功标准：安全功能在规定时间内完成
- 失败处理：执行超时或失败时进入 fault 状态

### 步骤 3：状态确认与反馈

- 动作：确认安全功能执行结果并反馈
- 输入：执行结果
- 成功标准：状态与请求一致
- 失败处理：状态不一致时标记 fault

## 输出格式

```json
{
  "safety_response": "completed",
  "drive_command": {
    "torque_enable": false,
    "brake_command": "engage",
    "current_limit": 0
  },
  "fault_code": null
}
```

## 可用方法与代表性系统

### IEC 61800-5-2 安全功能

| 功能 | 描述 | 典型响应时间 |
|------|------|-------------|
| STO | 安全转矩关断，立即断电 | < 10 ms |
| SS1 | 安全停止1，减速后断电 | 取决于减速时间 |
| SS2 | 安全停止2，减速后保持位置 | 取决于减速时间 |
| SBC | 安全制动控制，控制制动器 | < 50 ms |

### 关键设计原则

- **双通道**：安全信号必须双通道冗余
- **正逻辑**：安全信号断开 = 触发安全功能
- **制动器优先**：STO 后必须立即制动
- **温度监控**：过温时降低电流或停止

## 可用方案（Recipes）

| Recipe | 适用场景 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [ace-estop-sto](recipes/ace-estop-sto/RECIPE.md) | 急停+STO | IEC 61800-5-2 | intermediate | 否 | STO < 10ms |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 双通道不一致 | 通道信号不匹配 | 进入 fault，断电制动 |
| 制动器失效 | 制动器未响应 | 保持电机保持力矩，报警 |
| 过流触发 | 电流超限 | 立即断电，报告 fault |
| 过温 | 温度超限 | 降低电流或停止 |
| 看门狗超时 | 超时未喂狗 | 进入 STO |
| 编码器异常 | 编码器数据无效 | 进入 SS2 或 STO |

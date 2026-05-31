---
name: ball-tracker
description: 用于球类运动的短轨迹跟踪，对连续帧的 2D 检测结果做时序平滑，输出去噪后的 2D 轨迹。支持滑动窗口平滑、TrackNet 风格热图跟踪、速度异常值剔除。适用于用户需要实现球类跟踪、轨迹平滑、遮挡处理；不用于多目标跟踪（MOT）或通用目标跟踪。
when_to_use: 用户提到球跟踪、轨迹平滑、时序关联、TrackNet、ball tracking、trajectory smoothing、遮挡处理时触发。
version: 1.0.0
allowed-tools:
  - filesystem.read
  - filesystem.write
  - terminal.run
input_schema:
  type: object
  required: [x, y, timestamp]
  properties:
    x: { type: number, description: 当前帧球心 x 坐标，可为 null }
    y: { type: number, description: 当前帧球心 y 坐标，可为 null }
    timestamp: { type: number, description: 帧时间戳 }
    confidence: { type: number, description: 检测置信度 }
output_schema:
  type: object
  required: [x, y, timestamp, confidence]
  properties:
    x: { type: number, description: 平滑后 x 坐标 }
    y: { type: number, description: 平滑后 y 坐标 }
    timestamp: { type: number }
    confidence: { type: number }
---

# 球类短轨迹跟踪器

## 何时使用

当用户需要对连续帧的球类检测结果做时序平滑和轨迹关联时使用。典型场景：

- 消除单帧检测的抖动噪声
- 在短暂遮挡期间预测球的位置
- 过滤速度异常的误检
- 为 Kalman 滤波器提供更稳定的 2D 观测

不适用于：多目标跟踪（MOT）、行人跟踪、车辆跟踪。

## 输入约束

- 每帧输入 (x, y, timestamp)，x/y 可为 None（表示检测丢失）
- 需要连续帧输入，帧间时间间隔应相对稳定
- max_velocity 参数需根据实际场景标定（像素/秒）

## 执行步骤

### 步骤 1：速度校验

- 动作：计算当前检测与上一帧的位移速度
- 输入：当前 (x, y) 和历史最后有效位置
- 成功标准：速度 < max_velocity 阈值
- 失败处理：超速检测视为异常值，丢弃当前检测，进入 gap 模式

### 步骤 2：滑动窗口更新

- 动作：将有效检测加入滑动窗口，用指数加权做平滑
- 输入：当前有效检测 + 历史窗口
- 成功标准：输出平滑后的 (x, y)
- 失败处理：窗口为空时返回 None

### 步骤 3：Gap 管理

- 动作：检测丢失时递增 gap 计数器
- 输入：连续丢失帧数
- 成功标准：gap < max_gap 时继续预测
- 失败处理：gap >= max_gap 时清空历史，重置 tracker

## 输出格式

```json
{
  "x": 320.8,
  "y": 241.1,
  "timestamp": 0.032,
  "confidence": 0.88
}
```

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 连续检测丢失 | gap >= max_gap | 清空历史窗口，重置 tracker |
| 速度异常 | velocity > max_velocity | 丢弃当前检测，使用预测值 |
| 窗口数据不足 | len(history) < 2 | 返回原始检测值 |
| 预测不可用 | 历史点 < 2 | 返回 None |

---
name: eth-shuttle-aero
skill: ball-flight-model
description: ETH 腿足羽毛球系统风格的机载视觉噪声 + 羽毛球高阻力轨迹预测。
source:
  repo: https://github.com/leggedrobotics/shuttle_detection
sport: [badminton]
difficulty: advanced
requires_training: false
---

# ETH Shuttle Aero 轨迹预测 Recipe

## 思路

羽毛球减速极快，轨迹预测要同时处理高阻力、机载视觉延迟和观测噪声。在线估计器应以视觉观测异步更新，以物理模型在观测间隙外推。

## 步骤

1. 接收机载双目输出的 3D 羽毛球观测和时间戳。
2. 对观测延迟做回滚更新。
3. 用高阻力或指数衰减模型预测短时轨迹。
4. 输出可拦截轨迹的注册时刻与剩余运动时间。
5. 在仿真中注入真实视觉噪声，避免策略只适应真值。

## 关键指标

| 指标 | 说明 |
|---|---|
| 感知频率 | 机载视觉常见 60 Hz |
| 状态估计 | 可高于感知频率，例如 400 Hz |
| 控制更新 | 读取估计结果，通常 100 Hz 左右 |


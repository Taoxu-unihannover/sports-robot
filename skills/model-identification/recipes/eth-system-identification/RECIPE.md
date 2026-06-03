---
name: eth-system-identification
skill: model-identification
description: ETH 羽毛球系统风格的部署前系统辨识和真实噪声回灌流程。
source:
  repo: https://github.com/leggedrobotics/shuttle_detection
sport: [badminton]
difficulty: advanced
requires_training: false
---

# ETH System Identification Recipe

## 工作流

1. 采集真实相机观测、机器人状态和控制输入。
2. 分别拟合传感器噪声、延迟、运动模型和接触/执行残差。
3. 将辨识结果写入仿真环境，使训练策略看到部署噪声。
4. 用独立验证集评估跨场景退化率。

## 关键原则

不要只拟合一个“阻力参数”。移动平台系统需要同时拟合感知噪声、时间延迟、本体运动误差和执行器残差。


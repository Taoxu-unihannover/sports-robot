---
name: latent-humanoid-tennis
skill: whole-body-executor
description: LATENT 风格的人形网球动作原语、仿真训练和真实部署。
source:
  paper_url: https://arxiv.org/html/2309.03315v2
sport: [tennis]
difficulty: advanced
requires_training: true
---

# LATENT Humanoid Tennis Recipe

## 思路

将人类动作片段拆成准备、引拍、挥拍、收拍、复位等原语，再适配到人形机器人。

## 接口

- 高层：来球状态、击球目标、动作原语
- 中层：身体朝向、支撑状态、拍面约束
- 低层：关节跟踪、安全限位、跌倒保护


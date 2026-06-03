---
name: hitter-wholebody-rl
skill: skill-policy-controller
description: HITTER 风格的模型式击球规划 + 全身 RL tracking。
source:
  paper_url: https://arxiv.org/abs/2505.22974
sport: [table_tennis]
difficulty: advanced
requires_training: true
---

# HITTER Whole-body RL Recipe

## 思路

模型规划器输出击球位置、速度和时机；全身 RL 控制器负责让人形身体完成目标并保持稳定。

## 落地建议

1. 不让 RL 直接解决球路预测。
2. 上层输出物理含义明确的低维目标。
3. 下层策略只负责跟踪、协调和动作自然性。
4. 安全层检查关节、碰撞、支撑和跌倒风险。


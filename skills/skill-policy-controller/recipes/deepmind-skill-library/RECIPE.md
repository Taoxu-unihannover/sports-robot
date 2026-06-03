---
name: deepmind-skill-library
skill: skill-policy-controller
description: DeepMind 竞技乒乓系统风格的高层技能选择器 + 低层技能库。
source:
  paper_url: https://www.nature.com/articles/s41586-026-10338-5
sport: [table_tennis]
difficulty: advanced
requires_training: true
---

# DeepMind Skill Library Recipe

## 思路

低层技能负责具体击球动作，高层根据来球、对手和回合上下文选择技能。这样可把“如何挥拍”和“何时用哪种打法”拆开。

## 接口

| 接口 | 字段 |
|---|---|
| skill input | 球状态、目标落点、拍面约束 |
| skill status | 可执行性、预计完成时间、失败概率 |
| post action | reset trajectory、下一拍准备姿态 |


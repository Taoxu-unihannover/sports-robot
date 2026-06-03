---
name: ace-spin-state-fusion
skill: model-uncertainty-risk
description: Ace 风格的位置状态与旋转状态异步融合，并将置信度传递给控制层。
source:
  paper_url: https://arxiv.org/html/2505.06285v1
sport: [table_tennis]
difficulty: advanced
requires_training: false
---

# Ace Spin State Fusion Recipe

## 思路

位置由多 APS 相机估计，旋转由事件相机估计。两者频率、延迟和噪声不同，必须分别维护置信度，再在控制层统一使用。

## 步骤

1. 为位置状态 $p,v$ 和旋转状态 $\omega$ 分别维护时间戳与协方差。
2. 迟到观测按自身时间戳做回放更新。
3. 控制层读取同一预测时刻下的 $p,v,\omega,\Sigma$。
4. 若旋转置信度低，则降级为位置驱动回击策略。


---
name: modeling-stack
plugin: ball-modeling
description: 建模层完整工作流：坐标链 -> 飞行预测 -> 接触模型 -> 参数辨识 -> 风险输出。
---

# Modeling Stack Recipe

1. 冻结坐标系和 `ModelState`。
2. 选择球路预测模型。
3. 建立拍面/台面/地面接触参数。
4. 用日志进行参数辨识。
5. 输出击球候选和风险界给控制层。


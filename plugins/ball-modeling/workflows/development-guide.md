# Ball Modeling 开发规范

## 模块边界

建模层只负责把状态、参数和物理约束转成预测模型，不直接产生执行器命令。

## 接口约定

```
PerceptionState -> FlightModel / KinematicModel / ContactModel -> PredictionBundle -> Control
```

## 测试标准

- 正运动学雅可比应通过有限差分校验。
- 飞行模型应验证重力、阻力和击球平面穿越。
- 接触模型应验证法向反射、移动球拍和地面弹跳。
- 风险模型应验证协方差传播和门控行为。

## 性能目标

短时预测 50 步应在控制周期内完成；参数辨识不得阻塞实时链路。

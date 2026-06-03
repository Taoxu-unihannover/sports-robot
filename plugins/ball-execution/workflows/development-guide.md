# Ball Execution 开发规范

## 模块边界

执行层负责把控制命令映射到硬件命令，并执行限幅、联锁和状态回报。

## 接口约定

```
ExecutionCommand -> Launcher / Manipulator / Base / WholeBody -> ServoSafety -> Hardware
```

## 测试标准

- 发球机映射要验证速度回推和旋转轮差。
- 机械臂轨迹要验证终点、速度和加速度限制。
- 底盘控制要验证角度包裹和前进命令。
- 伺服安全要验证位置、速度、力矩和温度降额。

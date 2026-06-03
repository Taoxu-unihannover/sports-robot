# Ball Engineering 开发规范

## 模块边界

工程层负责实时预算、中间件生命周期、电源安全、HIL 验证和发布维护。

## 接口约定

```
RuntimeConfig -> IntegrationChecks -> HILRegression -> ReleasePackage
```

## 测试标准

- 延迟预算要有总延迟和分模块延迟。
- ROS2/RTOS 配置要验证 QoS 与生命周期状态机。
- 电源预算要验证总电流、总功率和欠压状态。
- 发布包要验证版本兼容和标定 checksum。

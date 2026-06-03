---
name: engineering-stack
plugin: ball-engineering
description: 工程层完整工作流：时序接口 -> ROS2/RTOS -> 电源总线 -> HIL -> 发布维护。
---

# Engineering Stack Recipe

1. 冻结接口字段、时钟和时序预算。
2. 分离 ROS 2、RTOS 和安全 MCU。
3. 设计 48V 电源、BMS、预充和回生。
4. 建立 HIL、日志回放和故障注入。
5. 绑定 release、标定、BOM 和维护 SOP。


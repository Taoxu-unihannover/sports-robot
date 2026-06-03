# ROS2 / RTOS 中间件参考

- ROS 2 managed lifecycle nodes.
  - 适合控制启动顺序、故障恢复和配置热更新。

- micro-ROS.
  - 参考代码: https://github.com/micro-ROS
  - 适合 MCU/RTOS 与 ROS2 主机通信。

- DDS QoS policies.
  - 需要根据传感器流、控制命令和状态回传分别配置 reliability、deadline、history。


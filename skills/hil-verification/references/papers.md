# HIL 验证参考

- Log replay for robotics regression testing.
  - 将现场日志固定为回归用例，能有效防止算法升级破坏实时链路。

- Gazebo / MuJoCo / Isaac Sim HIL practice.
  - 参考代码: https://github.com/google-deepmind/mujoco
  - 可用仿真执行器替代真实硬件，保留上层软件栈。

- ROS bag and MCAP.
  - 适合记录时间戳、消息载荷和跨模块链路延迟。


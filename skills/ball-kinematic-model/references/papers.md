# 建模层运动学参考

- Pinocchio: A fast forward and inverse dynamics library for robotics.
  - 参考代码: https://github.com/stack-of-tasks/pinocchio
  - 适合实现 Lie group 位姿、雅可比、质心与动力学接口。

- RBDL: Rigid Body Dynamics Library.
  - 参考代码: https://github.com/rbdl/rbdl
  - 适合轻量级刚体运动学和动力学验证。

- DeepMind robotic table tennis system.
  - 使用工业机械臂和高速相机，需要低延迟球拍位姿预测。
  - 运动学层重点是球拍中心 frame、工作空间边界和速度映射。


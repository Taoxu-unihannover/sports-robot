# 机器人动力学参考

- Pinocchio: Fast forward and inverse dynamics for poly-articulated systems.
  - 参考代码: https://github.com/stack-of-tasks/pinocchio
  - ABA/RNEA/CRBA 的推荐实现，支持 Lie-group 和自动微分。

- Featherstone, R., *Rigid Body Dynamics Algorithms.*
  - Springer, 2008.
  - ABA/RNEA 的理论基础，第 7-8 章详述算法推导。

- MIT lightweight robot table tennis.
  - 5 DoF 轻量化结构降低动力学复杂度，固定时域 MPC 快速修正末端轨迹。
  - 降阶动力学模型在实时控制中的典型应用。

- DeepMind robot table tennis.
  - 工业机械臂动力学建模，前馈力矩+反馈校正。
  - 强调动力学模型在高速运动中的数值稳定性。

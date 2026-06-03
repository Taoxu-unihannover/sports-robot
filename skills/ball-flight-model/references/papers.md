# 飞行动力学参考

- MIT / robotic table tennis: lumped drag model for table tennis trajectory prediction.
  - 常用简化形式为重力 + 二次阻力，足够支撑短时击球规划。

- ETH legged badminton robot: shuttlecock aerodynamic model.
  - 羽毛球阻力大、速度衰减快，常需要强阻力和经验参数辨识。
  - 参考代码: https://github.com/leggedrobotics

- SpinDOE / Magnus-effect spin estimation.
  - 旋转可通过轨迹弯曲反推，模型层需暴露 Magnus acceleration 和参数辨识接口。


# 球拍/地面接触参考

- MIT robotic table tennis impact model.
  - 常用法向恢复系数 + 切向阻尼/摩擦简化球拍碰撞。

- Table tennis ball impact dynamics literature.
  - 重点参数包括 restitution、tangential damping、spin transfer 和 paddle normal。

- MuJoCo / Drake contact models.
  - 参考代码: https://github.com/google-deepmind/mujoco
  - 适合在仿真中验证接触参数和能量边界。


# 旋转估计参考论文

## 事件相机旋转估计

- **Table tennis ball spin estimation with an event camera** (2024): Gossard, Krismer, Ziegler, Tebbe, Zell (University of Tübingen), CVPRW 2024
  - 论文: https://arxiv.org/abs/2404.09870
  - Ordinal Time Surface 编码事件流为时间面
  - 事件光流提取 + 角速度回归
  - 球面光流场与角速度的几何约束 v_flow = omega x r
  - 旋转幅度 MAE: 10.7 ± 17.3 rps，旋转轴 MAE: 32.9 ± 38.2°
  - 代码可用性: 论文有详细方法描述和伪代码，但未公开完整源码。核心算法可按论文复现。

- **Ace: An Elite Badminton Robot** (2026): Sony AI / Nature
  - 论文: https://www.nature.com/articles/s41586-026-10338-5
  - 3 套事件视觉 gaze-control system（可转镜面 + 可调焦镜头 + 事件传感器）
  - 低延迟 CNN：事件流累积为 ~1ms 事件帧，轻量 CNN 回归角速度，延迟 2-3 ms
  - 高精度 CMax：对比度最大化框架，搜索最优旋转参数，约 10 ms
  - 角速度估计频率 400-700 Hz，平均误差 24.8 rad/s
  - 代码可用性: 完全闭源，Nature 论文仅描述架构和性能指标。

- **A multi-modal table tennis robot system** (2023): Ziegler, Gossard, Vetter, Tebbe, Zell (University of Tübingen), CoRL 2023 Workshop
  - 论文: https://arxiv.org/abs/2310.19062
  - 多模态感知系统（4 帧相机 + 2 事件相机）
  - SpinDOE 旋转估计 + SNN 事件检测
  - 代码可用性: 未公开完整源码。

## 带标记球几何姿态估计

- **SpinDOE: A ball spin estimation method for table tennis robot** (2023): Gossard, Tebbe, Ziegler, Zell (University of Tübingen), IROS 2023
  - 论文: https://arxiv.org/abs/2303.03879
  - 球面点模式识别（CNN）+ 几何哈希匹配 + PnP 姿态估计
  - 相邻帧相对旋转 → 角速度
  - 姿态估计误差 2.4°，旋转估计相对误差 < 1%
  - 350 fps 相机可测量最高 175 rps 旋转
  - 开放数据集：乒乓球轨迹含位置和旋转标注
  - 代码可用性: 论文提到 project page 提供数据集，核心代码未完全开源。

- **Sound-Based Spin Estimation in Table Tennis** (2024): Gossard, Schmalzl, Ziegler, Zell (University of Tübingen), IEEE Star 2025
  - 论文: https://arxiv.org/abs/2409.11760
  - 基于声音的旋转分类（辅助视觉方法）
  - 公开数据集和代码
  - 代码可用性: 数据集和代码公开。

## 轨迹倒推旋转（Magnus 效应）

- **A Novel Trajectory-Based Ball Spin Estimation Method for Table Tennis Robot** (2024): Wang, Sun et al., IEEE TIE 2024
  - 论文: https://ieeexplore.ieee.org/document/10342178
  - 基于飞行轨迹的旋转估计，非线性回归 + 最优估计
  - 代码可用性: 代码未公开。

- **Magnus Effect General Reference**
  - F_Magnus = C_L * (4/3) * pi * r^3 * rho * (omega x v)
  - 乒乓球 Magnus 加速度通常 < 1 m/s^2（重力 9.8 m/s^2）
  - 位置误差 5mm 时信号可能被噪声淹没
  - 弹跳行为辅助：上旋球弹跳后加速，下旋球减速

- **Learning Racket-Ball Bounce Dynamics Across Diverse Rubbers for Robotic Table Tennis** (2026): Gossard (University of Tübingen)
  - 论文: https://arxiv.org/abs/2604.11349
  - 10 种球拍配置的弹跳动力学建模（含旋转）
  - Gaussian Process 建模弹跳后速度和旋转预测
  - 代码可用性: 未公开。

## 相关基础理论

- **Event Camera Fundamentals**: Gallego et al. (2020), "Event Cameras: A Survey"
  - 事件相机原理、时间面、事件帧
  - 异步事件流处理方法

- **PnP Problem**: Gao et al. (2003), "Complete Solution Classification for the Perspective-Three-Point Problem"
  - PnP 问题求解方法
  - RANSAC + PnP 鲁棒估计

- **Rotation Representation**: Axis-angle, Rodrigues, Quaternion
  - 旋转矩阵到角速度的转换
  - delta_R = R_{t+1} * R_t^{-1}
  - omega = axis(delta_R) * angle(delta_R) / dt

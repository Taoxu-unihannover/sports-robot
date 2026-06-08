---
name: casadi-nls-identification
skill: model-identification
description: 使用 CasADi+IPOPT 进行批量非线性最小二乘参数辨识，自动生成解析雅可比，支持物理约束和分速度段拟合。
source:
  docs: https://web.casadi.org
  report: docs/tech-report/002-建模层.md
sport: [table_tennis, badminton, tennis]
difficulty: advanced
requires_training: false
---

# CasADi NLS 参数辨识 Recipe

## 思路

批量非线性最小二乘（NLS）是离线参数辨识的最强方法，但手写雅可比矩阵极其繁琐且容易出错。CasADi 通过符号计算图自动生成高精度稀疏雅可比，IPOPT 利用该雅可比做高斯-牛顿迭代，收敛速度和精度远超有限差分方案。

## 核心原理

### 问题形式化

给定 $M$ 帧飞行轨迹观测 $\{y_k\}$，拟合物理参数 $\theta = [k_d, k_m, e_n, \mu, \ldots]$：

$$\theta^* = \arg\min_\theta \sum_{k=1}^{M} \lVert y_k - \hat y_k(\theta) \rVert_W^2 \quad \text{s.t.} \quad \theta_{\min} \le \theta \le \theta_{\max}$$

其中 $\hat y_k(\theta)$ 是用当前参数通过飞行模型前推得到的预测观测。

### CasADi 自动微分优势

| 方法 | 雅可比计算时间 | 精度 | 开发成本 |
|---|---|---|---|
| 有限差分 | ~5 ms | 一阶近似，受步长影响 | 低 |
| CasADi 自动微分 | ~0.05 ms | 机器精度 | 低 |
| 手写解析雅可比 | ~0.02 ms | 机器精度 | 极高 |

CasADi 的速度接近手写解析式，但开发成本与有限差分相当。

### 分速度段拟合

MIT 发现阻力系数 $k_d$ 在不同球速范围内近似恒定但值不同。建议分速度段拟合：

| 速度段 | $k_d$ 范围 | 典型场景 |
|---|---|---|
| $< 5$ m/s | 0.01–0.05 | 慢速回球 |
| 5–10 m/s | 0.05–0.15 | 中速对拉 |
| $> 10$ m/s | 0.15–0.50 | 高速扣杀 |

## 步骤

1. **数据准备**：采集固定发球机/视觉轨迹日志，按球速分段组织。
2. **符号建模**：用 CasADi `SX` 构建飞行模型的符号计算图，参数 $\theta$ 作为符号变量。
3. **轨迹前推**：用 RK4 积分符号化飞行模型，生成预测观测 $\hat y_k(\theta)$。
4. **雅可比自动生成**：CasADi 自动计算 $\frac{\partial \hat y}{\partial \theta}$，利用稀疏性只计算非零元素。
5. **IPOPT 求解**：将 NLS 问题交给 IPOPT，利用解析雅可比做高斯-牛顿迭代。
6. **物理约束**：加入参数边界约束（如 $e_n \in [0,1]$，$k_d > 0$），确保辨识结果物理可行。
7. **交叉验证**：用独立验证集评估参数泛化能力，检查跨速度段外推误差。

## 关键参数

| 参数 | 建议值 | 说明 |
|---|---|---|
| 优化容差 | 1e-6 | IPOPT 最优性容差 |
| 最大迭代 | 200 | IPOPT 迭代上限 |
| 数据窗口 | 5–30 s | 每段轨迹时长 |
| 速度分段数 | 2–4 | 按球速分几段拟合 |
| 权重矩阵 $W$ | $\Sigma_y^{-1}$ | 观测协方差逆 |

## 验收指标

| 指标 | 建议 |
|---|---|
| 一步预测误差 | < 2% NRMSE |
| 参数重复性 | 跨批次标准差 < 5% |
| 验证集外推误差 | < 10% |
| 求解收敛率 | > 99% |
| 雅可比精度 | 有限差分对比误差 < 1e-8 |

---
name: mujoco-compliant-contact
skill: ball-impact-contact
description: MuJoCo 风格的顺应接触模型与参数连续化，用罚函数+阻尼替代刚性冲量，使 OCP 可获得光滑梯度。
source:
  docs: https://mujoco.org
  report: docs/tech-report/002-建模层.md
sport: [table_tennis, badminton, tennis]
difficulty: advanced
requires_training: false
---

# MuJoCo 顺应接触 Recipe

## 思路

刚性冲量模型（$v_n^+ = -e_n v_n^-$）在碰撞瞬间产生速度跳变，不可导，无法为基于梯度的优化器（如 CasADi+IPOPT）提供光滑雅可比。MuJoCo 采用罚函数+阻尼的顺应接触模型，接触力连续可导，天然适合 OCP 和参数辨识中的梯度下降。

## 核心原理

### 顺应接触力模型

法向接触力：

$$f_n = k_n \cdot \max(0, d) + d_n \cdot (-\dot d)$$

其中 $d$ 为穿透深度（球表面到接触面的距离，负值表示穿透），$k_n$ 为法向刚度，$d_n$ 为法向阻尼。

切向摩擦力（平滑近似）：

$$f_t = -\mu \cdot f_n \cdot \tanh\left(\frac{v_t}{v_{\text{thresh}}}\right)$$

其中 $v_t$ 为切向滑移速度，$v_{\text{thresh}}$ 控制摩擦过渡的平滑度。

### 参数连续化

| 参数 | 刚性模型 | 顺应模型 | 连续化效果 |
|---|---|---|---|
| 恢复系数 $e_n$ | 离散跳变 | 由 $k_n, d_n$ 隐式决定 | 碰撞速度连续过渡 |
| 摩擦 $\mu$ | 库仑锥（不连续） | $\tanh$ 平滑近似 | 滑移-粘滞连续过渡 |
| 接触检测 | 穿透/非穿透二值 | 罚函数连续 | 碰撞时刻可导 |

### solref/solimp 参数化

MuJoCo 通过 `solref` 和 `solimp` 控制接触特性：

- `solref = [timeconst, dampratio]`：时间常数和阻尼比，等价于调节 $k_n$ 和 $d_n$。
- `solimp = [dmin, dmax, width, midpoint, power]`：阻抗曲线参数，控制接触力随穿透深度的非线性关系。

## 步骤

1. **离线参数标定**：用高速相机采集球触台/触拍过程，拟合 $k_n, d_n, \mu$。
2. **仿真验证**：在 MuJoCo 中搭建球-台/球-拍接触场景，调节 `solref/solimp` 使反弹行为与真实数据匹配。
3. **梯度验证**：确认接触力对状态和参数的雅可比可用 CasADi 自动微分获得，且数值稳定。
4. **OCP 集成**：将顺应接触模型嵌入轨迹优化，替代刚性冲量，使优化器在碰撞区域也能收敛。
5. **Sim-to-Real 校准**：对比仿真与真实的反弹后速度/角度误差，微调接触参数。

## 关键参数

| 参数 | 建议值 | 说明 |
|---|---|---|
| 法向刚度 $k_n$ | 1e4–1e6 N/m | 越大越接近刚性，但数值刚性增加 |
| 法向阻尼 $d_n$ | 10–1000 N·s/m | 控制能量耗散，等价于恢复系数 |
| 摩擦系数 $\mu$ | 0.2–0.6 | 台面/拍面/地面分别标定 |
| 滑移阈值 $v_{\text{thresh}}$ | 0.01–0.1 m/s | 控制 $\tanh$ 过渡锐度 |
| 积分步长 | 0.1–1 ms | 顺应接触需要小步长保证稳定性 |

## 验收指标

| 指标 | 建议 |
|---|---|
| 反弹后速度误差 | < 5%（vs 真实数据） |
| 接触力雅可比精度 | 有限差分对比误差 < 1e-4 |
| OCP 在碰撞区收敛率 | > 95% |
| Sim-to-Real 反弹角度偏差 | < 3° |

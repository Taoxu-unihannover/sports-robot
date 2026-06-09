# Ball Modeling — 球类建模开发 Team

> 端到端建模层开发环境。含 7 个专业 Skill、3 个 Agent、完整工作流和可运行预测 pipeline，包括网球动力学建模。

## 架构概览

```
ball-modeling/
├── plugin.json
├── AGENTS.md
├── quickstart.md
├── init.sh
├── assets/config.yaml
├── agents/
│   ├── modeling-architect.md
│   ├── modeling-developer.md
│   └── modeling-reviewer.md
├── scripts/pipeline.py
├── tests/regression.py
├── references/papers.md
├── examples/predict_hit.md
└── workflows/
```

## 七模块 Skills

| Skill | 职责 | 输入 | 输出 |
|-------|------|------|------|
| `ball-kinematic-model` | 机械臂/球拍运动学 | 关节角、结构参数 | 球拍位姿、雅可比、工作空间余量 |
| `ball-flight-model` | 球飞行预测 | 位置、速度、旋转 | 未来轨迹、平面穿越点 |
| `ball-impact-contact` | 球拍/地面接触 | 入射速度、球拍速度、法向 | 出射速度 |
| `model-identification` | 参数辨识 | 轨迹日志、控制日志 | 阻力、映射、在线参数 |
| `model-uncertainty-risk` | 不确定性风险 | 残差、协方差、时序 | 门控结果、风险分数 |
| `tennis-ball-dynamics-sim` | 网球动力学仿真 | 初始状态、速度 | 网球轨迹、目标位置 |
| `mujoco-tennis-world-builder` | MuJoCo 网球世界 | 球场配置 | MJCF XML + 资产 |

## 网球动力学建模

### 网球飞行模型

网球飞行受以下力影响：

- 重力：F_g = -mg ẑ
- 空气阻力：F_d = -½ρCdA|v|v
- Magnus 效应：F_m = ½ρCmA|v|(ω × v̂)

参数：
- 网球质量 m = 0.057 kg
- 网球直径 d = 0.067 m
- 空气密度 ρ = 1.225 kg/m³
- 阻力系数 Cd ≈ 0.55
- Magnus 系数 Cm ≈ 0.33

### MuJoCo 中的网球动力学

在 MuJoCo XML 中定义网球体：

```xml
<body name="tennis_ball" pos="0 0 1">
  <joint type="free"/>
  <geom type="sphere" size="0.0335" mass="0.057" rgba="0.8 0.8 0 1"/>
</body>
```

### 简化动力学模型（非物理引擎）

用于 RL 环境中的快速网球运动模拟：

- 恒定速度直线运动：goal += velocity × dt
- 无空气阻力、无 Magnus 效应
- 网球可飞出场地边界（触发终止条件）
- 初始速度范围：vx ∈ [-1, 1], vy ∈ [-2, -0.5]

### 域随机化参数

| 参数 | 标称值 | 随机范围 | 说明 |
|---|---|---|---|
| 网球初始位置 | 对侧场地 | ±0.5m 均匀 | 发球位置变化 |
| 网球初始速度 | [-1,1]×[-2,-0.5] | ±30% | 击球力量变化 |
| 地面摩擦 | 0.8 | [0.6, 1.0] | 场地条件变化 |
| 空气阻力 | 0.55 | [0.4, 0.7] | 环境条件变化 |

## 三 Agent 分工

### Modeling Architect

- 职责：模型选型、坐标系与接口设计、参数来源规划、网球动力学建模。
- 输出：`DESIGN.md` + `PLAN.md`。
- 调用时机：建模层新建、物理模型变更、跨层接口冻结。

### Modeling Developer

- 职责：实现模型、配置、参数辨识、预测 pipeline 和测试、网球动力学实现。
- 输出：Python 模块、配置文件、回归测试报告。
- 调用时机：设计确定后、模型误差修复、参数更新。

### Modeling Reviewer

- 职责：审查物理一致性、数值稳定性、实时性和控制接口风险、动力学验证。
- 输出：`REVIEW.md`、风险清单、上线检查项。
- 调用时机：代码提交前、参数发布前、系统联调前。

## 工作流

```
Step 1: 需求分析 -> Architect 输出 DESIGN.md + PLAN.md
Step 2: 参数来源确认 -> Developer 建立配置和辨识路径
Step 3: 代码实现 -> Developer 实现预测/接触/风险接口
Step 4: 回归测试 -> Developer 运行 tests/regression.py
Step 5: 模型审查 -> Reviewer 检查误差、边界和跨层接口
```

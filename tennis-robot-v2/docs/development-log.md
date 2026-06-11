# tennis-robot-v2 开发日志

> 创建日期：2026-06-09
> 最后更新：2026-06-11
> 项目类型：ball-project-assimilator 对 dynamic-tennis-v2 的吸收与超越产物

## 1. 项目背景

tennis-robot-v2 是 `ball-project-assimilator` 插件执行"开源球类机器人项目吸收与超越计划"的产物。

### 1.1 四阶段工作流执行记录

| 阶段 | 状态 | 说明 |
|------|------|------|
| 阶段 1：技术栈拆解 | ✅ 完成 | 扫描 dynamic-tennis-v2，输出 stack_map + skill_gap |
| 阶段 2：项目复现 | ✅ 完成 | 创建 tennis-robot-v2，通过 smoke test + 训练 + 评估 |
| 阶段 3：横向评测 | ✅ 完成 | 对比 v1/v2/dynamic-tennis-v2 三版本 |
| 阶段 4：最优组合 | ✅ 完成 | 选择 dynamic-tennis 的奖励函数 + sports-robot 的工程栈 |

### 1.2 吸收来源

| 来源项目 | 吸收内容 |
|----------|----------|
| dynamic-tennis-v2 | 预测性导航奖励、拦截点计算、velocity_alignment 奖励 |
| sports-robot | from_xml_string 加载、标准化环境封装 |

## 2. 技术栈拆解结果

### 2.1 扫描结果

```
python plugins/ball-project-assimilator/scripts/scan_project.py \
  --project_path dynamic-tennis-v2 \
  --project_name dynamic-tennis-v2 \
  --domain tennis
```

**输出**：15 个模块，15 个已覆盖，0 个部分覆盖，0 个未覆盖

### 2.2 关键技术栈识别

| 技术栈 | 模块 | 映射 Skill | 覆盖 |
|--------|------|-----------|------|
| 仿真 | MuJoCo 网球世界 | mujoco-tennis-world-builder | ✅ |
| 感知 | 真值状态观测 | truth-state-policy-input | ✅ |
| 训练 | SB3 SAC/PPO | sb3-rl-training-runner | ✅ |
| 评估 | 策略评估 | mujoco-policy-evaluator | ✅ |
| 可视化 | Web 轨迹可视化 | robot-trajectory-web-visualizer | ✅ |

### 2.3 Skill 缺口

| 缺口 | 补充方案 | 优先级 |
|------|----------|--------|
| 预测性导航奖励 | 从 dynamic-tennis-v2 沉淀到 gymnasium-mujoco-env-builder | P0 |
| 拦截点计算 | 新增 recipe | P0 |
| velocity_alignment 奖励 | 扩展 reward_config | P0 |

## 3. 项目复现过程

### 3.1 创建 tennis-robot-v2

基于 dynamic-tennis-v2 的技术栈分析，通过 sports-robot skills 生成复现项目。

### 3.2 v2 关键改进（来自阶段 3 横向评测结论）

| 改进项 | v1 问题 | v2 改进 | 来源 |
|--------|---------|---------|------|
| 奖励函数 | 只有基础距离奖励 | 添加预测性导航奖励 | dynamic-tennis-v2 |
| velocity_alignment | 无 | 添加速度对齐奖励 (weight=500) | dynamic-tennis-v2 |
| relative_speed | 无 | 添加拦截性奖励 (weight=20) | dynamic-tennis-v2 |
| 拦截点计算 | 无 | 添加 _calculate_interception_point | dynamic-tennis-v2 |
| control_cost | 0.001 (过高) | 0.0005 | dynamic-tennis-v2 |
| step_penalty | 无 | -0.3 | dynamic-tennis-v2 |
| XML 加载 | 临时目录拷贝 | from_xml_string 优先 | sports-robot |
| Real 模式感知 | 无 | HSV 检测 + 立体深度 + Kalman 滤波 | dynamic-tennis-v2 |

### 3.3 可运行性验证

```
[1/5] Creating environment... ✅
[2/5] Running check_env... ✅ PASSED
[3/5] Testing reset... ✅
[4/5] Testing step... ✅
[5/5] Running short episode... ✅
ALL TESTS PASSED
```

## 4. 性能验证结果

### 4.1 Sim 模式（真值推理）评测

| 模型 | success_rate | avg_reward | std_reward | vs Baseline |
|------|-------------|------------|------------|-------------|
| **Baseline (1M SAC)** | 86.7% | 14145.5 | 4525.0 | 100% |
| Reproduction (100K PPO) | 20.0% | -9772.8 | 6030.3 | 23.1% |
| **Enhanced (best_model)** | **93.3%** | **14992.2** | **3751.0** | **107.7%** ✅ |

**结论：增强版成功超越 Baseline！**
- 成功率: 93.3% > 86.7% (+7.6%)
- 平均奖励: 14992 > 14145 (+6.0%)
- 奖励标准差: 3751 < 4525 (-17.1%)，更稳定

### 4.2 Real 模式（图像推理）评测

| 模型 | success_rate | avg_reward | avg_detection_rate | sim→real gap |
|------|--------------|------------|-------------------|--------------|
| Baseline (sim) | 86.7% | 14145.5 | 100% | - |
| **Enhanced (real)** | **0.0%** | 549.3 | **75.8%** | **-86.7%** |

**Real 模式瓶颈分析：**
1. 观测重建误差导致TTC计算不准确
2. 训练-推理模式不匹配（sim训练 → real推理）
3. 检测率不足75.8%，回退到Kalman引入误差
4. 需要实现domain randomization训练

### 4.3 关键发现

#### 发现 1：课程学习导致训练不稳定

| 配置 | success_rate 波动 | 结果 |
|------|-------------------|------|
| **无课程学习（Baseline）** | 稳定 80-95% | ✅ 收敛 |
| 有课程学习 | 22%-60% 大幅波动 | ❌ 不稳定 |

**结论：Baseline 明确禁用课程学习 (`ENABLE_CURRICULUM=0`)，使用固定高难度训练。**

#### 发现 2：固定学习率优于衰减学习率

- Baseline 使用固定 lr=5e-4
- 衰减学习率可能导致后期策略震荡
- 推荐使用固定学习率

#### 发现 3：更大网络有助于收敛

| 网络架构 | 成功率 | avg_reward |
|----------|--------|------------|
| [256,256] | 40.0% | 8392.1 |
| [512,512] | **93.3%** | **14992.2** |

## 5. Real 模式感知链路

### 5.1 完整推理管线

```
MuJoCo 仿真引擎
    ↓
双目相机渲染 (320x240 offscreen)
    ↓
HSV 球检测 (SimBallDetector)
  - H: 40-80, S: 40-150, V: 100-200
  - 球检测率: 75.8%
    ↓
SGBM 立体深度估计
  - 基线: 0.24m, crop模式
  - 无WLS滤波
    ↓
坐标变换 (base_link)
    ↓
Kalman 滤波 (位置平滑 + 时延补偿)
    ↓
观测向量重建
    ↓
PPO 策略网络
    ↓
3维动作 (vx, vy, wz)
```

### 5.2 Real 模式优化路径

| 瓶颈 | 优化方案 | 优先级 | 预期效果 |
|------|----------|--------|----------|
| 球检测率 65-80% | YOLOv8 替代 HSV | P0 | 远距离小目标检测率显著提升 |
| 深度估计精度 | 安装 opencv-contrib 启用 WLS | P0 | 深度估计精度提升 30%+ |
| sim→real gap | Domain randomization 训练 | P0 | 策略对检测失败更鲁棒 |
| Kalman 速度收敛慢 | 使用位置差分替代 Kalman 速度 | P1 | TTC 计算精度提升 |

## 6. 代码修复记录

| 文件 | 修复内容 | 原因 |
|------|----------|------|
| `summit_xls.urdf.xml` | 相机朝向 +Y 方向 | 相机朝向 -Y 但网球在 +Y 方向 |
| `real_mode_perception.py` | HSV 参数调整 S_MIN=40 | 仿真网球像素 S=49-67 |
| `tennis_navigation_v2_env.py` | Real 模式感知初始化 | 相机渲染器和观测构建器 |

## 7. 文档清单

| 文件 | 说明 |
|------|------|
| [development-log.md](development-log.md) | 本文件，详细开发过程记录 |
| [code-level-verification-report.md](code-level-verification-report.md) | 功能验证详情 |
| [dynamic-tennis-v2-baseline-metrics.json](dynamic-tennis-v2-baseline-metrics.json) | 原始项目性能 (1M步SAC) |
| [tennis-robot-v2-baseline-metrics.json](tennis-robot-v2-baseline-metrics.json) | 复现项目性能 (100K步PPO) |

## 8. 结论与下一步行动

### 8.1 总体结论

**tennis-robot-v2 吸收验证任务：**
- ✅ **Sim 模式：成功超越 Baseline** (93.3% > 86.7%)
- ❌ **Real 模式：待优化** (Gap=86.7%)

### 8.2 下一步行动

1. **P0**: 实现 domain randomization 训练
2. **P0**: 提升球检测率至 90%+（YOLOv8）
3. **P1**: 启用 WLS 滤波提升深度精度

---

*文档更新：2026-06-11*
*验证方：sports-robot (ball-project-assimilator)*

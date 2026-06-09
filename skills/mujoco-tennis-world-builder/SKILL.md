---
name: mujoco-tennis-world-builder
description: 生成可加载的 MuJoCo 球类机器人仿真世界，管理 MJCF XML 模板、mesh 资产路径、碰撞体、相机、传感器和目标体。适用于用户需要搭建 MuJoCo 仿真场景、定义球场/目标/障碍物、配置机器人模型；不用于纯 Gymnasium 环境逻辑或 RL 训练。
---

# MuJoCo 球类机器人世界构建

## 用途

从 MJCF XML 模板和 mesh 资产生成可加载的 MuJoCo 仿真场景，支持球类机器人（网球、乒乓球、羽毛球等）的仿真需求。管理场景中的地面、球场标记、目标体（球）、机器人模型、相机和传感器。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| sport_type | string | 是 | 球类类型：tennis, badminton, table_tennis |
| court_dimensions | dict | 否 | 球场尺寸 {length, width}，默认使用标准尺寸 |
| robot_model | string | 否 | 机器人模型类型：mecanum, differential, arm |
| include_ball | bool | 否 | 是否包含动态球体，默认 True |
| ball_radius | float | 否 | 球半径，默认按球类类型 |
| include_camera | bool | 否 | 是否包含仿真相机，默认 False |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| 主 XML 文件 | assets/{sport_type}_world.xml | 可直接加载的 MuJoCo 场景 |
| 资产引用 | assets/ | mesh 文件、子 XML 引用 |
| 加载测试 | tests/ | 验证 XML 可加载、无缺失资产 |

## 执行步骤

### 步骤 1：确定球场参数

根据 sport_type 选择标准球场尺寸，或使用用户提供的自定义尺寸：

| 球类 | 标准半场长度 | 标准宽度 |
|---|---|---|
| tennis | 11.885m | 8.23m |
| badminton | 6.7m | 3.05m (双打 6.1m) |
| table_tennis | 1.37m | 0.7625m |

### 步骤 2：生成 MJCF XML 结构

标准 XML 层次：

```xml
<mujoco model="{sport_type}_world">
  <include file="assets/assets.xml"/>       <!-- compiler, textures, meshes -->
  <worldbody>
    <include file="assets/scene.xml"/>       <!-- ground, ball, court markers, light -->
    <include file="assets/robot.xml"/>       <!-- 机器人模型 -->
  </worldbody>
  <include file="assets/actuator.xml"/>      <!-- 执行器定义 -->
</mujoco>
```

### 步骤 3：生成场景组件

- **地面**：平面 geom，带 checker 纹理
- **目标球体**：freejoint + sphere geom，半径按球类设定
- **球场标记**：角标、底线标记（cylinder/box geom，contype=0）
- **光照**：directional light

### 步骤 4：生成机器人模型

根据 robot_model 选择：
- **mecanum**：4 轮全向底盘，含 roller 子体
- **differential**：2 轮差速底盘
- **arm**：多关节机械臂

### 步骤 5：验证

- `mujoco.MjModel.from_xml_path(xml_file)` 无报错
- 所有 mesh 文件路径可解析
- qpos/qvel 布局与文档一致

## 失败处理

| 失败场景 | 处理策略 |
|---|---|
| mesh 文件缺失 | 生成占位几何体并输出警告 |
| XML 解析错误 | 检查 include 路径和语法 |
| 球体初始化异常 | 确认 freejoint 和初始 qpos |

## 验证方式

```python
import mujoco
model = mujoco.MjModel.from_xml_path("assets/tennis_world.xml")
data = mujoco.MjData(model)
mujoco.mj_step(model, data)
print(f"nq={model.nq}, nv={model.nv}, nu=model.nu")
```

## 可选 Recipes

| Recipe | 说明 |
|---|---|
| tennis-mecanum-world | 网球 + 麦克纳姆底盘场景 |
| badminton-differential-world | 羽毛球 + 差速底盘场景 |

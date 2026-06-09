# dynamic-tennis 技术栈图谱

> 扫描日期：2026-06-09T17:39:58.465613
> 项目类型：tennis
> 项目路径：dynamic-tennis
> 项目仓库：https://github.com/Taoxu-unihannover/dynamic-tennis

## 模块总览

| 类型 | 模块数 | 已覆盖 | 部分覆盖 | 未覆盖 |
|---|---|---|---|---|
| simulation | 2 | 2 | 0 | 0 |
| perception | 5 | 5 | 0 | 0 |
| modeling | 3 | 3 | 0 | 0 |
| control | 2 | 2 | 0 | 0 |
| execution | 1 | 1 | 0 | 0 |
| training | 1 | 1 | 0 | 0 |
| engineering | 1 | 1 | 0 | 0 |

## 模块详情

### mujoco-tennis-world-builder (simulation)

- **覆盖状态**: full
- **映射 Skill**: mujoco-tennis-world-builder
- **源文件**: 161 个
  - `README.md`
  - `env-cpu.yaml`
  - `env-gpu.yaml`
  - `models\arm.urdf.xacro`
  - `models\common.urdf.xacro`
  - `models\components.urdf.xacro`
  - `mujoco_car_navigation_tutorial.ipynb`
  - `mujoco_mecanum\robots\summit_xl_description\assets\assets.xml`
  - `mujoco_mecanum\robots\summit_xl_description\assets\basic_scene.xml`
  - `mujoco_mecanum\robots\summit_xl_description\assets\summit_xls.urdf.xml`
  - ... 及其他 151 个

### mujoco-policy-evaluator (simulation)

- **覆盖状态**: full
- **映射 Skill**: mujoco-policy-evaluator
- **源文件**: 3 个
  - `README.md`
  - `scripts\test_mecanum_navigation.py`
  - `web_visualization\README_Web_Visualization.md`

### sim-camera-perception-input (perception)

- **覆盖状态**: full
- **映射 Skill**: sim-camera-perception-input
- **源文件**: 58 个
  - `env-cpu.yaml`
  - `env-gpu.yaml`
  - `meshes\Ball.usd`
  - `models\arm.urdf.xacro`
  - `models\meshes\firstFingerLink.DAE`
  - `models\meshes\forceTorqueSensor.DAE`
  - `models\meshes\palm.DAE`
  - `models\meshes\secondFingerLink.DAE`
  - `models\meshes\thirdFingerLink.DAE`
  - `models\meshes\wamBase.dae`
  - ... 及其他 48 个

### truth-state-policy-input (perception)

- **覆盖状态**: full
- **映射 Skill**: truth-state-policy-input
- **源文件**: 11 个
  - `scripts\envs\3Dreacher\completenavigator_v0.py`
  - `scripts\envs\armreacher\armreacher_v0.py`
  - `scripts\envs\armreacher\armreacher_v1.py`
  - `scripts\envs\mecanum_navigator\mecanum_navigator_static_tenis copy.py`
  - `scripts\envs\mecanum_navigator\mecanum_navigator_v1.py`
  - `scripts\envs\navigaterobot\navigaterobot_v0.py`
  - `scripts\envs\navigaterobot\navigaterobot_v1.py`
  - `scripts\envs\navigaterobot\navigaterobot_v2.py`
  - `scripts\envs\navigaterobot\navigaterobot_v3.py`
  - `scripts\envs\stroke\stroke_v0.py`
  - ... 及其他 1 个

### ball-detector (perception)

- **覆盖状态**: full
- **映射 Skill**: ball-detector
- **源文件**: 4 个
  - `env-cpu.yaml`
  - `env-gpu.yaml`
  - `scripts\cfg\mecanum_navigator.yaml`
  - `scripts\test_mecanum_navigation.py`

### ball-state-estimator (perception)

- **覆盖状态**: full
- **映射 Skill**: ball-state-estimator
- **源文件**: 14 个
  - `assets\gifs\armreacher.gif`
  - `models\meshes\wamBase.dae`
  - `models\meshes\wamForeArmLink4.DAE`
  - `models\meshes\wamShoulderLink1.DAE`
  - `models\meshes\wamUpperArmInShoulderLink.DAE`
  - `models\meshes\wamUpperArmLink3.DAE`
  - `models\meshes\wamUpperWristYawLink.DAE`
  - `mujoco_mecanum\robots\summit_xl_description\meshes\bases\summit_xl_chassis_copy.dae`
  - `mujoco_mecanum\robots\summit_xl_description\meshes\structures\structure_ptz_rgbd_gps.stl`
  - `mujoco_mecanum\robots\summit_xl_description\meshes\wheels\omni_wheel_1.dae`
  - ... 及其他 4 个

### ball-tracker (perception)

- **覆盖状态**: full
- **映射 Skill**: ball-tracker
- **源文件**: 21 个
  - `models\arm.urdf.xacro`
  - `models\common.urdf.xacro`
  - `models\components.urdf.xacro`
  - `mujoco_car_navigation_tutorial.ipynb`
  - `robots\archives\ant.xml`
  - `robots\archives\cassie.xml`
  - `robots\archives\wam7.xml`
  - `robots\archives\wam7_test.xml`
  - `robots\archives\wam7_test_v4.xml`
  - `robots\archives\wam7_test_v8.xml`
  - ... 及其他 11 个

### ball-flight-model (modeling)

- **覆盖状态**: full
- **映射 Skill**: ball-flight-model
- **源文件**: 2 个
  - `scripts\misc\trajectory_estimator.py`
  - `scripts\test_mecanum_navigation.py`

### ball-impact-contact (modeling)

- **覆盖状态**: full
- **映射 Skill**: ball-impact-contact
- **源文件**: 4 个
  - `mujoco_mecanum\robots\summit_xl_description\urdf\bases\summit_xl_base.urdf.xacro`
  - `mujoco_mecanum\robots\summit_xl_description\urdf\bases\summit_xl_hls_base.urdf.xacro`
  - `mujoco_mecanum\robots\summit_xl_description\urdf\bases\summit_xls_base.urdf.xacro`
  - `robots\archives\include_wam_7dof_wam_bhand_Chain.xml`

### ball-kinematic-model (modeling)

- **覆盖状态**: full
- **映射 Skill**: ball-kinematic-model
- **源文件**: 2 个
  - `mujoco_mecanum\robots\summit_xl_description\launch\summit_xl_state_robot.launch`
  - `robots\archives\include_wam_7dof_wam_bhand_Chain.xml`

### mpc-controller (control)

- **覆盖状态**: full
- **映射 Skill**: mpc-controller
- **源文件**: 2 个
  - `models\meshes\images\firstFingerLink2_512.tif`
  - `navigation_plots\navigation_episode_2.png`

### control-safety-supervisor (control)

- **覆盖状态**: full
- **映射 Skill**: control-safety-supervisor
- **源文件**: 6 个
  - `scripts\cfg\wam7_3Dreacher.yaml`
  - `scripts\cfg\wam7_armreacher.yaml`
  - `scripts\envs\3Dreacher\helper.py`
  - `scripts\envs\armreacher\armreacher_v1.py`
  - `scripts\envs\stroke\stroke_v0.py`
  - `scripts\envs\stroke\stroke_v1.py`

### mobile-base-executor (execution)

- **覆盖状态**: full
- **映射 Skill**: mobile-base-executor
- **源文件**: 119 个
  - `README.md`
  - `mujoco_mecanum\robots\summit_xl_description\assets\assets.xml`
  - `mujoco_mecanum\robots\summit_xl_description\assets\basic_scene.xml`
  - `mujoco_mecanum\robots\summit_xl_description\assets\summit_xls.urdf.xml`
  - `mujoco_mecanum\robots\summit_xl_description\assets\summit_xls_actuator.xml`
  - `mujoco_mecanum\robots\summit_xl_description\launch\summit_xl_rviz.launch`
  - `mujoco_mecanum\robots\summit_xl_description\launch\summit_xl_state_robot.launch`
  - `mujoco_mecanum\robots\summit_xl_description\meshes\bases\ext\summit_xl_hl_ext_chassis.dae`
  - `mujoco_mecanum\robots\summit_xl_description\meshes\bases\ext\summit_xl_hl_ext_chassis.stl`
  - `mujoco_mecanum\robots\summit_xl_description\meshes\bases\graveyard\summit_xl_chassis.stl`
  - ... 及其他 109 个

### sb3-rl-training-runner (training)

- **覆盖状态**: full
- **映射 Skill**: sb3-rl-training-runner
- **源文件**: 4 个
  - `env-cpu.yaml`
  - `env-gpu.yaml`
  - `scripts\test_mecanum_navigation.py`
  - `scripts\train_mecanum_navigator.py`

### robot-trajectory-web-visualizer (engineering)

- **覆盖状态**: full
- **映射 Skill**: robot-trajectory-web-visualizer
- **源文件**: 24 个
  - `README.md`
  - `env-cpu.yaml`
  - `env-gpu.yaml`
  - `mujoco_car_navigation_tutorial.ipynb`
  - `mujoco_mecanum\robots\summit_xl_description\assets\basic_scene.xml`
  - `navigation_plots\navigation_episode_1.png`
  - `navigation_plots\navigation_episode_10.png`
  - `navigation_plots\navigation_episode_2.png`
  - `navigation_plots\navigation_episode_3.png`
  - `navigation_plots\navigation_episode_4.png`
  - ... 及其他 14 个

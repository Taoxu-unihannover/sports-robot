# dynamic-tennis-v2 技术栈图谱

> 扫描日期：2026-06-09T22:42:23.639591
> 项目类型：tennis
> 项目路径：/home/xutao/文档/sports-robot/dynamic-tennis-v2
> 项目仓库：

## 模块总览

| 类型 | 模块数 | 已覆盖 | 部分覆盖 | 未覆盖 |
|---|---|---|---|---|
| simulation | 2 | 2 | 0 | 0 |
| perception | 5 | 5 | 0 | 0 |
| modeling | 3 | 3 | 0 | 0 |
| control | 1 | 1 | 0 | 0 |
| execution | 1 | 1 | 0 | 0 |
| training | 1 | 1 | 0 | 0 |
| engineering | 1 | 1 | 0 | 0 |

## 模块详情

### mujoco-tennis-world-builder (simulation)

- **覆盖状态**: full
- **映射 Skill**: mujoco-tennis-world-builder
- **源文件**: 143 个
  - `.gitignore`
  - `README.md`
  - `docs/PROJECT_OVERVIEW.md`
  - `docs/VELOCITY_CONTROL_ANALYSIS.md`
  - `docs/VIDEO_TELEMETRY_GUIDE.md`
  - `docs/guides/SPEED_SCALING_FIX.md`
  - `mujoco_mecanum/README.md`
  - `mujoco_mecanum/export_summit_video.py`
  - `mujoco_mecanum/robots/summit_xl_description/CMakeLists.txt`
  - `mujoco_mecanum/robots/summit_xl_description/assets/assets.xml`
  - ... 及其他 133 个

### mujoco-policy-evaluator (simulation)

- **覆盖状态**: full
- **映射 Skill**: mujoco-policy-evaluator
- **源文件**: 2 个
  - `scripts/test_mecanum_navigation.py`
  - `scripts/test_summit_catcher.py`

### sim-camera-perception-input (perception)

- **覆盖状态**: full
- **映射 Skill**: sim-camera-perception-input
- **源文件**: 54 个
  - `README.md`
  - `meshes/Ball.usd`
  - `mujoco_mecanum/README.md`
  - `mujoco_mecanum/export_summit_video.py`
  - `mujoco_mecanum/robots/summit_xl_description/assets/basic_scene.xml`
  - `mujoco_mecanum/robots/summit_xl_description/meshes/bases/summit_xl_chassis.dae`
  - `mujoco_mecanum/robots/summit_xl_description/robots/summit_xl_std.urdf.xacro`
  - `mujoco_mecanum/robots/summit_xl_description/robots/summit_xls_std.urdf.xacro`
  - `mujoco_mecanum/robots/summit_xl_description/urdf/structures/structure_rear_axis.urdf.xacro`
  - `robots/wam7_armreacher.xml`
  - ... 及其他 44 个

### truth-state-policy-input (perception)

- **覆盖状态**: full
- **映射 Skill**: truth-state-policy-input
- **源文件**: 18 个
  - `docs/OBSERVATION_SPACE_ANALYSIS.md`
  - `docs/SUCCESS_RATE_IMPROVEMENTS.md`
  - `docs/VELOCITY_CONTROL_ANALYSIS.md`
  - `scripts/analyze_obs_gap.py`
  - `scripts/envs/3Dreacher/completenavigator_v0.py`
  - `scripts/envs/armreacher/armreacher_v0.py`
  - `scripts/envs/armreacher/armreacher_v1.py`
  - `scripts/envs/mecanum_navigator/mecanum_navigator_v1.py`
  - `scripts/envs/navigaterobot/navigaterobot_v0.py`
  - `scripts/envs/navigaterobot/navigaterobot_v1.py`
  - ... 及其他 8 个

### ball-detector (perception)

- **覆盖状态**: full
- **映射 Skill**: ball-detector
- **源文件**: 21 个
  - `README.md`
  - `scripts/cfg/mecanum_navigator.yaml`
  - `scripts/envs/summit_catcher/summit_catcher_v1.py`
  - `scripts/test_mecanum_navigation.py`
  - `scripts/test_summit_catcher.py`
  - `tennis_tracker/INSTALL.md`
  - `tennis_tracker/PROJECT_SUMMARY.md`
  - `tennis_tracker/QUICKSTART.md`
  - `tennis_tracker/README.md`
  - `tennis_tracker/binocular_camera/demo_obs_builder.py`
  - ... 及其他 11 个

### ball-state-estimator (perception)

- **覆盖状态**: full
- **映射 Skill**: ball-state-estimator
- **源文件**: 14 个
  - `README.md`
  - `mujoco_mecanum/robots/summit_xl_description/meshes/structures/structure_ptz_rgbd_gps.stl`
  - `scripts/misc/trajectory_estimator.py`
  - `tennis_tracker/INSTALL.md`
  - `tennis_tracker/PROJECT_SUMMARY.md`
  - `tennis_tracker/README.md`
  - `tennis_tracker/binocular_camera/obs_builder.py`
  - `tennis_tracker/config/obs_mode.yaml`
  - `tennis_tracker/config/system_config.yaml`
  - `tennis_tracker/requirements.txt`
  - ... 及其他 4 个

### ball-tracker (perception)

- **覆盖状态**: full
- **映射 Skill**: ball-tracker
- **源文件**: 48 个
  - `.gitignore`
  - `README.md`
  - `mujoco_mecanum/README.md`
  - `mujoco_mecanum/robots/summit_xl_description/assets/summit_xls.urdf.xml`
  - `mujoco_mecanum/robots/summit_xl_description/package.xml`
  - `robots/wam7_armreacher.xml`
  - `robots/wam7_blockreacher.xml`
  - `robots/wam7_mecanum.xml`
  - `robots/wam7_test_v10.xml`
  - `scripts/analyze_obs_gap.py`
  - ... 及其他 38 个

### ball-flight-model (modeling)

- **覆盖状态**: full
- **映射 Skill**: ball-flight-model
- **源文件**: 6 个
  - `docs/SUCCESS_RATE_ANALYSIS.md`
  - `docs/SUCCESS_RATE_EXPLAINED.md`
  - `scripts/envs/summit_catcher/summit_catcher_v1.py`
  - `scripts/misc/trajectory_estimator.py`
  - `scripts/test_mecanum_navigation.py`
  - `tennis_tracker/PROJECT_SUMMARY.md`

### ball-impact-contact (modeling)

- **覆盖状态**: full
- **映射 Skill**: ball-impact-contact
- **源文件**: 6 个
  - `mujoco_mecanum/robots/summit_xl_description/assets/basic_scene.xml`
  - `mujoco_mecanum/robots/summit_xl_description/summit_xls.xml`
  - `mujoco_mecanum/robots/summit_xl_description/urdf/bases/summit_xl_base.urdf.xacro`
  - `mujoco_mecanum/robots/summit_xl_description/urdf/bases/summit_xl_hls_base.urdf.xacro`
  - `mujoco_mecanum/robots/summit_xl_description/urdf/bases/summit_xls_base.urdf.xacro`
  - `mujoco_mecanum/summit_test.py`

### ball-kinematic-model (modeling)

- **覆盖状态**: full
- **映射 Skill**: ball-kinematic-model
- **源文件**: 1 个
  - `mujoco_mecanum/robots/summit_xl_description/launch/summit_xl_state_robot.launch`

### control-safety-supervisor (control)

- **覆盖状态**: full
- **映射 Skill**: control-safety-supervisor
- **源文件**: 6 个
  - `scripts/cfg/wam7_3Dreacher.yaml`
  - `scripts/cfg/wam7_armreacher.yaml`
  - `scripts/envs/3Dreacher/helper.py`
  - `scripts/envs/armreacher/armreacher_v1.py`
  - `scripts/envs/stroke/stroke_v0.py`
  - `scripts/envs/stroke/stroke_v1.py`

### mobile-base-executor (execution)

- **覆盖状态**: full
- **映射 Skill**: mobile-base-executor
- **源文件**: 120 个
  - `.gitignore`
  - `README.md`
  - `baseline_training_log.txt`
  - `docs/BEFORE_AFTER_COMPARISON.md`
  - `docs/MECANUM_INSPIRED_UPDATE.md`
  - `docs/PROJECT_OVERVIEW.md`
  - `docs/guides/SPEED_SCALING_FIX.md`
  - `mujoco_mecanum/README.md`
  - `mujoco_mecanum/export_summit_video.py`
  - `mujoco_mecanum/robots/summit_xl_description/CMakeLists.txt`
  - ... 及其他 110 个

### sb3-rl-training-runner (training)

- **覆盖状态**: full
- **映射 Skill**: sb3-rl-training-runner
- **源文件**: 13 个
  - `baseline_aligned_log.txt`
  - `baseline_training_log.txt`
  - `docs/CHECKPOINT_UPDATE_SUMMARY.md`
  - `scripts/analyze_obs_gap.py`
  - `scripts/callbacks/curriculum.py`
  - `scripts/callbacks/episode_end_logger.py`
  - `scripts/callbacks/success_rate.py`
  - `scripts/callbacks/video_callback.py`
  - `scripts/test_mecanum_navigation.py`
  - `scripts/test_summit_catcher.py`
  - ... 及其他 3 个

### robot-trajectory-web-visualizer (engineering)

- **覆盖状态**: full
- **映射 Skill**: robot-trajectory-web-visualizer
- **源文件**: 10 个
  - `.gitignore`
  - `mujoco_mecanum/robots/summit_xl_description/assets/basic_scene.xml`
  - `scripts/misc/motionplanners/obstacle.py`
  - `scripts/misc/trajectory_estimator.py`
  - `scripts/test_mecanum_navigation.py`
  - `tennis_tracker/INSTALL.md`
  - `tennis_tracker/PROJECT_SUMMARY.md`
  - `tennis_tracker/QUICKSTART.md`
  - `tennis_tracker/binocular_camera/test_stereo_on_sim.py`
  - `tennis_tracker/requirements.txt`

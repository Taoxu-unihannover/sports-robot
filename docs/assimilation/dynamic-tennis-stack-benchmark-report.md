# dynamic-tennis 技术栈横向评测报告

> 评测日期：2026-06-09T17:53:29
> 随机种子：[0, 42, 123]
> 每种子评测回合：5

## simulation

| 方法 | 来源 | Skill |
|---|---|---|
| mujoco-tennis-world-builder | sports_robot | mujoco-tennis-world-builder |
| mujoco-policy-evaluator | sports_robot | mujoco-policy-evaluator |

## perception

| 方法 | 来源 | Skill |
|---|---|---|
| sim-camera-perception-input | sports_robot | sim-camera-perception-input |
| truth-state-policy-input | sports_robot | truth-state-policy-input |
| ball-detector | sports_robot | ball-detector |
| ball-state-estimator | sports_robot | ball-state-estimator |
| ball-tracker | sports_robot | ball-tracker |

## modeling

| 方法 | 来源 | Skill |
|---|---|---|
| ball-flight-model | sports_robot | ball-flight-model |
| ball-impact-contact | sports_robot | ball-impact-contact |
| ball-kinematic-model | sports_robot | ball-kinematic-model |

## control

| 方法 | 来源 | Skill |
|---|---|---|
| mpc-controller | sports_robot | mpc-controller |
| control-safety-supervisor | sports_robot | control-safety-supervisor |

## execution

| 方法 | 来源 | Skill |
|---|---|---|
| mobile-base-executor | sports_robot | mobile-base-executor |

## training

| 方法 | 来源 | Skill |
|---|---|---|
| sb3-rl-training-runner | sports_robot | sb3-rl-training-runner |

## engineering

| 方法 | 来源 | Skill |
|---|---|---|
| robot-trajectory-web-visualizer | sports_robot | robot-trajectory-web-visualizer |

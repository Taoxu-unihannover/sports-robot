---
name: versioned-calibration-release
skill: maintenance-release
description: 将代码、固件、硬件、标定和场地参数绑定为可复现 release 的流程。
source:
  report: docs/tech-report/005-工程层.md
sport: [table_tennis, badminton, tennis]
difficulty: beginner
requires_training: false
---

# Versioned Calibration Release Recipe

## 参数文件

- `kinematic.yaml`
- `sensor_calib.yaml`
- `dyn_params.yaml`
- `court_profile.yaml`
- `safety_limits.yaml`

## 流程

1. 标定完成后写入版本号和时间戳。
2. release 绑定硬件 revision 与参数文件。
3. 上机前检查版本匹配。
4. 更换 FRU 后强制复标定。
5. 未通过标定不得进入高动态模式。


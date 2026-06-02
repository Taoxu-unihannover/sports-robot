# Ball Perception 快速开始

> 5 分钟搭建球类感知开发环境

## 环境要求

- Python >= 3.8
- pip
- Git

## 安装

```bash
# 1. 克隆仓库
git clone https://github.com/Taoxu-unihannover/sports-robot.git
cd sports-robot

# 2. 初始化插件环境
cd plugins/ball-perception
bash init.sh

# 3. 安装 Python 依赖
pip install -r requirements.txt
```

## 验证安装

```bash
# 运行回归测试（23 个测试用例）
cd plugins/ball-perception
python -m pytest tests/regression.py -v

# 预期输出：23 passed, 5 skipped (缺少 opencv 时跳过视觉相关测试)
```

## 第一个感知流水线

### 1. 准备配置文件

创建 `config.yaml`：

```yaml
cameras:
  cam0:
    width: 1920
    height: 1080
    K: [[1200, 0, 960], [0, 1200, 540], [0, 0, 1]]
    dist_coeffs: [0, 0, 0, 0, 0]
    R: [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    t: [0, 0, 0]

detector:
  type: yolo
  model_path: yolov8n.pt
  confidence_threshold: 0.25

tracker:
  window_size: 5
  max_gap: 3
  max_velocity: 500

filter:
  model: CV
  dt: 0.008
  process_noise: 1.0
  measurement_noise: 10.0
```

### 2. 运行流水线

```python
import sys
sys.path.insert(0, "plugins/ball-perception/scripts")
sys.path.insert(0, "skills/ball-detector/scripts")
sys.path.insert(0, "skills/ball-tracker/scripts")
sys.path.insert(0, "skills/ball-state-estimator/scripts")
sys.path.insert(0, "skills/ball-geometry/scripts")
sys.path.insert(0, "skills/ball-spin-estimator/scripts")

from pipeline import PerceptionPipeline

pipeline = PerceptionPipeline("plugins/ball-perception/assets/config.yaml")
pipeline.run("input_video.mp4", display=True)
```

## 下一步

- 阅读 [AGENTS.md](./AGENTS.md) 了解 Team 架构
- 阅读 [development-guide.md](./workflows/development-guide.md) 了解开发规范
- 查看各 Skill 的 SKILL.md 了解模块详情

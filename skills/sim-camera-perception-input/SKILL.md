---
name: sim-camera-perception-input
description: 从 MuJoCo camera/render buffer 采集仿真图像，接入球检测/跟踪/状态估计感知链路，模拟真实感知输入替代真值状态。适用于用户需要用仿真图像训练感知策略、对比真值与感知输入的性能差异、测试 sim-to-real 鲁棒性；不用于真值状态输入或纯 MuJoCo 场景搭建。
---

# 仿真相机感知输入

## 用途

从 MuJoCo 渲染引擎采集仿真图像，通过球检测→跟踪→状态估计的感知链路，将图像转换为策略可用的观测向量。用于模拟真实感知链路，对比真值输入与感知输入的性能差异，测试 sim-to-real 鲁棒性。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| mujoco_model | MjModel | 是 | MuJoCo 模型 |
| mujoco_data | MjData | 是 | MuJoCo 数据 |
| camera_name | string | 否 | 相机名称，默认默认相机 |
| image_width | int | 否 | 图像宽度，默认 640 |
| image_height | int | 否 | 图像高度，默认 480 |
| perception_pipeline | string | 否 | 感知管线类型：detector, tracker, estimator |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| 相机适配器 | scripts/mujoco_camera_adapter.py | MuJoCo 渲染接口 |
| 视觉状态适配器 | scripts/vision_state_adapter.py | 图像→状态估计 |
| 测试 | tests/test_camera.py | 渲染和感知测试 |

## 执行步骤

### 步骤 1：MuJoCo 渲染接口

```python
class MuJoCoCameraAdapter:
    def __init__(self, model, data, width=640, height=480, camera_name=None):
        self.model = model
        self.data = data
        self.width = width
        self.height = height
        self.renderer = mujoco.Renderer(model, height=height, width=width)
        self.camera_name = camera_name

    def capture(self):
        if self.camera_name:
            self.renderer.update_scene(self.data, camera_id=self.camera_name)
        else:
            self.renderer.update_scene(self.data)
        return self.renderer.render()
```

### 步骤 2：球检测

从渲染图像中检测球体位置：

```python
class BallDetector:
    def detect(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        mask = cv2.inRange(hsv, self.ball_hsv_low, self.ball_hsv_high)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest)
            if M["m00"] > 0:
                cx = M["m10"] / M["m00"]
                cy = M["m01"] / M["m00"]
                return (cx, cy, 1.0)
        return (0.0, 0.0, 0.0)
```

### 步骤 3：状态估计

从 2D 检测结果估计 3D 状态：

```python
class VisionStateAdapter:
    def __init__(self, detector, camera_adapter):
        self.detector = detector
        self.camera = camera_adapter
        self.estimator = BallStateEstimator()

    def get_observation(self):
        image = self.camera.capture()
        detection = self.detector.detect(image)
        state = self.estimator.update(detection)
        return state
```

### 步骤 4：性能对比

| 输入类型 | 状态误差 | 推理延迟 |
|---|---|---|
| 真值输入 | 0 | <0.1ms |
| 图像感知输入 | 待测量 | 待测量 |

感知输入的状态误差不应超过真值输入误差的 120%。

## 失败处理

| 失败场景 | 处理策略 |
|---|---|
| 渲染失败 | 检查 OpenGL 后端和显示环境 |
| 检测失败 | 调整 HSV 阈值或使用深度学习检测器 |
| 状态估计发散 | 增加观测噪声或降低估计增益 |

## 验证方式

1. 渲染图像非全黑
2. 球检测在仿真场景中有效
3. 状态估计误差在可接受范围
4. 与真值输入的对比测试

## 可选 Recipes

| Recipe | 说明 |
|---|---|
| tennis-ball-camera | 网球仿真相机感知 |

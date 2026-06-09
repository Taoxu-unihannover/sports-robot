---
name: robot-trajectory-web-visualizer
description: 输出 episode JSON 数据、HTML5 播放器、本地 HTTP server 和轨迹图，用于球类机器人导航/击球轨迹的 Web 可视化。适用于用户需要可视化机器人轨迹、分享评估结果、在浏览器中查看仿真回放；不用于实时仿真或训练过程。
---

# 机器人轨迹 Web 可视化

## 用途

将评估 episode 的轨迹数据导出为 JSON 格式，生成 HTML5 交互式可视化页面，支持轨迹动画播放、球场标记、机器人/球体位置显示。提供本地 HTTP server 用于浏览器查看。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| episodes_data | list[dict] | 是 | episode 数据列表 |
| court_dimensions | dict | 是 | 球场尺寸 {length, width} |
| output_dir | string | 否 | 输出目录，默认 web_viz_data |
| include_images | bool | 否 | 是否包含 MuJoCo 截图，默认 False |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| Episode JSON | web_viz_data/episode_N.json | 轨迹数据 |
| HTML 播放器 | web_visualization/visualization.html | 交互式可视化 |
| HTTP Server | scripts/launch_server.py | 本地浏览服务 |
| 轨迹图 | web_viz_data/trajectory_N.png | Matplotlib 静态图 |

## 执行步骤

### 步骤 1：导出 Episode JSON

标准 JSON schema：

```json
{
  "episode": 1,
  "success": true,
  "tennis_ball": [x, y],
  "court_width": 8.23,
  "court_length": 11.885,
  "goal_tolerance": 0.5,
  "trajectory": [[x, y], ...],
  "tennis_ball_trajectory": [[x, y], ...],
  "mujoco_images": []
}
```

### 步骤 2：生成 HTML 可视化

HTML5 Canvas 可视化组件：
- 球场边界绘制
- 机器人轨迹动画
- 球体轨迹动画
- 播放/暂停/重置控制
- Episode 切换
- 距离和步数实时显示

### 步骤 3：启动本地 Server

```python
import http.server, socketserver
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/visualization.html'
        return super().do_GET()

with socketserver.TCPServer(("", 8000), QuietHandler) as httpd:
    httpd.serve_forever()
```

### 步骤 4：生成轨迹图

Matplotlib 静态图包含：
- 球场边界（绿色矩形）
- 机器人轨迹（蓝色线）
- 球体轨迹（橙色虚线）
- 起止点标记
- 成功/失败状态

## 失败处理

| 失败场景 | 处理策略 |
|---|---|
| JSON 数据格式错误 | 验证 schema 并修复 |
| 浏览器不兼容 | 使用 Canvas API 降级 |
| 端口占用 | 自动选择可用端口 |

## 验证方式

1. JSON 文件格式正确
2. HTML 页面可在浏览器打开
3. 轨迹动画可播放

## 可选 Recipes

| Recipe | 说明 |
|---|---|
| tennis-navigation-viz | 网球导航可视化 |

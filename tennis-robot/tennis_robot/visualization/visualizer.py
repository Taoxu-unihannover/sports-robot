import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_trajectory(episode_data, output_path):
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    half_l = episode_data.get("court_length", 11.885) / 2
    half_w = episode_data.get("court_width", 8.23) / 2
    court = plt.Rectangle((-half_w, -half_l), 2 * half_w, 2 * half_l,
                          fill=False, edgecolor="green", linewidth=2)
    ax.add_patch(court)
    traj = np.array(episode_data["trajectory"])
    ax.plot(traj[:, 0], traj[:, 1], "b-", linewidth=1, label="Robot")
    ax.plot(traj[0, 0], traj[0, 1], "go", markersize=8, label="Start")
    ax.plot(traj[-1, 0], traj[-1, 1], "rx", markersize=8, label="End")
    goal = episode_data.get("tennis_ball", [0, 0])
    ax.plot(goal[0], goal[1], "y*", markersize=12, label="Goal")
    ax.set_xlim(-half_w - 1, half_w + 1)
    ax.set_ylim(-half_l - 1, half_l + 1)
    ax.set_aspect("equal")
    ax.legend()
    status = "SUCCESS" if episode_data.get("success") else "FAIL"
    ax.set_title(f"Episode {episode_data.get('episode', '?')}: {status}")
    fig.savefig(output_path, dpi=100)
    plt.close(fig)


def generate_html_visualization(web_viz_dir, output_path):
    episodes = []
    for f in sorted(os.listdir(web_viz_dir)):
        if f.startswith("episode_") and f.endswith(".json"):
            with open(os.path.join(web_viz_dir, f), "r", encoding="utf-8") as fp:
                episodes.append(json.load(fp))

    if not episodes:
        print("No episode data found")
        return

    ep0 = episodes[0]
    court_w = ep0.get("court_width", 8.23)
    court_l = ep0.get("court_length", 11.885)
    goal_tol = ep0.get("goal_tolerance", 0.5)

    episodes_json = json.dumps(episodes)

    html = f"""<!DOCTYPE html>
<html>
<head>
<title>Tennis Robot Trajectory Visualization</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
canvas {{ border: 1px solid #ccc; }}
.controls {{ margin: 10px 0; }}
button {{ padding: 8px 16px; margin: 0 5px; cursor: pointer; }}
#info {{ margin: 10px 0; font-size: 14px; }}
</style>
</head>
<body>
<h1>Tennis Robot Trajectory Visualization</h1>
<div class="controls">
<button id="prevBtn" onclick="prevEpisode()">Previous</button>
<button id="playBtn" onclick="togglePlay()">Play</button>
<button id="resetBtn" onclick="resetAnim()">Reset</button>
<button id="nextBtn" onclick="nextEpisode()">Next</button>
<span id="epLabel">Episode 1/{len(episodes)}</span>
</div>
<div id="info">Step: 0 | Distance: - | Status: -</div>
<canvas id="canvas" width="600" height="750"></canvas>
<script>
const episodes = {episodes_json};
const courtW = {court_w};
const courtL = {court_l};
const goalTol = {goal_tol};
let currentEp = 0;
let currentStep = 0;
let playing = false;
let animId = null;

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

function worldToCanvas(x, y) {{
    const scale = 500 / (courtL + 2);
    const cx = canvas.width / 2 + x * scale;
    const cy = canvas.height / 2 - y * scale;
    return [cx, cy];
}}

function drawCourt() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const [tlx, tly] = worldToCanvas(-courtW/2, courtL/2);
    const [brx, bry] = worldToCanvas(courtW/2, -courtL/2);
    ctx.strokeStyle = 'green';
    ctx.lineWidth = 2;
    ctx.strokeRect(tlx, tly, brx - tlx, bry - tly);
}}

function drawFrame() {{
    drawCourt();
    const ep = episodes[currentEp];
    if (!ep || !ep.trajectory) return;

    const step = Math.min(currentStep, ep.trajectory.length - 1);
    const traj = ep.trajectory.slice(0, step + 1);

    if (traj.length > 1) {{
        ctx.beginPath();
        ctx.strokeStyle = 'blue';
        ctx.lineWidth = 1;
        const [sx, sy] = worldToCanvas(traj[0][0], traj[0][1]);
        ctx.moveTo(sx, sy);
        for (let i = 1; i < traj.length; i++) {{
            const [px, py] = worldToCanvas(traj[i][0], traj[i][1]);
            ctx.lineTo(px, py);
        }}
        ctx.stroke();
    }}

    if (traj.length > 0) {{
        const last = traj[traj.length - 1];
        const [rx, ry] = worldToCanvas(last[0], last[1]);
        ctx.fillStyle = 'blue';
        ctx.beginPath();
        ctx.arc(rx, ry, 5, 0, 2 * Math.PI);
        ctx.fill();
    }}

    if (ep.tennis_ball) {{
        const [gx, gy] = worldToCanvas(ep.tennis_ball[0], ep.tennis_ball[1]);
        ctx.fillStyle = 'orange';
        ctx.beginPath();
        ctx.arc(gx, gy, 8, 0, 2 * Math.PI);
        ctx.fill();
        ctx.strokeStyle = 'orange';
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.arc(gx, gy, goalTol * 500 / (courtL + 2), 0, 2 * Math.PI);
        ctx.stroke();
        ctx.setLineDash([]);
    }}

    const dist = ep.final_distance ? ep.final_distance.toFixed(3) : '-';
    const status = ep.success ? 'SUCCESS' : (step >= ep.trajectory.length - 1 ? 'FAIL' : 'Running');
    document.getElementById('info').textContent = `Step: ${{step}} | Distance: ${{dist}} | Status: ${{status}}`;
}}

function animate() {{
    if (!playing) return;
    const ep = episodes[currentEp];
    if (currentStep < (ep.trajectory ? ep.trajectory.length : 0)) {{
        currentStep++;
        drawFrame();
        animId = requestAnimationFrame(animate);
    }} else {{
        playing = false;
        document.getElementById('playBtn').textContent = 'Play';
    }}
}}

function togglePlay() {{
    playing = !playing;
    document.getElementById('playBtn').textContent = playing ? 'Pause' : 'Play';
    if (playing) animate();
}}

function resetAnim() {{
    playing = false;
    document.getElementById('playBtn').textContent = 'Play';
    currentStep = 0;
    drawFrame();
}}

function nextEpisode() {{
    if (currentEp < episodes.length - 1) {{
        currentEp++;
        currentStep = 0;
        playing = false;
        document.getElementById('playBtn').textContent = 'Play';
        document.getElementById('epLabel').textContent = `Episode ${{currentEp + 1}}/${{episodes.length}}`;
        drawFrame();
    }}
}}

function prevEpisode() {{
    if (currentEp > 0) {{
        currentEp--;
        currentStep = 0;
        playing = false;
        document.getElementById('playBtn').textContent = 'Play';
        document.getElementById('epLabel').textContent = `Episode ${{currentEp + 1}}/${{episodes.length}}`;
        drawFrame();
    }}
}}

drawFrame();
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Visualization HTML saved to: {output_path}")


if __name__ == "__main__":
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    web_viz_dir = os.path.join(project_root, "web_viz_data")
    output_path = os.path.join(project_root, "tennis_robot", "visualization", "web", "visualization.html")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    generate_html_visualization(web_viz_dir, output_path)

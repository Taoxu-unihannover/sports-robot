#!/usr/bin/env python3
"""
SummitCatcherEnv - 接球任务环境 (完整复现 dynamic-tennis-v2)

任务描述：
- 机器人站在场地中央
- 模拟对面击球，球从对面底线飞向机器人
- 机器人需要移动到球落点接住球

观测空间: Box(16,) - 16维真值观测
动作空间: Box(3,) - [vx, vy, wz]

来源: dynamic-tennis-v2/scripts/envs/summit_catcher/summit_catcher_v1.py
"""

import os
os.environ.pop("PYOPENGL_PLATFORM", None)
if "MUJOCO_GL" not in os.environ:
    os.environ["MUJOCO_GL"] = "osmesa"

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
from gymnasium import spaces

import mujoco
import numpy as np


@dataclass
class ThrowConfig:
    """对面击球来球分布配置"""
    opponent_x_range: Tuple[float, float] = (-0.8, 0.8)
    opponent_y_range: Tuple[float, float] = (-0.2, 0.2)
    opponent_z_range: Tuple[float, float] = (-0.08, 0.18)
    flight_time_range: Tuple[float, float] = (1.25, 1.85)
    target_xy_jitter: Tuple[float, float] = (-0.25, 0.25)
    target_z_jitter: Tuple[float, float] = (-0.08, 0.06)
    init_xy_radius: float = 2.0
    shot_angle_jitter_deg: float = 10.0
    shot_speed_scale_jitter: float = 0.10


class SummitCatcherEnv(gym.Env):
    """接球任务环境 - 完整复现 dynamic-tennis-v2"""
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}

    def __init__(
        self,
        render_mode: Optional[str] = None,
        frame_skip: int = 5,
        max_episode_steps: int = 800,
        img_size: Tuple[int, int] = (480, 640),
        camera_name: str = "box_cam1",
        v_max_x: float = 5.0,
        v_max_y: float = 2.0,
        w_max: float = 4.0,
        catch_hold_frames: int = 5,
        seed: int = 0,
        obs_mode: str = "sim",  # "sim"=真值, "real"=相机感知
    ):
        assert render_mode in {None, "human", "rgb_array"}
        self.render_mode = render_mode
        self.frame_skip = int(frame_skip)
        self.max_episode_steps = int(max_episode_steps)
        self.img_size = img_size
        self.camera_name = camera_name
        self.v_max_x = float(v_max_x)
        self.v_max_y = float(v_max_y)
        self.w_max = float(w_max)
        self.catch_hold_frames = int(catch_hold_frames)
        self.obs_mode = obs_mode

        self._np_random = np.random.default_rng(seed)

        # XML path - 使用 dynamic-tennis-v2 的路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # tennis-robot-v2/tennis_robot_v2/envs -> tennis-robot-v2 -> sports-robot
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
        # 优先使用 dynamic-tennis submodule
        dynamic_tennis = os.path.join(project_root, "dynamic-tennis")
        if os.path.exists(dynamic_tennis):
            self.xml_file = os.path.join(
                dynamic_tennis,
                "mujoco_mecanum",
                "robots",
                "summit_xl_description",
                "summit_xls.xml",
            )
        else:
            # 回退到 sports-robot 根目录
            self.xml_file = os.path.join(
                project_root,
                "mujoco_mecanum",
                "robots",
                "summit_xl_description",
                "summit_xls.xml",
            )

        # Load MuJoCo model
        self.model = mujoco.MjModel.from_xml_path(self.xml_file)
        self.data = mujoco.MjData(self.model)

        # Body IDs
        self._ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "goal_body")
        self._base_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "base")
        self._catch_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "catch_volume")

        # Camera
        self._cam_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_CAMERA, self.camera_name)
        self._renderer = None

        # Qpos/qvel indices for robot base (free joint: pos[3] + quat[4] + vel[6])
        # Free joints: 0=goal_joint (ball), 1=base_joint
        self._ball_jnt_id = 0  # goal_joint
        self._ball_qposadr = self.model.jnt_qposadr[self._ball_jnt_id]
        self._ball_qveladr = self.model.jnt_dofadr[self._ball_jnt_id]

        self._base_jnt_id = 1  # base_joint
        self._base_qposadr = self.model.jnt_qposadr[self._base_jnt_id]
        self._base_qveladr = self.model.jnt_dofadr[self._base_jnt_id]

        # Observation/action spaces
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(16,), dtype=np.float32)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)

        # Reward config
        self.R_EE_POS = float(os.environ.get('R_EE_POS', '15.0'))
        self.R_PRECISION = float(os.environ.get('R_PRECISION', '15.0'))
        self.SUCCESS_BONUS = float(os.environ.get('SUCCESS_BONUS', '10.0'))
        self.FAIL_PENALTY = float(os.environ.get('FAIL_PENALTY', '-15.0'))
        self.ALIVE_BONUS = float(os.environ.get('ALIVE_BONUS', '0.05'))
        self.CONTROL_COST = float(os.environ.get('CONTROL_COST', '0.0002'))
        self.STEP_PENALTY = float(os.environ.get('STEP_PENALTY', '0.05'))

        # State
        self._step_count = 0
        self._catch_frames = 0
        self._throw_config = ThrowConfig()

        self.metadata["render_fps"] = int(np.round(1.0 / (self.frame_skip * self.model.opt.timestep)))

    def set_obs_mode(self, mode: str):
        """设置观测模式: 'sim'=真值, 'real'=相机感知"""
        assert mode in ["sim", "real"]
        self.obs_mode = mode

    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        if seed is not None:
            self._np_random = np.random.default_rng(seed)

        mujoco.mj_resetData(self.model, self.data)

        # Random robot initial position
        angle = self._np_random.uniform(0, 2 * np.pi)
        radius = self._np_random.uniform(0, 2.0)
        self.data.qpos[self._base_qposadr:self._base_qposadr + 2] = [radius * np.cos(angle), radius * np.sin(angle)]
        self.data.qpos[self._base_qposadr + 2] = 0.0
        self.data.qpos[self._base_qposadr + 3:self._base_qposadr + 7] = [1, 0, 0, 0]  # identity quat
        self.data.qvel[self._base_qveladr:self._base_qveladr + 6] = 0.0

        # Throw ball
        self._throw_ball()

        self._step_count = 0
        self._catch_frames = 0

        obs = self._get_obs()
        info = self._get_info()
        return obs, info

    def _throw_ball(self):
        """模拟对面击球"""
        cfg = self._throw_config

        # Opponent hitting position
        opp_x = self._np_random.uniform(*cfg.opponent_x_range)
        opp_y = self._np_random.uniform(*cfg.opponent_y_range)
        opp_z = self._np_random.uniform(*cfg.opponent_z_range)

        # Target landing position (robot area)
        target_x = self._np_random.uniform(-2.0, 2.0)
        target_y = self._np_random.uniform(-2.0, 2.0)
        target_z = 0.0

        # Flight time
        flight_time = self._np_random.uniform(*cfg.flight_time_range)

        # Calculate initial ball velocity to reach target
        g = 9.81
        dx = target_x - opp_x
        dy = target_y - opp_y
        dz = target_z - opp_z - 0.5 * g * flight_time * flight_time

        v_xy = np.sqrt(dx * dx + dy * dy) / flight_time
        angle = np.arctan2(dy, dx) + np.radians(self._np_random.uniform(-cfg.shot_angle_jitter_deg, cfg.shot_angle_jitter_deg))
        scale = self._np_random.uniform(1 - cfg.shot_speed_scale_jitter, 1 + cfg.shot_speed_scale_jitter)

        vx = v_xy * np.cos(angle) * scale
        vy = v_xy * np.sin(angle) * scale
        vz = (dz / flight_time) * scale

        # Set ball position and velocity using free joint qpos/qvel
        self.data.qpos[self._ball_qposadr:self._ball_qposadr + 3] = [opp_x, opp_y, opp_z]
        self.data.qpos[self._ball_qposadr + 3:self._ball_qposadr + 7] = [1, 0, 0, 0]  # identity quat
        self.data.qvel[self._ball_qveladr:self._ball_qveladr + 3] = [vx, vy, vz]
        self.data.qvel[self._ball_qveladr + 3:self._ball_qveladr + 6] = 0.0

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        action = np.clip(action, -1, 1)

        # Apply action
        vx = action[0] * self.v_max_x
        vy = action[1] * self.v_max_y
        wz = action[2] * self.w_max

        self.data.ctrl[0] = vx
        self.data.ctrl[1] = vy
        self.data.ctrl[2] = wz

        # Simulate
        for _ in range(self.frame_skip):
            mujoco.mj_step(self.model, self.data)

        # Check catch
        ball_pos = self.data.body(self._ball_body_id).xpos
        base_pos = self.data.body(self._base_body_id).xpos
        dist = np.linalg.norm(ball_pos - base_pos)

        if dist < 0.3:  # Catch threshold
            self._catch_frames += 1
            success = self._catch_frames >= self.catch_hold_frames
        else:
            self._catch_frames = 0
            success = False

        # Check out of bounds
        ball_y = self.data.body(self._ball_body_id).xpos[1]
        out_of_bounds = abs(ball_y) > 8.0 or base_pos[1] > 8.0

        # Check truncated (max steps)
        self._step_count += 1
        truncated = self._step_count >= self.max_episode_steps

        # Compute reward
        reward = self._compute_reward(dist, success, out_of_bounds)

        terminated = success or out_of_bounds

        obs = self._get_obs()
        info = self._get_info()
        info['success'] = success
        info['final_distance'] = dist

        return obs, reward, terminated, truncated, info

    def _get_obs(self) -> np.ndarray:
        """获取16维观测向量"""
        ball_pos = self.data.body(self._ball_body_id).xpos
        ball_vel = self.data.qvel[0:3]  # World velocity from qvel

        base_pos = self.data.body(self._base_body_id).xpos

        # Compute distance
        dist = np.linalg.norm(ball_pos - base_pos)

        # TTC (Time To Collision) approximation
        ball_vel_xy = ball_vel[0:2]
        rel_pos_xy = ball_pos[0:2] - base_pos[0:2]
        speed = np.linalg.norm(ball_vel_xy)
        ttc = np.linalg.norm(rel_pos_xy) / speed if speed > 0.01 else 10.0
        ttc = np.clip(ttc, 0, 10)

        # Gate
        gate = 1.0 if dist < 0.5 else 0.0

        obs = np.array([
            ball_pos[0], ball_pos[1], ball_pos[2],  # 0-2: ball position
            ball_vel[0], ball_vel[1], ball_vel[2],  # 3-5: ball velocity
            base_pos[0], base_pos[1], base_pos[2],  # 6-8: robot position
            ball_vel[0], ball_vel[1], ball_vel[2],  # 9-11: ball velocity (repeat)
            ttc,  # 12: TTC
            gate, 0.0, 0.0,  # 13-15: gate
        ], dtype=np.float32)

        return obs

    def _compute_reward(self, dist: float, success: bool, out_of_bounds: bool) -> float:
        """计算奖励"""
        if success:
            return self.SUCCESS_BONUS
        if out_of_bounds:
            return self.FAIL_PENALTY

        # Dense reward
        r_pos = -dist * self.R_EE_POS
        r_precision = self.R_PRECISION / (1.0 + dist)

        # Control cost
        ctrl = np.sum(self.data.ctrl**2) * self.CONTROL_COST

        # Step penalty
        r_step = -self.STEP_PENALTY

        return r_pos + r_precision + ctrl + r_step + self.ALIVE_BONUS

    def _get_info(self) -> Dict:
        """获取信息字典"""
        ball_pos = self.data.body(self._ball_body_id).xpos
        base_pos = self.data.body(self._base_body_id).xpos
        dist = np.linalg.norm(ball_pos - base_pos)

        return {
            'ball_pos': ball_pos.copy(),
            'robot_pos': base_pos.copy(),
            'distance': dist,
            'catch_frames': self._catch_frames,
            'step': self._step_count,
            'obs_mode': self.obs_mode,
        }

    def render(self):
        if self.render_mode is None:
            return

        if self._renderer is None:
            self._renderer = mujoco.Renderer(self.model, height=self.img_size[0], width=self.img_size[1])

        if self.render_mode == "rgb_array":
            self._renderer.update_scene(self.data, self._cam_id if self._cam_id >= 0 else 0)
            return self._renderer.render()
        else:
            self._renderer.update_scene(self.data, self._cam_id if self._cam_id >= 0 else 0)
            self._renderer.render()

    def close(self):
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None


# 注册环境
gym.register("SummitCatcherV2-v0", SummitCatcherEnv)


if __name__ == "__main__":
    # Test
    env = gym.make("SummitCatcherV2-v0")
    print(f"Observation space: {env.observation_space}")
    print(f"Action space: {env.action_space}")

    obs, info = env.reset()
    print(f"Initial obs shape: {obs.shape}")

    for _ in range(100):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            print(f"Episode ended: success={info.get('success', False)}")
            env.reset()

    env.close()
    print("✅ SummitCatcherV2 test passed")
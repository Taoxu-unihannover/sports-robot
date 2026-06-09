import gymnasium as gym
from gymnasium import spaces, utils
from gymnasium.envs.mujoco import MujocoEnv
import mujoco
import numpy as np
import os
import yaml


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


class TennisNavigationEnv(MujocoEnv, utils.EzPickle):
    metadata = {"render_modes": ["human", "rgb_array", "depth_array"]}

    def __init__(
        self,
        xml_file: str = None,
        config: dict = None,
        frame_skip: int = 20,
        render_mode: str = None,
        **kwargs,
    ):
        if xml_file is None:
            xml_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "assets", "mujoco", "tennis_world", "tennis_world.xml",
            )
            xml_file = os.path.normpath(xml_file)

        if config is None:
            config = {
                "dynamics": {
                    "max_linear_velocity": 5.0,
                    "max_angular_velocity": 1.5,
                    "max_linear_acceleration": 2.0,
                    "max_angular_acceleration": 1.6,
                    "wheel_torque_limit": 50.0,
                },
                "reward_scales": {
                    "control_cost": 0.001,
                    "distance_incentive": 5000,
                    "terminal_payoff": [-10000, 10000],
                    "inTimeCost": 100,
                    "grace_time_period": 5,
                },
                "navigation": {
                    "goal_tolerance": 0.5,
                    "diagonal_length": 14.45,
                    "court_length": 11.885,
                    "court_width": 8.23,
                },
                "mecanum": {
                    "wheel_base": 0.445,
                    "track_width": 0.409,
                    "wheel_radius": 0.120,
                },
                "mujoco": {
                    "frame_skip": 20,
                    "max_steps": 1000,
                },
            }

        self.config = config
        self.max_v = config["dynamics"]["max_linear_velocity"]
        self.max_w = config["dynamics"]["max_angular_velocity"]
        self.diagonal_length = config["navigation"]["diagonal_length"]
        self.court_length = config["navigation"]["court_length"]
        self.court_width = config["navigation"]["court_width"]
        self.goal_tolerance = config["navigation"]["goal_tolerance"]
        self.wheel_torque_limit = config["dynamics"]["wheel_torque_limit"]

        self.reached = False
        self.failed = False
        self.step_count = 0
        self.goal = np.zeros(2)
        self.tennis_velocity = np.zeros(2)
        self.prev_distance = 0.0
        self.sweep = 0.0
        self.t_accepted = 0.0
        self.datatoplot = {}

        utils.EzPickle.__init__(self, xml_file, frame_skip, render_mode, config=config, **kwargs)

        MujocoEnv.__init__(
            self,
            xml_file,
            frame_skip,
            observation_space=None,
            render_mode=render_mode,
            **kwargs,
        )

        self.metadata["render_fps"] = int(np.round(1.0 / self.dt))
        self.action_space = spaces.Box(low=-1, high=1, shape=(3,), dtype=np.float64)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(12,), dtype=np.float64)
        self.init_pos = self.data.qpos.copy()

    def _quat_to_euler(self, quat):
        x, y, z, w = quat
        t0 = 2.0 * (w * x + y * z)
        t1 = 1.0 - 2.0 * (x * x + y * y)
        roll = np.arctan2(t0, t1)
        t2 = 2.0 * (w * y - z * x)
        t2 = np.clip(t2, -1.0, 1.0)
        pitch = np.arcsin(t2)
        t3 = 2.0 * (w * z + x * y)
        t4 = 1.0 - 2.0 * (y * y + z * z)
        yaw = np.arctan2(t3, t4)
        return np.array([roll, pitch, yaw])

    def _normalize_angle(self, angle):
        while angle > np.pi:
            angle -= 2 * np.pi
        while angle < -np.pi:
            angle += 2 * np.pi
        return angle

    def _distance(self, pos1, pos2):
        return np.linalg.norm(pos1 - pos2)

    def _get_obs(self):
        robot_pos = self.data.qpos[7:9].copy()
        robot_quat = self.data.qpos[10:14].copy()
        robot_vel = self.data.qvel[6:12].copy()

        robot_euler = self._quat_to_euler(robot_quat)
        yaw = robot_euler[2]

        rel_x = self.goal[0] - robot_pos[0]
        rel_y = self.goal[1] - robot_pos[1]
        goal_angle = np.arctan2(rel_y, rel_x)
        rel_angle = self._normalize_angle(goal_angle - yaw)
        self.sweep = abs(rel_angle)

        goal_distance = np.sqrt(rel_x ** 2 + rel_y ** 2)
        goal_distance_norm = goal_distance / self.diagonal_length
        yaw_norm = yaw / (2 * np.pi)
        goal_angle_norm = goal_angle / (2 * np.pi)
        rel_angle_norm = rel_angle / np.pi

        vel_norm = robot_vel.copy()
        vel_norm[:3] /= self.max_v
        vel_norm[3:] /= self.max_w

        tennis_vel_norm = self.tennis_velocity.copy()
        tennis_vel_norm /= self.max_v

        observation = np.array([
            goal_distance_norm,
            goal_angle_norm,
            rel_angle_norm,
            yaw_norm,
            vel_norm[0],
            vel_norm[1],
            vel_norm[2],
            vel_norm[3],
            vel_norm[4],
            vel_norm[5],
            tennis_vel_norm[0],
            tennis_vel_norm[1],
        ])
        return observation

    def _update_goal_visualization(self):
        try:
            goal_joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "goal_joint")
            if goal_joint_id >= 0:
                joint_qpos_adr = self.model.jnt_qposadr[goal_joint_id]
                joint_qvel_adr = self.model.jnt_dofadr[goal_joint_id]
                self.data.qpos[joint_qpos_adr:joint_qpos_adr + 7] = [
                    self.goal[0], self.goal[1], 0.067,
                    1.0, 0.0, 0.0, 0.0,
                ]
                self.data.qvel[joint_qvel_adr:joint_qvel_adr + 6] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        except Exception:
            pass

    def _check_termination(self):
        robot_pos = self.data.qpos[7:9].copy()
        curr_distance = self._distance(robot_pos, self.goal)
        if curr_distance <= self.goal_tolerance:
            self.reached = True
        half_l = self.court_length / 2
        half_w = self.court_width / 2
        margin = 2.0
        x, y = robot_pos
        if abs(x) > half_w + margin or abs(y) > half_l + margin:
            self.failed = True

    @property
    def terminated(self):
        return self.reached

    @property
    def truncated(self):
        return self.failed

    def _compute_reward(self, action):
        robot_pos = self.data.qpos[7:9].copy()
        curr_distance = self._distance(robot_pos, self.goal)
        distance_rate = self.prev_distance - curr_distance
        reward = self.config["reward_scales"]["distance_incentive"] * distance_rate

        payoff = 0
        if self.failed:
            payoff = min(self.config["reward_scales"]["terminal_payoff"])
        if self.reached:
            payoff = max(self.config["reward_scales"]["terminal_payoff"])

        ctrl_cost = self.config["reward_scales"]["control_cost"] * np.sum(np.square(action))

        in_time_cost = 0
        if self.reached:
            in_time_cost = float(self.config["reward_scales"]["inTimeCost"]) * (self.t_accepted - self.data.time)

        self.prev_distance = curr_distance
        return reward + payoff - ctrl_cost + in_time_cost

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.reached = False
        self.failed = False
        self.step_count = 0

        half_l = self.court_length / 2
        half_w = self.court_width / 2
        court_back = -half_l / 2

        robot_start_x = 0.0
        safe_margin = 0.6
        robot_start_y = court_back + safe_margin

        opposite_boundary_y = half_l / 2 - 0.3
        tennis_x_min = -half_w / 2 + 0.3
        tennis_x_max = half_w / 2 - 0.3

        tennis_x = np.random.uniform(tennis_x_min, tennis_x_max)
        tennis_y = opposite_boundary_y
        self.goal = np.array([tennis_x, tennis_y])

        tennis_vx = np.random.uniform(-1.0, 1.0)
        tennis_vy = np.random.uniform(-2.0, -0.5)
        self.tennis_velocity = np.array([tennis_vx, tennis_vy])

        self.data.qpos[:] = self.init_pos.copy()
        self.data.qvel[:] = np.zeros(self.model.nv)
        self.data.time = 0.0

        self._update_goal_visualization()

        robot_start_pos = np.array([robot_start_x, robot_start_y, 0.0, 1.0, 0.0, 0.0, 0.0])
        self.data.qpos[7:14] = robot_start_pos
        self.set_state(self.data.qpos, self.data.qvel)
        mujoco.mj_forward(self.model, self.data)

        robot_pos = self.data.qpos[7:9].copy()
        self.prev_distance = self._distance(robot_pos, self.goal)

        observation = self._get_obs()
        info = self._get_info()

        self.t_accepted = (
            self._distance(robot_pos, self.goal) / self.max_v
            + self.sweep / self.max_w
            + self.config["reward_scales"]["grace_time_period"]
        )

        return observation, info

    def step(self, action):
        self.step_count += 1

        x_move = action[0]
        y_move = action[1]
        rotate = action[2]

        front_left = x_move - y_move - rotate
        front_right = x_move + y_move + rotate
        back_left = x_move + y_move - rotate
        back_right = x_move - y_move + rotate

        wheel_commands = np.array([front_left, front_right, back_left, back_right])
        max_val = np.max(np.abs(wheel_commands))
        if max_val > 1.0:
            wheel_commands /= max_val

        actual_torques = wheel_commands * self.wheel_torque_limit
        ctrl = self.data.ctrl.copy()
        ctrl[0] = actual_torques[1]
        ctrl[1] = actual_torques[0]
        ctrl[2] = actual_torques[3]
        ctrl[3] = actual_torques[2]

        self.do_simulation(ctrl, self.frame_skip)

        dt = self.frame_skip * self.model.opt.timestep
        self.goal += self.tennis_velocity * dt
        self._update_goal_visualization()

        self._check_termination()
        reward = self._compute_reward(action)

        observation = self._get_obs()
        terminated = self.terminated
        truncated = self.truncated
        info = self._get_info()
        info["total_reward"] = reward
        info["is_success"] = terminated
        self.datatoplot = info

        return observation, reward, terminated, truncated, info

    def _get_info(self):
        robot_pos = self.data.qpos[7:9].copy()
        robot_vel = self.data.qvel[6:12].copy()
        goal_distance = self._distance(robot_pos, self.goal)
        return {
            "total_reward": 0.0,
            "goal_distance": float(goal_distance),
            "positional_error": float(goal_distance),
            "linear_velocity_x": float(robot_vel[0]),
            "linear_velocity_y": float(robot_vel[1]),
            "angular_velocity": float(robot_vel[5]),
            "step_count": self.step_count,
            "is_success": False,
        }

    def _get_reset_info(self):
        return self._get_info()

import gymnasium as gym
from gymnasium import spaces, utils
from gymnasium.envs.mujoco import MujocoEnv
import mujoco
import numpy as np
import os
import tempfile
import yaml


def _resolve_xml_path(xml_file):
    xml_file = os.path.normpath(xml_file)
    if not os.path.exists(xml_file):
        raise FileNotFoundError(f"XML file not found: {xml_file}")
    try:
        with open(xml_file, "r", encoding="utf-8") as f:
            content = f.read()
        model = mujoco.MjModel.from_xml_path(xml_file)
        return xml_file
    except (ValueError, UnicodeDecodeError):
        pass
    try:
        xml_dir = os.path.dirname(os.path.abspath(xml_file))
        all_content = {}
        for root, dirs, files in os.walk(xml_dir):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    with open(fp, "rb") as fh:
                        all_content[os.path.relpath(fp, xml_dir)] = fh.read()
                except Exception:
                    pass
        main_xml_name = os.path.basename(xml_file)
        main_content = all_content.pop(main_xml_name, None)
        if main_content is None:
            raise FileNotFoundError(f"Cannot read {main_xml_name}")
        assets = {k: v for k, v in all_content.items()}
        model = mujoco.MjModel.from_xml_string(main_content, assets=assets)
        tmp_dir = tempfile.mkdtemp(prefix="mujoco_v2_")
        for rel, content in all_content.items():
            dst = os.path.join(tmp_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as fh:
                fh.write(content)
        tmp_xml = os.path.join(tmp_dir, main_xml_name)
        with open(tmp_xml, "wb") as fh:
            fh.write(main_content)
        return tmp_xml
    except Exception:
        xml_dir = os.path.dirname(xml_file)
        tmp_dir = tempfile.mkdtemp(prefix="mujoco_v2_fallback_")
        import shutil
        for root, dirs, files in os.walk(xml_dir):
            rel = os.path.relpath(root, xml_dir)
            dst_root = os.path.join(tmp_dir, rel)
            os.makedirs(dst_root, exist_ok=True)
            for f in files:
                src = os.path.join(root, f)
                dst = os.path.join(dst_root, f)
                shutil.copy2(src, dst)
        tmp_xml = os.path.join(tmp_dir, os.path.basename(xml_file))
        return tmp_xml


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


class TennisNavigationV2Env(MujocoEnv, utils.EzPickle):
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
            _env_dir = os.path.dirname(os.path.abspath(__file__))
            xml_file = os.path.normpath(os.path.join(
                _env_dir, "..", "..", "assets", "mujoco", "tennis_world", "tennis_world.xml",
            ))
            if not os.path.exists(xml_file):
                xml_file = os.path.normpath(os.path.join(
                    _env_dir, "..", "..", "..", "assets", "mujoco", "tennis_world", "tennis_world.xml",
                ))

        xml_file = _resolve_xml_path(xml_file)

        if config is None:
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "configs", "env.yaml",
            )
            config_path = os.path.normpath(config_path)
            if os.path.exists(config_path):
                config = load_config(config_path)
            else:
                config = self._default_config()

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

    @staticmethod
    def _default_config():
        return {
            "dynamics": {
                "max_linear_velocity": 5.0,
                "max_angular_velocity": 1.5,
                "max_linear_acceleration": 2.0,
                "max_angular_acceleration": 1.6,
                "wheel_torque_limit": 50.0,
            },
            "reward_scales": {
                "control_cost": 0.0005,
                "distance_incentive": 5000,
                "velocity_alignment": 500,
                "relative_speed": 20.0,
                "step_penalty": -0.3,
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

    def _calculate_interception_point(self):
        robot_pos = self.data.qpos[7:9]
        ball_pos = self.goal
        ball_vel = self.tennis_velocity
        ball_speed = np.linalg.norm(ball_vel)

        if ball_speed < 1e-6:
            return ball_pos

        trajectory_dir = ball_vel / ball_speed
        dx = ball_pos[0] - robot_pos[0]
        dy = ball_pos[1] - robot_pos[1]
        dir_x, dir_y = trajectory_dir
        speed_ratio = self.max_v / ball_speed

        A = dir_x ** 2 + dir_y ** 2 - speed_ratio ** 2
        B = 2 * (dir_x * dx + dir_y * dy)
        C = dx ** 2 + dy ** 2

        discriminant = B ** 2 - 4 * A * C

        if discriminant < 0 or abs(A) < 1e-6:
            projection_scalar = np.dot(robot_pos - ball_pos, trajectory_dir)
            return ball_pos + projection_scalar * trajectory_dir

        sqrt_disc = np.sqrt(discriminant)
        s1 = (-B + sqrt_disc) / (2 * A)
        s2 = (-B - sqrt_disc) / (2 * A)

        s = s1 if s1 > 0 else s2
        if s <= 0:
            return ball_pos

        interception_point = ball_pos + s * trajectory_dir
        time_to_intercept = np.linalg.norm(interception_point - robot_pos) / self.max_v

        if time_to_intercept > 8.0:
            return ball_pos

        return interception_point

    def _get_predictive_target(self):
        robot_pos = self.data.qpos[7:9]
        current_distance = np.linalg.norm(self.goal - robot_pos)
        if current_distance < 3.0:
            return self.goal
        return self._calculate_interception_point()

    def _check_termination(self):
        robot_pos = self.data.qpos[7:9].copy()
        curr_distance = self._distance(robot_pos, self.goal)
        if curr_distance <= self.goal_tolerance:
            self.reached = True
        half_l = self.court_length / 2
        half_w = self.court_width / 2
        margin = 2.0
        rx, ry = robot_pos
        robot_out = abs(rx) > half_w + margin or abs(ry) > half_l + margin
        tx, ty = self.goal
        tennis_out = abs(tx) > half_w + margin or abs(ty) > half_l + margin
        if robot_out or tennis_out:
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
        distance_reward = self.config["reward_scales"]["distance_incentive"] * (self.prev_distance - curr_distance)

        robot_vel = self.data.qvel[6:8].copy()
        predictive_target = self._get_predictive_target()
        target_direction = predictive_target - robot_pos
        target_distance = np.linalg.norm(target_direction)
        if target_distance > 0:
            target_direction_norm = target_direction / target_distance
        else:
            target_direction_norm = np.array([0.0, 0.0])

        velocity_alignment = np.dot(robot_vel, target_direction_norm)
        velocity_alignment_reward = velocity_alignment * self.config["reward_scales"].get("velocity_alignment", 500.0)

        relative_speed_reward = 0
        relative_velocity = robot_vel - self.tennis_velocity
        if self.tennis_velocity[1] < 0:
            predictive_distance = np.linalg.norm(predictive_target - robot_pos)
            if predictive_distance < 3.0:
                relative_speed = np.linalg.norm(relative_velocity)
                relative_speed_reward = relative_speed * self.config["reward_scales"].get("relative_speed", 20.0)

        control_cost = -self.config["reward_scales"].get("control_cost", 0.0005) * np.sum(np.abs(self.data.ctrl[:4]))
        step_penalty = self.config["reward_scales"].get("step_penalty", -0.3)

        payoff = 0
        if self.failed:
            payoff = min(self.config["reward_scales"]["terminal_payoff"])
        elif self.reached:
            payoff = max(self.config["reward_scales"]["terminal_payoff"])

        in_time_cost = 0
        if self.reached:
            in_time_cost = float(self.config["reward_scales"]["inTimeCost"]) * (self.t_accepted - self.data.time)

        total_reward = (
            distance_reward
            + velocity_alignment_reward
            + relative_speed_reward
            + control_cost
            + step_penalty
            + payoff
            + in_time_cost
        )

        self.prev_distance = curr_distance
        return total_reward

    def reset_model(self):
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

        self.t_accepted = (
            self._distance(robot_pos, self.goal) / self.max_v
            + self.sweep / self.max_w
            + self.config["reward_scales"]["grace_time_period"]
        )

        return self._get_obs()

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

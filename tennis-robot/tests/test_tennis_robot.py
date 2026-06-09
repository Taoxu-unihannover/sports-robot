import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tennis_robot.envs.registration import register_envs
from tennis_robot.envs.tennis_navigation_env import TennisNavigationEnv
from tennis_robot.control.mecanum_controller import MecanumController

import gymnasium as gym
import numpy as np


def test_env_registration():
    register_envs()
    env = gym.make("TennisNavigation-v1")
    assert env is not None
    print("PASS: Environment registration")


def test_env_reset():
    register_envs()
    env = gym.make("TennisNavigation-v1")
    obs, info = env.reset()
    assert obs.shape == (12,), f"Expected obs shape (12,), got {obs.shape}"
    assert isinstance(info, dict)
    print(f"PASS: Environment reset, obs shape={obs.shape}")


def test_env_step():
    register_envs()
    env = gym.make("TennisNavigation-v1")
    obs, info = env.reset()
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    assert obs.shape == (12,)
    assert isinstance(reward, (int, float))
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)
    print(f"PASS: Environment step, reward={reward:.4f}")


def test_check_env():
    register_envs()
    env = gym.make("TennisNavigation-v1")
    from stable_baselines3.common.env_checker import check_env
    check_env(env.unwrapped)
    print("PASS: check_env")


def test_mecanum_controller():
    ctrl = MecanumController()
    action = np.array([1.0, 0.0, 0.0])
    torques = ctrl.action_to_wheel_torques(action)
    assert torques.shape == (4,)
    print(f"PASS: Mecanum controller, torques={torques}")


def test_observation_components():
    register_envs()
    env = gym.make("TennisNavigation-v1")
    obs, info = env.reset()
    assert 0 <= obs[0] <= 1.0, f"goal_distance_norm out of range: {obs[0]}"
    assert -1 <= obs[2] <= 1, f"rel_angle_norm out of range: {obs[2]}"
    print(f"PASS: Observation components validated")


if __name__ == "__main__":
    test_env_registration()
    test_env_reset()
    test_env_step()
    test_check_env()
    test_mecanum_controller()
    test_observation_components()
    print("\nAll tests PASSED!")

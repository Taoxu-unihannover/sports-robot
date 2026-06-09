import pytest
import numpy as np
import gymnasium as gym
from tennis_robot_v2.envs.registration import register as _reg


def test_env_creation():
    env = gym.make("TennisNavigationV2-v1")
    assert env.observation_space.shape == (12,)
    assert env.action_space.shape == (3,)
    env.close()


def test_env_reset():
    env = gym.make("TennisNavigationV2-v1")
    obs, info = env.reset(seed=42)
    assert obs.shape == (12,)
    assert isinstance(info, dict)
    env.close()


def test_env_step():
    env = gym.make("TennisNavigationV2-v1")
    obs, info = env.reset(seed=0)
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    assert obs.shape == (12,)
    assert isinstance(reward, (int, float))
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    env.close()


def test_predictive_reward():
    env = gym.make("TennisNavigationV2-v1")
    obs, info = env.reset(seed=42)
    total_reward = 0
    for _ in range(50):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        if terminated or truncated:
            break
    assert total_reward != 0
    env.close()


def test_interception_point():
    env = gym.make("TennisNavigationV2-v1")
    obs, info = env.reset(seed=42)
    point = env.unwrapped._calculate_interception_point()
    assert point.shape == (2,)
    env.close()

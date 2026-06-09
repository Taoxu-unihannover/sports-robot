#!/usr/bin/env python3
"""Smoke test for tennis-robot-v2 environment."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gymnasium as gym
from stable_baselines3.common.env_checker import check_env
from tennis_robot_v2.envs.registration import register as _reg


def main():
    print("=" * 60)
    print("tennis-robot-v2 Smoke Test")
    print("=" * 60)

    print("\n[1/5] Creating environment...")
    env = gym.make("TennisNavigationV2-v1")
    print(f"  Observation space: {env.observation_space}")
    print(f"  Action space: {env.action_space}")

    print("\n[2/5] Running check_env...")
    check_env(env.unwrapped)
    print("  check_env PASSED")

    print("\n[3/5] Testing reset...")
    obs, info = env.reset(seed=42)
    print(f"  Observation shape: {obs.shape}")
    print(f"  Observation dtype: {obs.dtype}")
    print(f"  Info keys: {list(info.keys())}")

    print("\n[4/5] Testing step...")
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"  Reward: {reward:.2f}")
    print(f"  Terminated: {terminated}, Truncated: {truncated}")
    print(f"  Goal distance: {info['goal_distance']:.2f}m")

    print("\n[5/5] Running short episode...")
    obs, info = env.reset(seed=0)
    total_reward = 0
    steps = 0
    for _ in range(100):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        steps += 1
        if terminated or truncated:
            break
    print(f"  Steps: {steps}")
    print(f"  Total reward: {total_reward:.2f}")
    print(f"  Final distance: {info['goal_distance']:.2f}m")
    print(f"  Success: {info.get('is_success', False)}")

    env.close()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()

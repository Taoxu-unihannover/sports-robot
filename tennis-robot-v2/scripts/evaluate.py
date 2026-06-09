#!/usr/bin/env python3
"""Evaluate a trained tennis-robot-v2 policy."""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gymnasium as gym
import numpy as np
from stable_baselines3 import SAC, PPO, DDPG, TD3

from tennis_robot_v2.envs.registration import register as _reg

ALGORITHMS = {
    "SAC": SAC,
    "PPO": PPO,
    "DDPG": DDPG,
    "TD3": TD3,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--algorithm", default="SAC", choices=ALGORITHMS.keys())
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    algo_class = ALGORITHMS[args.algorithm]
    model = algo_class.load(args.model_path)

    env = gym.make("TennisNavigationV2-v1")

    results = []
    for ep in range(args.episodes):
        obs, info = env.reset(seed=args.seed + ep)
        total_reward = 0
        steps = 0
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1
            done = terminated or truncated

        robot_pos = env.unwrapped.data.qpos[7:9].copy()
        final_distance = env.unwrapped._distance(robot_pos, env.unwrapped.goal)
        success = terminated and env.unwrapped.reached

        result = {
            "episode": ep + 1,
            "reward": float(total_reward),
            "steps": steps,
            "success": success,
            "final_distance": float(final_distance),
        }
        results.append(result)
        print(f"Episode {ep + 1}: reward={total_reward:.2f}, steps={steps}, "
              f"success={success}, distance={final_distance:.2f}m")

    env.close()

    avg_reward = np.mean([r["reward"] for r in results])
    avg_steps = np.mean([r["steps"] for r in results])
    avg_distance = np.mean([r["final_distance"] for r in results])
    success_rate = np.mean([r["success"] for r in results])

    summary = {
        "source": "tennis-robot-v2",
        "algorithm": args.algorithm,
        "model_path": args.model_path,
        "evaluation_episodes": args.episodes,
        "success_rate": float(success_rate),
        "avg_reward": float(avg_reward),
        "avg_steps": float(avg_steps),
        "avg_final_distance": float(avg_distance),
        "episodes": results,
    }

    output_dir = "evaluation_results"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "v2_evaluation.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {output_path}")
    print(f"Summary: avg_reward={avg_reward:.2f}, avg_steps={avg_steps:.1f}, "
          f"avg_distance={avg_distance:.2f}m, success_rate={success_rate:.1%}")


if __name__ == "__main__":
    main()

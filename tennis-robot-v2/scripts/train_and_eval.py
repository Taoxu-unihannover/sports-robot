#!/usr/bin/env python3
"""Unified training and evaluation script for tennis-robot-v2 with baseline comparison."""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gymnasium as gym
import numpy as np
from stable_baselines3 import SAC
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
import torch

from tennis_robot_v2.envs.registration import register as _reg


class MetricsCallback(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []
        self.episode_distances = []
        self.episode_successes = []

    def _on_step(self) -> bool:
        for info in self.locals.get("infos", []):
            if "is_success" in info:
                pass
        return True


def make_env(seed=0):
    def _init():
        env = gym.make("TennisNavigationV2-v1")
        env.reset(seed=seed)
        return env
    return _init


def train(total_timesteps, seed=0, n_envs=1, save_dir="saved_models"):
    env = DummyVecEnv([make_env(seed + i) for i in range(n_envs)])

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Training on device: {device}")

    model = SAC(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=5e-4,
        buffer_size=3_000_000,
        learning_starts=5000,
        batch_size=512,
        gamma=0.99,
        tau=0.005,
        ent_coef="auto",
        policy_kwargs=dict(net_arch=[1024, 512]),
        seed=seed,
        device=device,
    )

    print(f"Training SAC for {total_timesteps} steps...")
    start = time.time()
    model.learn(total_timesteps=total_timesteps, progress_bar=False)
    elapsed = time.time() - start
    throughput = total_timesteps / elapsed
    print(f"Training done in {elapsed:.1f}s ({throughput:.1f} steps/sec)")

    os.makedirs(save_dir, exist_ok=True)
    model_path = os.path.join(save_dir, "tennis_robot_v2_sac_final")
    model.save(model_path)
    print(f"Model saved to {model_path}")

    env.close()
    return model, model_path, throughput, elapsed


def evaluate(model, episodes=20, seed=42):
    env = gym.make("TennisNavigationV2-v1")
    results = []

    for ep in range(episodes):
        obs, info = env.reset(seed=seed + ep)
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

        results.append({
            "episode": ep + 1,
            "reward": float(total_reward),
            "steps": steps,
            "success": success,
            "final_distance": float(final_distance),
        })
        if (ep + 1) % 5 == 0:
            print(f"  Episode {ep + 1}/{episodes}: reward={total_reward:.1f}, "
                  f"steps={steps}, success={success}, dist={final_distance:.2f}m")

    env.close()
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--total_timesteps", type=int, default=100000)
    parser.add_argument("--eval_episodes", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n_envs", type=int, default=1)
    parser.add_argument("--save_dir", default="saved_models")
    args = parser.parse_args()

    model, model_path, throughput, elapsed = train(
        total_timesteps=args.total_timesteps,
        seed=args.seed,
        n_envs=args.n_envs,
        save_dir=args.save_dir,
    )

    print(f"\nEvaluating trained model ({args.eval_episodes} episodes)...")
    results = evaluate(model, episodes=args.eval_episodes, seed=args.seed + 1000)

    avg_reward = np.mean([r["reward"] for r in results])
    avg_steps = np.mean([r["steps"] for r in results])
    avg_distance = np.mean([r["final_distance"] for r in results])
    success_rate = np.mean([r["success"] for r in results])

    summary = {
        "source": "tennis-robot-v2",
        "training_timesteps": args.total_timesteps,
        "training_throughput_steps_sec": round(throughput, 1),
        "training_time_sec": round(elapsed, 1),
        "training_device": "cuda" if torch.cuda.is_available() else "cpu",
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
        "algorithm": "SAC",
        "evaluation_episodes": args.eval_episodes,
        "avg_reward": round(float(avg_reward), 2),
        "avg_steps": round(float(avg_steps), 1),
        "avg_final_distance": round(float(avg_distance), 2),
        "success_rate": float(success_rate),
        "episodes": results,
    }

    output_dir = "docs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "tennis-robot-v2-baseline-metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"RESULTS SUMMARY")
    print(f"{'=' * 60}")
    print(f"Training: {args.total_timesteps} steps in {elapsed:.1f}s ({throughput:.1f} steps/sec)")
    print(f"Device: {summary['training_device']} ({summary['gpu_name']})")
    print(f"Avg Reward: {avg_reward:.2f}")
    print(f"Avg Steps: {avg_steps:.1f}")
    print(f"Avg Final Distance: {avg_distance:.2f}m")
    print(f"Success Rate: {success_rate:.1%}")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Collect dynamic-tennis baseline metrics for comparison with tennis-robot-v2."""

import json
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPORTS_ROBOT_ROOT = os.path.dirname(PROJECT_ROOT)
DYNAMIC_TENNIS_ROOT = os.path.join(SPORTS_ROBOT_ROOT, "dynamic-tennis")
SCRIPTS_DIR = os.path.join(DYNAMIC_TENNIS_ROOT, "scripts")
MECANUM_DIR = os.path.join(SCRIPTS_DIR, "envs", "mecanum_navigator")
NAVIGATE_DIR = os.path.join(SCRIPTS_DIR, "envs", "navigaterobot")

sys.path.insert(0, SCRIPTS_DIR)
sys.path.insert(0, MECANUM_DIR)
sys.path.insert(0, NAVIGATE_DIR)

import gymnasium as gym
from gymnasium.envs.registration import register
import numpy as np
from stable_baselines3 import SAC
from stable_baselines3.common.vec_env import DummyVecEnv
import torch


def make_dynamic_tennis_env(seed=0):
    def _init():
        from mecanum_navigator_v1 import MecanumNavigatorEnv
        env = MecanumNavigatorEnv()
        env.reset(seed=seed)
        return env
    return _init


def main():
    print("=" * 60)
    print("dynamic-tennis Baseline Collection")
    print("=" * 60)

    total_timesteps = 100000
    seed = 0
    eval_episodes = 20

    print(f"\nCreating dynamic-tennis environment...")
    try:
        from mecanum_navigator_v1 import MecanumNavigatorEnv
        test_env = MecanumNavigatorEnv()
        print(f"  Observation space: {test_env.observation_space}")
        print(f"  Action space: {test_env.action_space}")
        obs, info = test_env.reset(seed=seed)
        print(f"  Reset OK, obs shape: {obs.shape}")
        test_env.close()
    except Exception as e:
        print(f"Failed to create dynamic-tennis environment: {e}")
        import traceback
        traceback.print_exc()
        return

    env = DummyVecEnv([make_dynamic_tennis_env(seed + i) for i in range(1)])

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

    print(f"\nTraining SAC for {total_timesteps} steps...")
    start = time.time()
    model.learn(total_timesteps=total_timesteps, progress_bar=False)
    elapsed = time.time() - start
    throughput = total_timesteps / elapsed
    print(f"Training done in {elapsed:.1f}s ({throughput:.1f} steps/sec)")

    save_dir = os.path.join(PROJECT_ROOT, "tennis-robot-v2", "saved_models", "dynamic_tennis_baseline")
    os.makedirs(save_dir, exist_ok=True)
    model_path = os.path.join(save_dir, "dynamic_tennis_sac_final")
    model.save(model_path)
    print(f"Model saved to {model_path}")

    env.close()

    print(f"\nEvaluating ({eval_episodes} episodes)...")
    eval_env = MecanumNavigatorEnv()
    results = []

    for ep in range(eval_episodes):
        obs, info = eval_env.reset(seed=seed + 1000 + ep)
        total_reward = 0
        steps = 0
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = eval_env.step(action)
            total_reward += reward
            steps += 1
            done = terminated or truncated

        robot_pos = eval_env.data.qpos[7:9].copy()
        final_distance = eval_env.distance(robot_pos, eval_env.goal)
        success = terminated and eval_env.reached

        results.append({
            "episode": ep + 1,
            "reward": float(total_reward),
            "steps": steps,
            "success": success,
            "final_distance": float(final_distance),
        })
        if (ep + 1) % 5 == 0:
            print(f"  Episode {ep + 1}/{eval_episodes}: reward={total_reward:.1f}, "
                  f"steps={steps}, success={success}, dist={final_distance:.2f}m")

    eval_env.close()

    avg_reward = np.mean([r["reward"] for r in results])
    avg_steps = np.mean([r["steps"] for r in results])
    avg_distance = np.mean([r["final_distance"] for r in results])
    success_rate = np.mean([r["success"] for r in results])

    summary = {
        "source": "dynamic-tennis",
        "training_timesteps": total_timesteps,
        "training_throughput_steps_sec": round(throughput, 1),
        "training_time_sec": round(elapsed, 1),
        "training_device": device,
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
        "algorithm": "SAC",
        "evaluation_episodes": eval_episodes,
        "avg_reward": round(float(avg_reward), 2),
        "avg_steps": round(float(avg_steps), 1),
        "avg_final_distance": round(float(avg_distance), 2),
        "success_rate": float(success_rate),
        "episodes": results,
    }

    output_dir = os.path.join(PROJECT_ROOT, "tennis-robot-v2", "docs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "dynamic-tennis-baseline-metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"DYNAMIC-TENNIS BASELINE RESULTS")
    print(f"{'=' * 60}")
    print(f"Training: {total_timesteps} steps in {elapsed:.1f}s ({throughput:.1f} steps/sec)")
    print(f"Device: {device} ({summary['gpu_name']})")
    print(f"Avg Reward: {avg_reward:.2f}")
    print(f"Avg Steps: {avg_steps:.1f}")
    print(f"Avg Final Distance: {avg_distance:.2f}m")
    print(f"Success Rate: {success_rate:.1%}")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()

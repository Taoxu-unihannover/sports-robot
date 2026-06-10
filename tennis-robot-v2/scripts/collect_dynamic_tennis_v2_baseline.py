#!/usr/bin/env python3
"""
Collect dynamic-tennis-v2 baseline metrics using its own MecanumNavigatorEnv.

Uses the same SAC hyperparameters as dynamic-tennis-v2/scripts/train_mecanum_navigator.py
for a fair comparison with tennis-robot-v2.
"""

import argparse
import json
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPORTS_ROBOT_ROOT = os.path.dirname(PROJECT_ROOT)
DYNAMIC_TENNIS_ROOT = os.path.join(SPORTS_ROBOT_ROOT, "dynamic-tennis-v2")
SCRIPTS_DIR = os.path.join(DYNAMIC_TENNIS_ROOT, "scripts")
MECANUM_DIR = os.path.join(SCRIPTS_DIR, "envs", "mecanum_navigator")
NAVIGATE_DIR = os.path.join(SCRIPTS_DIR, "envs", "navigaterobot")

sys.path.insert(0, SCRIPTS_DIR)
sys.path.insert(0, MECANUM_DIR)
sys.path.insert(0, NAVIGATE_DIR)

import numpy as np
from stable_baselines3 import SAC
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback
import torch


class SuccessRateCallback(BaseCallback):
    def __init__(self, window=200, verbose=1):
        super().__init__(verbose)
        self.window = window
        self.buffer = []

    def _on_step(self):
        infos = self.locals.get("infos", [])
        for info in infos:
            if "is_success" in info:
                self.buffer.append(float(info["is_success"]))
                if len(self.buffer) > self.window:
                    self.buffer = self.buffer[-self.window:]
        if self.num_timesteps % 1024 == 0 and len(self.buffer) > 0:
            sr = np.mean(self.buffer)
            self.logger.record("rollout/success_rate", sr)
        return True


def make_env(rank, seed=0):
    def _init():
        from mecanum_navigator_v1 import MecanumNavigatorEnv
        env = MecanumNavigatorEnv()
        env.reset(seed=seed + rank)
        return env
    return _init


def train(total_timesteps, seed=0, n_envs=2, save_dir="saved_models"):
    env_fns = [make_env(i, seed) for i in range(n_envs)]
    if n_envs > 1:
        env = SubprocVecEnv(env_fns)
        print(f"Using SubprocVecEnv with {n_envs} parallel environments")
    else:
        env = DummyVecEnv(env_fns)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
    print(f"Training on device: {device} ({gpu_name})")

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
        target_update_interval=1,
        gradient_steps=-1,
        policy_kwargs=dict(net_arch=[1024, 512]),
        seed=seed,
        device=device,
    )

    print(f"Training dynamic-tennis-v2 SAC for {total_timesteps} steps...")

    eval_env = DummyVecEnv([make_env(1000, seed)])
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=os.path.join(save_dir, "best_model"),
        log_path=os.path.join(save_dir, "eval_logs"),
        eval_freq=max(total_timesteps // 20, 5000),
        n_eval_episodes=10,
        deterministic=True,
        verbose=0,
    )
    success_callback = SuccessRateCallback(window=200)

    start = time.time()
    model.learn(
        total_timesteps=total_timesteps,
        progress_bar=False,
        log_interval=4,
        callback=[eval_callback, success_callback],
    )
    elapsed = time.time() - start
    throughput = total_timesteps / elapsed
    print(f"Training done in {elapsed:.1f}s ({throughput:.1f} steps/sec)")

    os.makedirs(save_dir, exist_ok=True)
    model_path = os.path.join(save_dir, "dynamic_tennis_v2_sac_final")
    model.save(model_path)
    print(f"Model saved to {model_path}")

    env.close()
    eval_env.close()
    return model, model_path, throughput, elapsed, gpu_name


def evaluate(model, episodes=50, seed=42):
    from mecanum_navigator_v1 import MecanumNavigatorEnv
    env = MecanumNavigatorEnv()
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

        robot_pos = env.data.qpos[7:9].copy()
        final_distance = env.distance(robot_pos, env.goal)
        success = terminated and env.reached

        results.append({
            "episode": ep + 1,
            "reward": float(total_reward),
            "steps": steps,
            "success": success,
            "final_distance": float(final_distance),
        })
        if (ep + 1) % 10 == 0:
            print(f"  Episode {ep + 1}/{episodes}: reward={total_reward:.1f}, "
                  f"steps={steps}, success={success}, dist={final_distance:.2f}m")

    env.close()
    return results


def main():
    parser = argparse.ArgumentParser(description="dynamic-tennis-v2 baseline collection")
    parser.add_argument("--total_timesteps", type=int, default=1000000)
    parser.add_argument("--eval_episodes", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n_envs", type=int, default=2)
    parser.add_argument("--save_dir", default="saved_models")
    args = parser.parse_args()

    save_dir = os.path.join(PROJECT_ROOT, "tennis-robot-v2", "saved_models", "dynamic_tennis_v2_baseline")

    model, model_path, throughput, elapsed, gpu_name = train(
        total_timesteps=args.total_timesteps,
        seed=args.seed,
        n_envs=args.n_envs,
        save_dir=save_dir,
    )

    print(f"\nEvaluating dynamic-tennis-v2 model ({args.eval_episodes} episodes)...")
    results = evaluate(model, episodes=args.eval_episodes, seed=args.seed + 2000)

    avg_reward = np.mean([r["reward"] for r in results])
    avg_steps = np.mean([r["steps"] for r in results])
    avg_distance = np.mean([r["final_distance"] for r in results])
    success_rate = np.mean([r["success"] for r in results])

    summary = {
        "source": "dynamic-tennis-v2",
        "training_timesteps": args.total_timesteps,
        "training_throughput_steps_sec": round(throughput, 1),
        "training_time_sec": round(elapsed, 1),
        "training_device": "cuda" if torch.cuda.is_available() else "cpu",
        "gpu_name": gpu_name,
        "algorithm": "SAC",
        "hyperparameters": {
            "learning_rate": 5e-4,
            "buffer_size": 3_000_000,
            "batch_size": 512,
            "net_arch": [1024, 512],
            "gamma": 0.99,
            "tau": 0.005,
            "ent_coef": "auto",
            "target_update_interval": 1,
        },
        "n_envs": args.n_envs,
        "evaluation_episodes": args.eval_episodes,
        "avg_reward": round(float(avg_reward), 2),
        "avg_steps": round(float(avg_steps), 1),
        "avg_final_distance": round(float(avg_distance), 2),
        "success_rate": float(success_rate),
        "episodes": results,
    }

    output_dir = os.path.join(PROJECT_ROOT, "tennis-robot-v2", "docs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "dynamic-tennis-v2-baseline-metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"DYNAMIC-TENNIS-V2 BASELINE RESULTS")
    print(f"{'=' * 60}")
    print(f"Training: {args.total_timesteps} steps in {elapsed:.1f}s ({throughput:.1f} steps/sec)")
    print(f"Device: {summary['training_device']} ({gpu_name})")
    print(f"Avg Reward: {avg_reward:.2f}")
    print(f"Avg Steps: {avg_steps:.1f}")
    print(f"Avg Final Distance: {avg_distance:.2f}m")
    print(f"Success Rate: {success_rate:.1%}")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()

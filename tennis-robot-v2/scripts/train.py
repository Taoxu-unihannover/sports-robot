#!/usr/bin/env python3
"""Train tennis-robot-v2 with Stable-Baselines3."""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gymnasium as gym
from stable_baselines3 import SAC, PPO, DDPG, TD3
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback
import torch

from tennis_robot_v2.envs.registration import register as _reg

ALGORITHMS = {
    "SAC": SAC,
    "PPO": PPO,
    "DDPG": DDPG,
    "TD3": TD3,
}


def make_env(env_id, rank=0, seed=0):
    def _init():
        env = gym.make(env_id)
        env.reset(seed=seed + rank)
        return env
    return _init


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--algorithm", default="SAC", choices=ALGORITHMS.keys())
    parser.add_argument("--total_timesteps", type=int, default=5000)
    parser.add_argument("--version", default="v1")
    parser.add_argument("--n_envs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    env_id = "TennisNavigationV2-v1"
    algo_class = ALGORITHMS[args.algorithm]

    if args.n_envs > 1:
        env = DummyVecEnv([make_env(env_id, i, args.seed) for i in range(args.n_envs)])
    else:
        env = DummyVecEnv([make_env(env_id, 0, args.seed)])

    save_dir = os.path.join("saved_models", args.version)
    os.makedirs(save_dir, exist_ok=True)

    tensorboard_dir = os.path.join("runs", args.version)
    os.makedirs(tensorboard_dir, exist_ok=True)

    model = algo_class(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=5e-4,
        buffer_size=3_000_000,
        batch_size=512,
        gamma=0.99,
        tau=0.005,
        ent_coef="auto",
        policy_kwargs=dict(net_arch=[1024, 512]),
        tensorboard_log=tensorboard_dir,
        seed=args.seed,
        device="auto",
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=max(args.total_timesteps // 50, 20),
        save_path=save_dir,
        name_prefix="tennis_robot_v2",
    )

    print(f"Training {args.algorithm} for {args.total_timesteps} steps...")
    import time
    start = time.time()
    model.learn(
        total_timesteps=args.total_timesteps,
        callback=checkpoint_callback,
        progress_bar=False,
    )
    elapsed = time.time() - start
    throughput = args.total_timesteps / elapsed
    print(f"Training done in {elapsed:.1f}s ({throughput:.1f} steps/sec)")

    model_path = os.path.join(save_dir, f"tennis_robot_v2_{args.algorithm}_final")
    model.save(model_path)
    print(f"Model saved to {model_path}")

    env.close()


if __name__ == "__main__":
    main()

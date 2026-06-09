import os
import sys
import argparse
import yaml
import numpy as np

import gymnasium as gym
from stable_baselines3 import SAC, PPO, DDPG, TD3
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.utils import set_random_seed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tennis_robot.envs.registration import register_envs

ALGORITHMS = {"SAC": SAC, "PPO": PPO, "DDPG": DDPG, "TD3": TD3}


class MetricsCallback(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)

    def _on_rollout_end(self):
        try:
            envs = self.model.get_env()
            if envs is not None:
                info = envs.env_method("get_attr", "datatoplot")[0]
                if info:
                    for key, value in info.items():
                        if isinstance(value, (int, float)):
                            self.logger.record(f"rollout/{key}", value)
        except Exception:
            pass

    def _on_step(self):
        return True


def train(args):
    register_envs()

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "configs", "train_sac.yaml",
    )
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            train_config = yaml.load(f, Loader=yaml.FullLoader)
    else:
        train_config = {}

    algorithm = args.algorithm or train_config.get("algorithm", "SAC")
    total_timesteps = args.total_timesteps or train_config.get("total_timesteps", 15000)
    n_envs = args.n_envs or train_config.get("n_envs", 2)
    save_frequency = train_config.get("save_frequency", 50)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    save_dir = os.path.join(project_root, "saved_models", args.version or "default")
    log_dir = os.path.join(project_root, "runs", args.version or "default")
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    def make_env(rank):
        def _init():
            env = gym.make("TennisNavigation-v1")
            env.reset(seed=(args.seed or 42) + rank)
            return env.unwrapped
        return _init

    env = make_vec_env("TennisNavigation-v1", n_envs=n_envs, seed=args.seed or 42)

    algo_class = ALGORITHMS.get(algorithm, SAC)

    if args.resume_from:
        model = algo_class.load(args.resume_from, env=env, tensorboard_log=log_dir)
        print(f"Resumed from {args.resume_from}")
    else:
        model = algo_class(
            "MlpPolicy",
            env,
            learning_rate=train_config.get("learning_rate", 5e-4),
            batch_size=train_config.get("batch_size", 512),
            buffer_size=train_config.get("buffer_size", 3000000),
            gamma=train_config.get("gamma", 0.99),
            tau=train_config.get("tau", 0.005),
            ent_coef=train_config.get("ent_coef", "auto"),
            verbose=1,
            tensorboard_log=log_dir,
            policy_kwargs=dict(net_arch=train_config.get("net_arch", [1024, 512])),
        )

    checkpoint_callback = CheckpointCallback(
        save_freq=max(total_timesteps // save_frequency, 1),
        save_path=save_dir,
        name_prefix="tennis_robot",
    )
    metrics_callback = MetricsCallback()

    print(f"Training {algorithm} for {total_timesteps} timesteps...")
    print(f"Save dir: {save_dir}")
    print(f"Log dir: {log_dir}")

    model.learn(
        total_timesteps=total_timesteps,
        callback=[checkpoint_callback, metrics_callback],
        tb_log_name=f"{algorithm}_{args.version or 'default'}",
        reset_num_timesteps=not args.resume_from,
    )

    final_path = os.path.join(save_dir, f"tennis_robot_{algorithm}_final")
    model.save(final_path)
    print(f"Model saved to {final_path}")

    env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train tennis-robot RL agent")
    parser.add_argument("--algorithm", type=str, default=None, choices=["SAC", "PPO", "DDPG", "TD3"])
    parser.add_argument("--total_timesteps", type=int, default=None)
    parser.add_argument("--n_envs", type=int, default=None)
    parser.add_argument("--version", type=str, default="v1")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--resume_from", type=str, default=None)
    train(parser.parse_args())

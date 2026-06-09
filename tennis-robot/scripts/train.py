import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tennis_robot.training.train import train
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train tennis-robot RL agent")
    parser.add_argument("--algorithm", type=str, default=None, choices=["SAC", "PPO", "DDPG", "TD3"])
    parser.add_argument("--total_timesteps", type=int, default=None)
    parser.add_argument("--n_envs", type=int, default=None)
    parser.add_argument("--version", type=str, default="v1")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--resume_from", type=str, default=None)
    train(parser.parse_args())

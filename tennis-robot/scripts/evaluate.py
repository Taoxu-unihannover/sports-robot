import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tennis_robot.evaluation.evaluate import evaluate
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate tennis-robot RL agent")
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--algorithm", type=str, default=None)
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--max_steps", type=int, default=2000)
    parser.add_argument("--deterministic", action="store_true", default=True)
    parser.add_argument("--version", type=str, default="v1")
    evaluate(parser.parse_args())

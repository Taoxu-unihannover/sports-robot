#!/usr/bin/env python3
"""
Real-mode evaluation for tennis-robot-v2.

Compares sim mode (truth state) vs real mode (image-based perception).
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from stable_baselines3 import SAC

from tennis_robot_v2.envs.registration import register as _reg


def evaluate_sim(env, model, episodes, seed):
    """Evaluate using truth state observation."""
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

        results.append({
            "episode": ep + 1,
            "mode": "sim",
            "reward": float(total_reward),
            "steps": steps,
            "success": terminated and env.unwrapped.reached,
            "final_distance": float(final_distance),
        })

    return results


def evaluate_real(env, model, episodes, seed):
    """Evaluate using image-based perception (real mode)."""
    results = []
    detection_count = 0
    total_cam_steps = 0

    for ep in range(episodes):
        obs, info = env.reset(seed=seed + ep)
        # Switch to real mode
        env.unwrapped.set_obs_mode("real")

        total_reward = 0
        steps = 0
        done = False

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1
            done = terminated or truncated

            if info.get("ball_detected"):
                detection_count += 1
            total_cam_steps += 1

        # Switch back to sim mode for reset
        env.unwrapped.set_obs_mode("sim")

        robot_pos = env.unwrapped.data.qpos[7:9].copy()
        final_distance = env.unwrapped._distance(robot_pos, env.unwrapped.goal)

        det_rate = detection_count / max(total_cam_steps, 1)

        results.append({
            "episode": ep + 1,
            "mode": "real",
            "reward": float(total_reward),
            "steps": steps,
            "success": terminated and env.unwrapped.reached,
            "final_distance": float(final_distance),
            "detection_rate": float(det_rate),
        })

    return results


def compute_summary(results, label):
    successes = [r["success"] for r in results]
    rewards = [r["reward"] for r in results]
    steps = [r["steps"] for r in results]
    distances = [r["final_distance"] for r in results]

    summary = {
        "label": label,
        "num_episodes": len(results),
        "success_rate": float(np.mean(successes)),
        "avg_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "avg_steps": float(np.mean(steps)),
        "avg_final_distance": float(np.mean(distances)),
    }

    det_rates = [r.get("detection_rate") for r in results if "detection_rate" in r]
    if det_rates:
        summary["avg_detection_rate"] = float(np.mean(det_rates))

    return summary


def main():
    parser = argparse.ArgumentParser(description="Real-mode evaluation for tennis-robot-v2")
    parser.add_argument("--model_path", required=True, help="Path to trained model")
    parser.add_argument("--algorithm", default="SAC", choices=["SAC", "PPO"])
    parser.add_argument("--episodes", type=int, default=20, help="Number of episodes per mode")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--skip_real", action="store_true", help="Skip real mode evaluation")
    parser.add_argument("--output", default="evaluation_results/real_mode_eval.json")
    args = parser.parse_args()

    print(f"Loading model from {args.model_path}")
    model = SAC.load(args.model_path)

    import gymnasium as gym
    env = gym.make("TennisNavigationV2-v1")

    # Sim mode evaluation
    print(f"\n=== Sim Mode Evaluation ({args.episodes} episodes) ===")
    sim_results = evaluate_sim(env, model, args.episodes, args.seed)
    sim_summary = compute_summary(sim_results, "Sim Mode")

    print(f"Success rate: {sim_summary['success_rate']*100:.1f}%")
    print(f"Avg reward: {sim_summary['avg_reward']:.1f}")
    print(f"Avg steps: {sim_summary['avg_steps']:.1f}")
    print(f"Avg final distance: {sim_summary['avg_final_distance']:.2f}m")

    # Real mode evaluation
    if not args.skip_real:
        print(f"\n=== Real Mode Evaluation ({args.episodes} episodes) ===")
        real_results = evaluate_real(env, model, args.episodes, args.seed)
        real_summary = compute_summary(real_results, "Real Mode")

        print(f"Success rate: {real_summary['success_rate']*100:.1f}%")
        print(f"Avg reward: {real_summary['avg_reward']:.1f}")
        print(f"Avg steps: {real_summary['avg_steps']:.1f}")
        print(f"Avg final distance: {real_summary['avg_final_distance']:.2f}m")
        print(f"Avg detection rate: {real_summary.get('avg_detection_rate', 0)*100:.1f}%")
    else:
        real_results = []
        real_summary = None

    env.close()

    # Save results
    all_results = {
        "eval_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model_path": args.model_path,
        "algorithm": args.algorithm,
        "episodes": args.episodes,
        "seed": args.seed,
        "sim_summary": sim_summary,
        "real_summary": real_summary,
        "sim_results": sim_results,
        "real_results": real_results,
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to {args.output}")

    # Summary comparison
    if real_summary is not None:
        print("\n" + "=" * 60)
        print("=== Sim vs Real Mode Comparison ===")
        print("=" * 60)
        print(f"{'Metric':<25} {'Sim':>15} {'Real':>15} {'Gap':>15}")
        print("-" * 60)
        print(f"{'Success Rate':<25} {sim_summary['success_rate']*100:>14.1f}% {real_summary['success_rate']*100:>14.1f}% {(real_summary['success_rate']-sim_summary['success_rate'])*100:>+14.1f}%")
        print(f"{'Avg Reward':<25} {sim_summary['avg_reward']:>15.1f} {real_summary['avg_reward']:>15.1f} {real_summary['avg_reward']-sim_summary['avg_reward']:>+15.1f}")
        print(f"{'Avg Steps':<25} {sim_summary['avg_steps']:>15.1f} {real_summary['avg_steps']:>15.1f} {real_summary['avg_steps']-sim_summary['avg_steps']:>+15.1f}")
        print(f"{'Avg Final Distance':<25} {sim_summary['avg_final_distance']:>14.2f}m {real_summary['avg_final_distance']:>14.2f}m {(real_summary['avg_final_distance']-sim_summary['avg_final_distance']):>+14.2f}m")
        print("=" * 60)


if __name__ == "__main__":
    main()
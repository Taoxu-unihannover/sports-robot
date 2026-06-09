import os
import sys
import json
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import gymnasium as gym

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tennis_robot.envs.registration import register_envs


def evaluate(args):
    register_envs()

    from stable_baselines3 import SAC, PPO, DDPG, TD3
    ALGORITHMS = {"SAC": SAC, "PPO": PPO, "DDPG": DDPG, "TD3": TD3}

    algorithm = args.algorithm or "SAC"
    algo_class = ALGORITHMS.get(algorithm, SAC)
    model = algo_class.load(args.model_path)

    env = gym.make("TennisNavigation-v1")

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    results_dir = os.path.join(project_root, "evaluation_results", args.version or "default")
    web_viz_dir = os.path.join(project_root, "web_viz_data")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(web_viz_dir, exist_ok=True)

    all_results = []

    for ep in range(args.episodes):
        obs, info = env.reset()
        episode_data = {
            "episode": ep + 1,
            "trajectory": [],
            "rewards": [],
            "steps": 0,
            "success": False,
            "final_distance": float("inf"),
        }
        total_reward = 0.0
        done = False

        while not done and episode_data["steps"] < args.max_steps:
            action, _ = model.predict(obs, deterministic=args.deterministic)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward

            robot_pos = env.unwrapped.data.qpos[7:9].copy()
            episode_data["trajectory"].append(robot_pos.tolist())
            episode_data["rewards"].append(float(reward))
            episode_data["steps"] += 1

            done = terminated or truncated

        episode_data["success"] = env.unwrapped.reached
        episode_data["final_distance"] = info.get("positional_error", float("inf"))
        episode_data["total_reward"] = total_reward
        episode_data["tennis_ball"] = env.unwrapped.goal.tolist()
        episode_data["court_width"] = env.unwrapped.court_width
        episode_data["court_length"] = env.unwrapped.court_length
        episode_data["goal_tolerance"] = env.unwrapped.goal_tolerance

        all_results.append(episode_data)
        print(f"Episode {ep+1}: steps={episode_data['steps']}, "
              f"reward={total_reward:.2f}, success={episode_data['success']}, "
              f"distance={episode_data['final_distance']:.4f}")

        json_path = os.path.join(web_viz_dir, f"episode_{ep+1}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(episode_data, f, indent=2)

        fig, ax = plt.subplots(1, 1, figsize=(8, 10))
        half_l = env.unwrapped.court_length / 2
        half_w = env.unwrapped.court_width / 2
        court = plt.Rectangle((-half_w, -half_l), 2 * half_w, 2 * half_l,
                              fill=False, edgecolor="green", linewidth=2)
        ax.add_patch(court)
        traj = np.array(episode_data["trajectory"])
        ax.plot(traj[:, 0], traj[:, 1], "b-", linewidth=1, label="Robot")
        ax.plot(traj[0, 0], traj[0, 1], "go", markersize=8, label="Start")
        ax.plot(traj[-1, 0], traj[-1, 1], "rx", markersize=8, label="End")
        ax.plot(env.unwrapped.goal[0], env.unwrapped.goal[1], "y*", markersize=12, label="Goal")
        ax.set_xlim(-half_w - 1, half_w + 1)
        ax.set_ylim(-half_l - 1, half_l + 1)
        ax.set_aspect("equal")
        ax.legend()
        ax.set_title(f"Episode {ep+1}: {'SUCCESS' if episode_data['success'] else 'FAIL'}")
        fig.savefig(os.path.join(results_dir, f"trajectory_{ep+1}.png"), dpi=100)
        plt.close(fig)

    success_rate = sum(r["success"] for r in all_results) / len(all_results)
    avg_reward = np.mean([r["total_reward"] for r in all_results])
    avg_steps = np.mean([r["steps"] for r in all_results])
    avg_distance = np.mean([r["final_distance"] for r in all_results])

    report = {
        "algorithm": algorithm,
        "model_path": args.model_path,
        "episodes": args.episodes,
        "success_rate": success_rate,
        "avg_reward": float(avg_reward),
        "avg_steps": float(avg_steps),
        "avg_final_distance": float(avg_distance),
        "deterministic": args.deterministic,
    }

    report_path = os.path.join(results_dir, "report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Evaluation Report")
    print(f"{'='*50}")
    print(f"Success Rate: {success_rate:.2%}")
    print(f"Avg Reward: {avg_reward:.2f}")
    print(f"Avg Steps: {avg_steps:.1f}")
    print(f"Avg Final Distance: {avg_distance:.4f}")
    print(f"Report saved to: {report_path}")

    env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate tennis-robot RL agent")
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--algorithm", type=str, default=None)
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--max_steps", type=int, default=2000)
    parser.add_argument("--deterministic", action="store_true", default=True)
    parser.add_argument("--version", type=str, default="v1")
    evaluate(parser.parse_args())

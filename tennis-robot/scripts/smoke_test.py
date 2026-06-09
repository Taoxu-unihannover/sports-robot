import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tennis_robot.envs.registration import register_envs
import gymnasium as gym


def smoke_test():
    register_envs()
    env = gym.make("TennisNavigation-v1")
    obs, info = env.reset()
    print(f"Reset: obs shape={obs.shape}, info keys={list(info.keys())}")

    for i in range(10):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            print(f"Episode ended at step {i+1}: terminated={terminated}, truncated={truncated}")
            break

    print(f"Step 10: reward={reward:.4f}, distance={info['positional_error']:.4f}")

    from stable_baselines3.common.env_checker import check_env
    check_env(env.unwrapped)
    print("check_env PASSED")

    env.close()
    print("Smoke test PASSED!")


if __name__ == "__main__":
    smoke_test()

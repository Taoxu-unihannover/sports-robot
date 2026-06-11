#!/usr/bin/env python3
"""
Real vs Sim 模式对比测试
测试 tennis-robot-v2 的 Real 模式感知管线
"""

import os
os.environ['MUJOCO_GL'] = 'osmesa'
os.environ['DISPLAY'] = ''

import sys
sys.path.insert(0, '/home/xutao/文档/sports-robot/tennis-robot-v2')

import numpy as np
from datetime import datetime

def test_sim_mode(model, env, n_episodes=20):
    """Sim 真值模式测试"""
    env.set_obs_mode('sim')
    print(f"\n{'='*60}")
    print(f"Sim Mode 测试 ({n_episodes} episodes)")
    print(f"{'='*60}")

    successes = 0
    total_reward = 0
    results = []

    for ep in range(n_episodes):
        obs, info = env.reset()
        ep_reward = 0
        done = False

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            ep_reward += reward
            done = terminated or truncated

        success = info.get('success', False)
        successes += int(success)
        total_reward += ep_reward
        results.append({'ep': ep+1, 'success': success, 'reward': ep_reward})

        if (ep + 1) % 5 == 0:
            print(f"  Episode {ep+1}: {'✅' if success else '❌'} Reward: {ep_reward:.1f}")

    sr = successes / n_episodes * 100
    avg_r = total_reward / n_episodes

    print(f"\n📊 Sim Mode Results:")
    print(f"  成功率: {sr:.1f}%")
    print(f"  平均奖励: {avg_r:.1f}")

    return {'success_rate': sr, 'avg_reward': avg_r, 'results': results}


def test_real_mode(model, env, n_episodes=20):
    """Real 图像模式测试"""
    env.set_obs_mode('real')
    print(f"\n{'='*60}")
    print(f"Real Mode 测试 ({n_episodes} episodes)")
    print(f"{'='*60}")

    successes = 0
    total_reward = 0
    detection_rates = []
    results = []

    for ep in range(n_episodes):
        obs, info = env.reset()
        ep_reward = 0
        ep_detections = 0
        ep_steps = 0
        done = False

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            ep_reward += reward
            ep_steps += 1

            # 记录检测状态
            if info.get('ball_detected', False):
                ep_detections += 1

            done = terminated or truncated

        success = info.get('success', False)
        det_rate = ep_detections / ep_steps if ep_steps > 0 else 0

        successes += int(success)
        total_reward += ep_reward
        detection_rates.append(det_rate)
        results.append({'ep': ep+1, 'success': success, 'reward': ep_reward, 'detection_rate': det_rate})

        if (ep + 1) % 5 == 0:
            print(f"  Episode {ep+1}: {'✅' if success else '❌'} Reward: {ep_reward:.1f}, Detection: {det_rate*100:.1f}%")

    sr = successes / n_episodes * 100
    avg_r = total_reward / n_episodes
    avg_det = np.mean(detection_rates) * 100

    print(f"\n📊 Real Mode Results:")
    print(f"  成功率: {sr:.1f}%")
    print(f"  平均奖励: {avg_r:.1f}")
    print(f"  平均检测率: {avg_det:.1f}%")

    return {'success_rate': sr, 'avg_reward': avg_r, 'avg_detection_rate': avg_det, 'results': results}


def main():
    from tennis_robot_v2.envs.tennis_navigation_v2_env import TennisNavigationV2Env
    from stable_baselines3 import SAC

    print("="*60)
    print("Tennis Robot V2: Real vs Sim Mode 对比测试")
    print("="*60)

    # 加载模型
    model_path = '/home/xutao/文档/sports-robot/tennis-robot-v2/saved_models/baseline/tennis_robot_v2_sac_final.zip'
    if not os.path.exists(model_path):
        print(f"❌ 模型不存在: {model_path}")
        print("使用随机策略进行测试...")
        model = None
    else:
        print(f"✅ 加载模型: {model_path}")
        model = SAC.load(model_path)

    # 创建环境
    print(f"\n创建测试环境...")
    env = TennisNavigationV2Env(render_mode='rgb_array')
    print(f"✅ 环境创建成功")
    print(f"   观测空间: {env.observation_space}")
    print(f"   动作空间: {env.action_space}")

    results = {}

    # Sim 模式测试
    sim_results = test_sim_mode(model, env, n_episodes=20)
    results['sim'] = sim_results

    # Real 模式测试
    real_results = test_real_mode(model, env, n_episodes=20)
    results['real'] = real_results

    # 打印对比表
    print(f"\n{'='*60}")
    print(f"📊 Real vs Sim 对比汇总")
    print(f"{'='*60}")
    print(f"{'模式':<10} {'成功率':<12} {'平均奖励':<14} {'检测率':<10}")
    print(f"{'-'*60}")
    print(f"{'Sim':<10} {sim_results['success_rate']:>10.1f}% {sim_results['avg_reward']:>13.1f} {'N/A':>9}")
    print(f"{'Real':<10} {real_results['success_rate']:>10.1f}% {real_results['avg_reward']:>13.1f} {real_results['avg_detection_rate']:>9.1f}%")

    gap = sim_results['success_rate'] - real_results['success_rate']
    print(f"\n{'='*60}")
    if gap > 0:
        print(f"⚠️  Sim→Real Gap: {gap:.1f}% (Real 模式性能下降)")
    else:
        print(f"✅ Real 模式性能与 Sim 持平或更好")
    print(f"{'='*60}")

    # 保存结果
    import json
    results_file = f'/home/xutao/文档/sports-robot/tennis-robot-v2/evaluation_results/real_sim_comparison_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.json'
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ 结果已保存到: {results_file}")

    env.close()


if __name__ == '__main__':
    main()
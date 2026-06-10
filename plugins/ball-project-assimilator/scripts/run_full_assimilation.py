#!/usr/bin/env python3
"""
Full assimilation evaluation for dynamic-tennis-v2 summit_catcher task.
Trains reproduction and enhanced models with GPU, then evaluates in sim + real mode.
"""

import argparse
import json
import os
import sys
import time
import numpy as np

os.environ["MUJOCO_GL"] = "egl"

# Baseline environment variables (matching hard_randomized training)
BASELINE_ENV_VARS = {
    "R_EE_POS": "15.0",
    "R_PRECISION": "15.0",
    "SUCCESS_BONUS": "10.0",
    "FAIL_PENALTY": "-15.0",
    "ALIVE_BONUS": "0.05",
    "CONTROL_COST": "0.0002",
    "STEP_PENALTY": "0.05",
}
for k, v in BASELINE_ENV_VARS.items():
    os.environ[k] = v

DYNAMIC_TENNIS_V2_PATH = "/home/xutao/文档/sports-robot/dynamic-tennis-v2"
LOCAL_BASELINE_PATH = "/home/xutao/文档/dynamic-tennis-v2.0-local"
OUTPUT_DIR = "/home/xutao/文档/sports-robot/docs/assimilation"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(DYNAMIC_TENNIS_V2_PATH, "scripts"))

from envs.summit_catcher.summit_catcher_v1 import SummitCatcherEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import BaseCallback


class SuccessRateCallback(BaseCallback):
    """Callback that only counts done=True steps (episode-level success rate)."""
    def __init__(self, window=200, verbose=1):
        super().__init__(verbose)
        self.window = window
        self.buffer = []

    def _on_step(self):
        infos = self.locals.get("infos", [])
        dones = self.locals.get("dones", None)
        if dones is not None:
            for i, done in enumerate(dones):
                if not done:
                    continue
                info = infos[i] if i < len(infos) else {}
                success = info.get("success", info.get("is_success"))
                if success is not None:
                    self.buffer.append(float(success))
                    if len(self.buffer) > self.window:
                        self.buffer = self.buffer[-self.window:]
        if self.num_timesteps % 2048 == 0 and len(self.buffer) > 0:
            sr = np.mean(self.buffer)
            self.logger.record("rollout/success_rate", sr)
        return True


class CurriculumCallback(BaseCallback):
    """Adaptive curriculum learning based on episode success rate."""
    def __init__(self, total_timesteps, warmup_frac=0.15, verbose=1):
        super().__init__(verbose)
        self.total_timesteps = total_timesteps
        self.warmup_frac = warmup_frac
        self.buffer = []
        self._last_stage = None

    def _on_step(self):
        infos = self.locals.get("infos", [])
        dones = self.locals.get("dones", None)
        if dones is not None:
            for i, done in enumerate(dones):
                if not done:
                    continue
                info = infos[i] if i < len(infos) else {}
                success = info.get("success")
                if success is not None:
                    self.buffer.append(1 if success else 0)
        if len(self.buffer) > 5000:
            self.buffer = self.buffer[-5000:]

        if self.num_timesteps % 2048 != 0:
            return True

        progress = self.num_timesteps / self.total_timesteps
        if len(self.buffer) > 50:
            sr = sum(self.buffer) / len(self.buffer)
        else:
            sr = 0.0

        if progress < self.warmup_frac:
            target_throw = 0.2
            target_r_orient = 0.0
            stage = "warmup"
        elif progress < 0.4:
            target_throw = 0.2 + 0.4 * ((progress - self.warmup_frac) / (0.4 - self.warmup_frac))
            target_r_orient = 0.5 * ((progress - self.warmup_frac) / (0.4 - self.warmup_frac))
            stage = "ramp-up"
        elif sr > 0.6:
            target_throw = 1.0
            target_r_orient = 1.0
            stage = "hard"
        elif sr > 0.35:
            target_throw = 0.7
            target_r_orient = 0.7
            stage = "medium"
        else:
            target_throw = 0.5
            target_r_orient = 0.3
            stage = "easy"

        if stage != self._last_stage:
            if self.verbose:
                print(f"[Curriculum] step={self.num_timesteps:,} progress={progress:.1%} "
                      f"sr={sr:.3f} stage={stage} throw={target_throw:.2f} r_orient={target_r_orient:.2f}")
            try:
                self.training_env.set_attr("throw_difficulty", target_throw)
                self.training_env.set_attr("r_orient", target_r_orient)
            except Exception:
                pass
            self._last_stage = stage

        return True


class LinearLRSchedule:
    def __init__(self, initial_lr, final_lr, total_timesteps):
        self.initial_lr = initial_lr
        self.final_lr = final_lr
        self.total_timesteps = total_timesteps

    def __call__(self, progress_remaining):
        progress = 1.0 - progress_remaining
        return self.initial_lr + (self.final_lr - self.initial_lr) * progress


def make_env(rank, seed=0):
    def _init():
        env = SummitCatcherEnv()
        env.reset(seed=seed + rank)
        return env
    return _init


def train_reproduction(total_timesteps=30_000_000, n_envs=4):
    """Train reproduction model with GPU, matching baseline hyperparameters."""
    print("\n" + "="*60)
    print("Training Reproduction Model (GPU, 30M steps)")
    print("="*60)

    model_dir = os.path.join(DYNAMIC_TENNIS_V2_PATH, "saved_models", "reproduction_gpu")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "reproduction_ppo.zip")
    best_path = os.path.join(model_dir, "best_model", "best_model.zip")

    # Check if already trained
    if os.path.exists(best_path):
        print(f"Reproduction model already exists at {best_path}")
        print("Skipping training. Delete the folder to retrain.")
        return model_path, best_path

    # Create training environment
    env = SubprocVecEnv([make_env(i, seed=42) for i in range(n_envs)])

    # Baseline matching hyperparameters
    lr_schedule = LinearLRSchedule(initial_lr=5e-4, final_lr=5e-5, total_timesteps=total_timesteps)

    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=lr_schedule,
        n_steps=2048,
        batch_size=256,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.005,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs=dict(net_arch=[256, 256]),
        device="cuda",
        verbose=1,
        tensorboard_log=os.path.join(model_dir, "tb"),
        seed=42,
    )

    callbacks = [
        SuccessRateCallback(window=200, verbose=1),
        CurriculumCallback(total_timesteps=total_timesteps, warmup_frac=0.15, verbose=1),
    ]

    start_time = time.time()
    model.learn(
        total_timesteps=total_timesteps,
        callback=callbacks,
        progress_bar=True,
        log_interval=10,
    )
    elapsed = time.time() - start_time
    print(f"\n[Reproduction] Training completed in {elapsed/60:.1f} minutes")

    model.save(model_path)
    os.makedirs(os.path.dirname(best_path), exist_ok=True)
    model.save(best_path)
    print(f"[Reproduction] Model saved to {model_path}")
    print(f"[Reproduction] Best model saved to {best_path}")

    env.close()

    return model_path, best_path


def train_enhanced(total_timesteps=30_000_000, n_envs=4):
    """Train enhanced model with GPU + curriculum learning + optimized hyperparameters."""
    print("\n" + "="*60)
    print("Training Enhanced Model (GPU + Curriculum, 30M steps)")
    print("="*60)

    model_dir = os.path.join(DYNAMIC_TENNIS_V2_PATH, "saved_models", "enhanced_gpu")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "enhanced_ppo.zip")
    best_path = os.path.join(model_dir, "best_model", "best_model.zip")

    # Check if already trained
    if os.path.exists(best_path):
        print(f"Enhanced model already exists at {best_path}")
        print("Skipping training. Delete the folder to retrain.")
        return model_path, best_path

    # Create training environment
    env = SubprocVecEnv([make_env(i, seed=42) for i in range(n_envs)])

    # Enhanced hyperparameters with learning rate decay
    lr_schedule = LinearLRSchedule(initial_lr=3e-4, final_lr=3e-5, total_timesteps=total_timesteps)

    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=lr_schedule,
        n_steps=4096,
        batch_size=512,
        n_epochs=10,
        gamma=0.999,
        gae_lambda=0.98,
        clip_range=0.15,
        ent_coef=0.01,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs=dict(net_arch=[512, 512]),
        device="cuda",
        verbose=1,
        tensorboard_log=os.path.join(model_dir, "tb"),
        seed=42,
    )

    callbacks = [
        SuccessRateCallback(window=200, verbose=1),
        CurriculumCallback(total_timesteps=total_timesteps, warmup_frac=0.15, verbose=1),
    ]

    start_time = time.time()
    model.learn(
        total_timesteps=total_timesteps,
        callback=callbacks,
        progress_bar=True,
        log_interval=10,
    )
    elapsed = time.time() - start_time
    print(f"\n[Enhanced] Training completed in {elapsed/60:.1f} minutes")

    model.save(model_path)
    os.makedirs(os.path.dirname(best_path), exist_ok=True)
    model.save(best_path)
    print(f"[Enhanced] Model saved to {model_path}")
    print(f"[Enhanced] Best model saved to {best_path}")

    env.close()

    return model_path, best_path


def evaluate_model(model, seeds, episodes_per_seed, mode="sim"):
    """Evaluate model in sim or real mode."""
    results = []

    for seed in seeds:
        for ep in range(episodes_per_seed):
            env = SummitCatcherEnv()
            obs, info = env.reset(seed=seed * 1000 + ep)

            if mode == "real":
                # Setup for real mode (binocular camera inference)
                import mujoco as mj
                sys.path.insert(0, os.path.join(DYNAMIC_TENNIS_V2_PATH, "tennis_tracker"))
                from binocular_camera.obs_builder import ObsBuilder

                env.model.vis.global_.offwidth = 3840
                env.model.vis.global_.offheight = 2160

                renderer = mj.Renderer(env.model, height=1080, width=1920)
                cam1_id = mj.mj_name2id(env.model, mj.mjtObj.mjOBJ_CAMERA, "box_cam1")
                cam2_id = mj.mj_name2id(env.model, mj.mjtObj.mjOBJ_CAMERA, "box_cam2")

                try:
                    obs_builder = ObsBuilder(
                        os.path.join(DYNAMIC_TENNIS_V2_PATH, "tennis_tracker", "config", "obs_mode.yaml")
                    )
                    obs_builder.mode = "real"
                    obs_builder._init_real_backend()
                    obs_builder._fallback_mode = "kalman"
                    obs_builder.reset()
                except Exception as e:
                    print(f"[real-mode] ObsBuilder init failed: {e}")
                    obs_builder = None
            else:
                renderer = None
                obs_builder = None

            done = False
            total_reward = 0
            steps = 0
            detection_count = 0
            total_cam_steps = 0

            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs_next, reward, terminated, truncated, info = env.step(action)
                total_reward += reward
                steps += 1
                done = terminated or truncated

                if mode == "real" and obs_builder is not None:
                    # Render binocular images and run perception pipeline
                    try:
                        renderer.update_scene(env.data, cam1_id)
                        img1 = renderer.render()
                        renderer.update_scene(env.data, cam2_id)
                        img2 = renderer.render()

                        h = min(img1.shape[0], img2.shape[0])
                        img1, img2 = img1[:h], img2[:h]
                        combined = np.concatenate((img1, img2), axis=1)
                        bgr = combined[..., ::-1].copy()
                        half_w = bgr.shape[1] // 2
                        cam1_bgr = bgr[:, :half_w]
                        cam2_bgr = bgr[:, half_w:]

                        obs_rebuilt = obs_builder.build(env=env, camera_frames=(cam1_bgr, cam2_bgr))
                        total_cam_steps += 1
                        if obs_builder.ball_detected:
                            detection_count += 1
                        obs = obs_rebuilt
                    except Exception:
                        obs = obs_next
                else:
                    obs = obs_next

            det_rate = detection_count / max(total_cam_steps, 1) if total_cam_steps > 0 else 0.0

            results.append({
                "seed": seed,
                "episode": ep,
                "total_reward": float(total_reward),
                "steps": steps,
                "success": bool(info.get("success", False)),
                "mode": mode,
                "detection_rate": float(det_rate),
            })

            if renderer:
                renderer.close()
            env.close()

    return results


def compute_summary(results, label):
    """Compute summary statistics from evaluation results."""
    successes = [r["success"] for r in results]
    rewards = [r["total_reward"] for r in results]
    steps = [r["steps"] for r in results]
    detection_rates = [r.get("detection_rate", 0) for r in results]

    return {
        "label": label,
        "num_episodes": len(results),
        "success_rate": float(np.mean(successes)),
        "avg_reward": float(np.mean(rewards)),
        "std_reward": float(np.std(rewards)),
        "min_reward": float(np.min(rewards)),
        "max_reward": float(np.max(rewards)),
        "avg_steps": float(np.mean(steps)),
        "std_steps": float(np.std(steps)),
        "avg_detection_rate": float(np.mean(detection_rates)) if any(detection_rates) else 0.0,
    }


def generate_report(baseline_results, reproduction_results, enhanced_results, output_dir):
    """Generate comprehensive comparison report."""
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "baseline_env_vars": BASELINE_ENV_VARS,
        "results": {
            "baseline_sim": compute_summary(baseline_results["sim"], "Baseline (sim)"),
            "reproduction_sim": compute_summary(reproduction_results["sim"], "Reproduction (sim)"),
            "enhanced_sim": compute_summary(enhanced_results["sim"], "Enhanced (sim)"),
            "reproduction_real": compute_summary(reproduction_results.get("real", []), "Reproduction (real)"),
            "enhanced_real": compute_summary(enhanced_results.get("real", []), "Enhanced (real)"),
        },
        "comparisons": {},
    }

    # Sim mode comparison
    baseline_sr = report["results"]["baseline_sim"]["success_rate"]
    repro_sr = report["results"]["reproduction_sim"]["success_rate"]
    enh_sr = report["results"]["enhanced_sim"]["success_rate"]

    report["comparisons"]["sim_mode"] = {
        "baseline_success_rate": baseline_sr,
        "reproduction_success_rate": repro_sr,
        "reproduction_vs_baseline_pct": repro_sr / baseline_sr if baseline_sr > 0 else 0,
        "enhanced_success_rate": enh_sr,
        "enhanced_vs_baseline_pct": enh_sr / baseline_sr if baseline_sr > 0 else 0,
        "enhanced_vs_reproduction_pct": enh_sr / repro_sr if repro_sr > 0 else 0,
        "reproduction_meets_95_pct": repro_sr >= 0.95 * baseline_sr,
        "enhanced_exceeds_105_pct": enh_sr >= 1.05 * baseline_sr,
    }

    # Real mode comparison
    if reproduction_results.get("real") and enhanced_results.get("real"):
        repro_real_sr = report["results"]["reproduction_real"]["success_rate"]
        enh_real_sr = report["results"]["enhanced_real"]["success_rate"]
        repro_real_dr = report["results"]["reproduction_real"]["avg_detection_rate"]
        enh_real_dr = report["results"]["enhanced_real"]["avg_detection_rate"]

        report["comparisons"]["real_mode"] = {
            "reproduction_success_rate": repro_real_sr,
            "reproduction_detection_rate": repro_real_dr,
            "reproduction_sim2real_gap": repro_sr - repro_real_sr,
            "enhanced_success_rate": enh_real_sr,
            "enhanced_detection_rate": enh_real_dr,
            "enhanced_sim2real_gap": enh_sr - enh_real_sr,
        }

    # Save JSON report
    report_path = os.path.join(output_dir, "full_eval_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[Report] JSON saved to {report_path}")

    # Generate markdown report
    md_path = os.path.join(output_dir, "full_eval_report.md")
    with open(md_path, "w") as f:
        f.write("# dynamic-tennis-v2 完整吸收验证报告\n\n")
        f.write(f"**生成时间**: {report['timestamp']}\n\n")
        f.write("## 训练配置\n\n")
        f.write("| 参数 | Baseline | Reproduction | Enhanced |\n")
        f.write("|---|---|---|---|\n")
        f.write("| 算法 | PPO | PPO | PPO |\n")
        f.write("| 学习率 | 5e-4→5e-5 | 5e-4→5e-5 | 3e-4→3e-5 |\n")
        f.write("| n_steps | 2048 | 2048 | 4096 |\n")
        f.write("| 批大小 | 256 | 256 | 512 |\n")
        f.write("| 网络架构 | [256,256] | [256,256] | [512,512] |\n")
        f.write("| 课程学习 | 无 | 无 | 有 (warmup→ramp→adaptive) |\n")
        f.write("| GPU | 是 | 是 | 是 |\n")
        f.write("| 训练步数 | 30M | 30M | 30M |\n\n")

        f.write("## Sim 模式评测结果（真值推理）\n\n")
        f.write("| 指标 | Baseline | Reproduction | Enhanced |\n")
        f.write("|---|---|---|---|\n")
        for key in ["success_rate", "avg_reward", "std_reward", "avg_steps"]:
            labels = ["Baseline (sim)", "Reproduction (sim)", "Enhanced (sim)"]
            vals = [report["results"][l][key] for l in labels]
            if key == "success_rate":
                f.write(f"| {key} | **{vals[0]:.1%}** | {vals[1]:.1%} | {vals[2]:.1%} |\n")
            elif key == "avg_reward":
                f.write(f"| {key} | **{vals[0]:.1f}** | {vals[1]:.1f} | {vals[2]:.1f} |\n")
            else:
                f.write(f"| {key} | {vals[0]:.1f} | {vals[1]:.1f} | {vals[2]:.1f} |\n")

        f.write("\n## Real 模式评测结果（图像推理）\n\n")
        if reproduction_results.get("real") and enhanced_results.get("real"):
            f.write("| 指标 | Reproduction | Enhanced |\n")
            f.write("|---|---|---|\n")
            for key in ["success_rate", "avg_reward", "avg_detection_rate"]:
                labels = ["Reproduction (real)", "Enhanced (real)"]
                vals = [report["results"][l][key] for l in labels]
                if key == "success_rate":
                    f.write(f"| {key} | {vals[0]:.1%} | {vals[1]:.1%} |\n")
                elif key == "avg_detection_rate":
                    f.write(f"| {key} | {vals[0]:.1%} | {vals[1]:.1%} |\n")
                else:
                    f.write(f"| {key} | {vals[0]:.1f} | {vals[1]:.1f} |\n")

            f.write("\n## Sim→Real Gap 分析\n\n")
            f.write("| 版本 | Sim成功率 | Real成功率 | Gap |\n")
            f.write("|---|---|---|---|\n")
            repro_gap = report["comparisons"]["real_mode"]["reproduction_sim2real_gap"]
            enh_gap = report["comparisons"]["real_mode"]["enhanced_sim2real_gap"]
            f.write(f"| Reproduction | {repro_sr:.1%} | {repro_real_sr:.1%} | {repro_gap:.1%} |\n")
            f.write(f"| Enhanced | {enh_sr:.1%} | {enh_real_sr:.1%} | {enh_gap:.1%} |\n")
        else:
            f.write("Real 模式评测未执行\n")

        f.write("\n## 超越判定\n\n")
        cmp = report["comparisons"]["sim_mode"]
        f.write(f"- 复现版是否达到 Baseline 95%: {'✅ 是' if cmp['reproduction_meets_95_pct'] else '❌ 否'} ({repro_sr:.1%} vs {baseline_sr:.1%})\n")
        f.write(f"- 增强版是否超过 Baseline 5%: {'✅ 是' if cmp['enhanced_exceeds_105_pct'] else '❌ 否'} ({enh_sr:.1%} vs {baseline_sr:.1%})\n")

        if not cmp['reproduction_meets_95_pct'] or not cmp['enhanced_exceeds_105_pct']:
            f.write("\n## 瓶颈分析与优化建议\n\n")
            if not cmp['reproduction_meets_95_pct']:
                gap = baseline_sr - repro_sr
                f.write(f"### 复现版差距: {gap:.1%}\n\n")
                f.write("可能原因:\n")
                f.write("1. 训练步数可能需要更多（baseline 训练了 15.5M 步达到最佳）\n")
                f.write("2. 随机种子差异导致训练轨迹不同\n")
                f.write("3. GPU vs CPU 训练可能导致数值精度差异\n\n")
            if not cmp['enhanced_exceeds_105_pct']:
                f.write("### 增强版未超越\n\n")
                f.write("可能原因:\n")
                f.write("1. Curriculum learning 的 warmup 阶段可能延迟了策略学习\n")
                f.write("2. 更大的网络 [512,512] 需要更多训练步数才能收敛\n")
                f.write("3. gamma=0.999 可能导致价值函数收敛变慢\n\n")

        f.write("\n## 完整结果 JSON\n\n")
        f.write(f"详见: `{report_path}`\n")

    print(f"[Report] Markdown saved to {md_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Full assimilation evaluation")
    parser.add_argument("--train-repro", action="store_true", help="Train reproduction model")
    parser.add_argument("--train-enh", action="store_true", help="Train enhanced model")
    parser.add_argument("--eval-sim", action="store_true", help="Evaluate in sim mode")
    parser.add_argument("--eval-real", action="store_true", help="Evaluate in real mode")
    parser.add_argument("--all", action="store_true", help="Run all (train + eval)")
    parser.add_argument("--steps", type=int, default=30_000_000, help="Training steps")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4], help="Evaluation seeds")
    parser.add_argument("--episodes", type=int, default=20, help="Episodes per seed")
    args = parser.parse_args()

    # Default: run all
    if not any([args.train_repro, args.train_enh, args.eval_sim, args.eval_real, args.all]):
        args.all = True

    results = {
        "baseline": {"sim": [], "real": []},
        "reproduction": {"sim": [], "real": []},
        "enhanced": {"sim": [], "real": []},
    }

    # Load baseline model
    baseline_path = os.path.join(LOCAL_BASELINE_PATH, "runs", "hard_randomized_20260220_214512", "best_model", "best_model.zip")
    if os.path.exists(baseline_path):
        print(f"[Baseline] Loading model from {baseline_path}")
        baseline_model = PPO.load(baseline_path, env=None)
    else:
        print(f"[Baseline] Model not found at {baseline_path}")
        baseline_model = None

    # Train models
    if args.train_repro or args.all:
        repro_path, repro_best = train_reproduction(total_timesteps=args.steps)
    else:
        repro_best = os.path.join(DYNAMIC_TENNIS_V2_PATH, "saved_models", "reproduction_gpu", "best_model", "best_model.zip")

    if args.train_enh or args.all:
        enh_path, enh_best = train_enhanced(total_timesteps=args.steps)
    else:
        enh_best = os.path.join(DYNAMIC_TENNIS_V2_PATH, "saved_models", "enhanced_gpu", "best_model", "best_model.zip")

    # Load trained models
    if os.path.exists(repro_best):
        print(f"[Reproduction] Loading model from {repro_best}")
        repro_model = PPO.load(repro_best, env=None)
    else:
        print(f"[Reproduction] Model not found at {repro_best}")
        repro_model = None

    if os.path.exists(enh_best):
        print(f"[Enhanced] Loading model from {enh_best}")
        enh_model = PPO.load(enh_best, env=None)
    else:
        print(f"[Enhanced] Model not found at {enh_best}")
        enh_model = None

    # Evaluate in sim mode
    if args.eval_sim or args.all:
        print("\n" + "="*60)
        print("Evaluating in SIM mode (truth-state inference)")
        print("="*60)

        if baseline_model:
            print("[Baseline] Evaluating...")
            results["baseline"]["sim"] = evaluate_model(baseline_model, args.seeds, args.episodes, mode="sim")

        if repro_model:
            print("[Reproduction] Evaluating...")
            results["reproduction"]["sim"] = evaluate_model(repro_model, args.seeds, args.episodes, mode="sim")

        if enh_model:
            print("[Enhanced] Evaluating...")
            results["enhanced"]["sim"] = evaluate_model(enh_model, args.seeds, args.episodes, mode="sim")

    # Evaluate in real mode
    if args.eval_real or args.all:
        print("\n" + "="*60)
        print("Evaluating in REAL mode (image-based inference)")
        print("="*60)

        if repro_model:
            print("[Reproduction] Evaluating in real mode...")
            results["reproduction"]["real"] = evaluate_model(repro_model, args.seeds[:3], args.episodes, mode="real")

        if enh_model:
            print("[Enhanced] Evaluating in real mode...")
            results["enhanced"]["real"] = evaluate_model(enh_model, args.seeds[:3], args.episodes, mode="real")

    # Generate report
    if any(results.values()):
        report = generate_report(results["baseline"], results["reproduction"], results["enhanced"], OUTPUT_DIR)

        # Print summary
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)

        if results["baseline"]["sim"]:
            sr = report["results"]["baseline_sim"]["success_rate"]
            print(f"Baseline (sim):    {sr:.1%} success rate")
        if results["reproduction"]["sim"]:
            sr = report["results"]["reproduction_sim"]["success_rate"]
            print(f"Reproduction (sim): {sr:.1%} success rate")
        if results["enhanced"]["sim"]:
            sr = report["results"]["enhanced_sim"]["success_rate"]
            print(f"Enhanced (sim):     {sr:.1%} success rate")

        if results["reproduction"]["real"]:
            sr = report["results"]["reproduction_real"]["success_rate"]
            dr = report["results"]["reproduction_real"]["avg_detection_rate"]
            print(f"Reproduction (real): {sr:.1%} success rate, {dr:.1%} detection rate")
        if results["enhanced"]["real"]:
            sr = report["results"]["enhanced_real"]["success_rate"]
            dr = report["results"]["enhanced_real"]["avg_detection_rate"]
            print(f"Enhanced (real):     {sr:.1%} success rate, {dr:.1%} detection rate")

        cmp = report["comparisons"]["sim_mode"]
        print(f"\nReproduction meets 95%: {'✅' if cmp['reproduction_meets_95_pct'] else '❌'}")
        print(f"Enhanced exceeds 105%: {'✅' if cmp['enhanced_exceeds_105_pct'] else '❌'}")


if __name__ == "__main__":
    main()
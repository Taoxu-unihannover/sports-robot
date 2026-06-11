#!/usr/bin/env python3
"""
Test real-mode perception pipeline for tennis-robot-v2.

Tests:
  1. SimBallDetector - HSV-based ball detection
  2. ObjectKalmanFilter - Ball state estimation
  3. StereoDepthEstimator - Depth from stereo images
  4. TennisRobotV2ObsBuilder - Full observation builder
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np


def test_sim_ball_detector():
    """Test SimBallDetector."""
    print("=== Testing SimBallDetector ===")

    from tennis_robot_v2.perception.real_mode_perception import SimBallDetector

    # Create detector
    detector = SimBallDetector(min_area=3, max_area=4000)

    # Create synthetic test image with green ball
    import cv2

    # Create blank image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw green circle (tennis ball)
    cv2.circle(img, (320, 240), 20, (80, 180, 80), -1)

    # Test detection
    result = detector.detect(img)

    assert result is not None, "Detection failed on synthetic image"
    assert "cx" in result, "Missing centroid x"
    assert "cy" in result, "Missing centroid y"
    assert "area" in result, "Missing area"
    assert abs(result["cx"] - 320) < 5, f"Cx mismatch: {result['cx']}"
    assert abs(result["cy"] - 240) < 5, f"Cy mismatch: {result['cy']}"

    print(f"  Detected ball at ({result['cx']:.1f}, {result['cy']:.1f}), area={result['area']:.0f}")
    print("✓ SimBallDetector test passed")


def test_kalman_filter():
    """Test ObjectKalmanFilter."""
    print("\n=== Testing ObjectKalmanFilter ===")

    from tennis_robot_v2.perception.real_mode_perception import ObjectKalmanFilter

    kf = ObjectKalmanFilter(dt=1/60, process_noise=0.05, measurement_noise=0.08)

    # Simulate ball trajectory with gravity
    true_pos = np.array([0.0, 5.0, 1.5])
    true_vel = np.array([0.0, -4.0, 1.0])
    dt = 1.0 / 60.0
    errors_pos = []
    errors_vel = []

    print(f"  {'Frame':>5} {'True z':>8} {'Filter z':>8} {'Err z':>8}")
    print("  " + "-" * 35)

    for i in range(30):
        # Physics step (with gravity)
        true_vel[2] += -9.81 * dt
        true_pos += true_vel * dt

        # Add noise
        noisy_pos = true_pos + np.random.normal(0, 0.05, 3)

        # Kalman update
        result = kf.update(noisy_pos)

        err_pos = np.linalg.norm(result["position"] - true_pos)
        err_vel = np.linalg.norm(result["velocity"] - true_vel)
        errors_pos.append(err_pos)
        errors_vel.append(err_vel)

        if i % 10 == 0:
            print(f"  {i:5d} {true_pos[2]:8.3f} {result['position'][2]:8.3f} {err_pos:8.4f}")

    mean_err = float(np.mean(errors_pos))
    max_err = float(np.max(errors_pos))

    print(f"\n  Mean position error: {mean_err:.4f} m")
    print(f"  Max position error: {max_err:.4f} m")

    assert mean_err < 0.3, f"Kalman mean error too large: {mean_err:.4f}"
    print("✓ Kalman filter test passed")


def test_coriolis_velocity():
    """Test Coriolis velocity computation."""
    print("\n=== Testing Coriolis Velocity ===")

    from tennis_robot_v2.perception.real_mode_perception import compute_coriolis_velocity

    # Test case: robot rotating
    ball_pos_base = np.array([2.0, 1.0, 0.5])
    ball_vel_base = np.array([0.0, -3.0, 0.0])
    robot_yaw = 0.5  # 0.5 rad
    robot_vx = 1.0
    robot_vy = 0.0
    robot_wz = 0.3  # rotating

    ball_v_world = compute_coriolis_velocity(
        ball_pos_base, ball_vel_base,
        robot_yaw, robot_vx, robot_vy, robot_wz
    )

    print(f"  Ball position (base): {ball_pos_base}")
    print(f"  Ball velocity (base): {ball_vel_base}")
    print(f"  Robot yaw: {robot_yaw:.3f} rad")
    print(f"  Robot angular velocity: {robot_wz:.3f} rad/s")
    print(f"  Ball velocity (world): {ball_v_world}")

    assert ball_v_world.shape == (2,), f"Wrong output shape: {ball_v_world.shape}"
    assert not np.isnan(ball_v_world).any(), "NaN in velocity"
    assert not np.isinf(ball_v_world).any(), "Inf in velocity"

    print("✓ Coriolis velocity test passed")


def test_obs_builder():
    """Test TennisRobotV2ObsBuilder."""
    print("\n=== Testing TennisRobotV2ObsBuilder ===")

    from tennis_robot_v2.perception.real_mode_perception import TennisRobotV2ObsBuilder

    config = {
        "obs_mode": "real",
        "v_max_x": 5.0,
        "v_max_y": 2.0,
        "w_max": 1.5,
        "court_diagonal": 14.45,
    }

    builder = TennisRobotV2ObsBuilder(config)

    assert builder.mode == "real", f"Wrong mode: {builder.mode}"
    assert builder.detector is not None, "Detector not initialized"
    assert builder.depth_estimator is not None, "Depth estimator not initialized"
    assert builder.kalman is not None, "Kalman filter not initialized"

    print(f"  Mode: {builder.mode}")
    print(f"  Detector: {type(builder.detector).__name__}")
    print(f"  Depth estimator: {type(builder.depth_estimator).__name__}")
    print(f"  Kalman filter: {type(builder.kalman).__name__}")

    # Test reset
    builder.reset()
    assert builder._last_ball_pos is None, "Reset failed"
    assert builder._last_ball_vel is None, "Reset failed"

    print("✓ ObsBuilder test passed")


def test_environment_integration():
    """Test environment with real mode support."""
    print("\n=== Testing Environment Real Mode ===")

    import gymnasium as gym
    from tennis_robot_v2.envs.registration import register as _reg

    env = gym.make("TennisNavigationV2-v1")

    # Check real mode support
    assert hasattr(env.unwrapped, "set_obs_mode"), "set_obs_mode not found"
    assert hasattr(env.unwrapped, "render_binocular"), "render_binocular not found"
    assert hasattr(env.unwrapped, "obs_builder"), "obs_builder not found"

    # Test sim mode (default)
    assert env.unwrapped.obs_mode == "sim", f"Wrong default mode: {env.unwrapped.obs_mode}"

    # Test switching to real mode
    env.unwrapped.set_obs_mode("real")
    assert env.unwrapped.obs_mode == "real", f"Mode switch failed: {env.unwrapped.obs_mode}"

    # Test reset
    obs, info = env.reset()
    assert obs.shape == (12,), f"Wrong obs shape: {obs.shape}"

    # Test step
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    assert obs.shape == (12,), f"Wrong obs shape: {obs.shape}"
    assert "obs_mode" in info, "obs_mode not in info"

    # Switch back to sim mode
    env.unwrapped.set_obs_mode("sim")
    assert env.unwrapped.obs_mode == "sim", "Mode switch back failed"

    env.close()

    print(f"  Default mode: sim")
    print(f"  Real mode available: True")
    print(f"  Observation shape: (12,)")
    print("✓ Environment integration test passed")


def main():
    print("=" * 60)
    print("Real-Mode Perception Pipeline Tests")
    print("=" * 60)

    try:
        test_sim_ball_detector()
        test_kalman_filter()
        test_coriolis_velocity()
        test_obs_builder()
        test_environment_integration()

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("  Real-mode perception module not available")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
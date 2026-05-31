"""
Full Perception Pipeline

Integrates all four modules:
  Module 1: Detector  → 2D ball centers
  Module 2: Tracker   → smoothed 2D trajectory
  Module 3: Filter    → filtered state [p, v]
  Module 4: Geometry  → 3D position/velocity

Usage:
  python pipeline.py --config ../assets/config.yaml
  python pipeline.py --config ../assets/config.yaml --video path/to/video.mp4
  python pipeline.py --config ../assets/config.yaml --images path/to/images/
"""

import argparse
import time
import sys
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple

import cv2
import numpy as np
import yaml

_SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills")
sys.path.insert(0, os.path.join(_SKILLS_DIR, "ball-detector", "scripts"))
sys.path.insert(0, os.path.join(_SKILLS_DIR, "ball-tracker", "scripts"))
sys.path.insert(0, os.path.join(_SKILLS_DIR, "ball-filter", "scripts"))
sys.path.insert(0, os.path.join(_SKILLS_DIR, "ball-geometry", "scripts"))

from detector import BallDetector, HSVColorDetector, DetectionResult
from tracker import TrajectoryTracker, TrackPoint
from filter import BallKalmanFilter, BallState
from geometry import Triangulator, CameraConfig, CoordinateTransformer


class PerceptionPipeline:
    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self._init_detectors()
        self._init_trackers()
        self._init_filters()
        self._init_geometry()

        self.frame_count = 0
        self.fps_history: List[float] = []

    def _init_detectors(self):
        det_cfg = self.config.get("detector", {})
        det_type = det_cfg.get("type", "yolo")

        self.detectors: Dict[str, object] = {}
        for cam_cfg in self.config.get("cameras", []):
            cam_id = cam_cfg["id"]
            if det_type == "yolo":
                detector = BallDetector(
                    model_path=det_cfg.get("model_path", "yolov8n.pt"),
                    input_size=det_cfg.get("input_size", 1024),
                    confidence_threshold=det_cfg.get("confidence_threshold", 0.25),
                    max_det=det_cfg.get("max_det", 1),
                    device=det_cfg.get("device", "cpu"),
                )
            elif det_type == "hsv":
                hsv_cfg = det_cfg.get("hsv", {})
                detector = HSVColorDetector(
                    lower_hsv=tuple(hsv_cfg.get("lower", [30, 50, 50])),
                    upper_hsv=tuple(hsv_cfg.get("upper", [90, 255, 255])),
                    min_area=hsv_cfg.get("min_area", 10),
                    max_area=hsv_cfg.get("max_area", 5000),
                )
            else:
                raise ValueError(f"Unknown detector type: {det_type}")
            self.detectors[cam_id] = detector

    def _init_trackers(self):
        trk_cfg = self.config.get("tracker", {})
        self.trackers: Dict[str, TrajectoryTracker] = {}
        for cam_cfg in self.config.get("cameras", []):
            cam_id = cam_cfg["id"]
            self.trackers[cam_id] = TrajectoryTracker(
                window_size=trk_cfg.get("window_size", 5),
                max_gap=trk_cfg.get("max_gap", 3),
                max_velocity=trk_cfg.get("max_velocity", 500.0),
                use_prediction=trk_cfg.get("use_prediction", True),
            )

    def _init_filters(self):
        flt_cfg = self.config.get("filter", {})
        dim = flt_cfg.get("dim", 2)
        self.filter_2d: Dict[str, BallKalmanFilter] = {}
        for cam_cfg in self.config.get("cameras", []):
            cam_id = cam_cfg["id"]
            self.filter_2d[cam_id] = BallKalmanFilter(
                dt=flt_cfg.get("dt", 1.0 / 125.0),
                dim=dim,
                process_noise=flt_cfg.get("process_noise", 1.0),
                measurement_noise=flt_cfg.get("measurement_noise", 10.0),
                model=flt_cfg.get("model", "CV"),
            )

        self.filter_3d = BallKalmanFilter(
            dt=flt_cfg.get("dt", 1.0 / 125.0),
            dim=3,
            process_noise=flt_cfg.get("process_noise_3d", 0.5),
            measurement_noise=flt_cfg.get("measurement_noise_3d", 5.0),
            model=flt_cfg.get("model", "CV"),
        )

    def _init_geometry(self):
        geo_cfg = self.config.get("geometry", {})
        camera_configs = []
        for cam_cfg in self.config.get("cameras", []):
            K = np.array(cam_cfg["K"])
            dist = np.array(cam_cfg.get("dist_coeffs", [0, 0, 0, 0, 0]))
            R = np.array(cam_cfg["R"])
            t = np.array(cam_cfg["t"])
            camera_configs.append(
                CameraConfig(
                    camera_id=cam_cfg["id"],
                    width=cam_cfg["width"],
                    height=cam_cfg["height"],
                    K=K,
                    dist_coeffs=dist,
                    R=R,
                    t=t,
                )
            )

        self.triangulator = Triangulator(
            camera_configs, method=geo_cfg.get("method", "DLT")
        )

        T = geo_cfg.get("T_cam_to_world", None)
        if T is not None:
            T = np.array(T)
        self.transformer = CoordinateTransformer(T)

    def process_frame(
        self, frames: Dict[str, np.ndarray], timestamp: Optional[float] = None
    ) -> Optional[BallState]:
        if timestamp is None:
            timestamp = time.time()

        t_start = time.perf_counter()

        detections_2d: Dict[str, Optional[DetectionResult]] = {}
        for cam_id, frame in frames.items():
            if cam_id in self.detectors:
                detections_2d[cam_id] = self.detectors[cam_id].detect(frame)

        tracked_2d: Dict[str, Optional[TrackPoint]] = {}
        for cam_id, det in detections_2d.items():
            if det is not None:
                tracked_2d[cam_id] = self.trackers[cam_id].update(
                    det.x, det.y, timestamp, det.confidence
                )
            else:
                tracked_2d[cam_id] = self.trackers[cam_id].update(
                    None, None, timestamp
                )

        filtered_2d: Dict[str, BallState] = {}
        for cam_id, tp in tracked_2d.items():
            if tp is not None:
                self.filter_2d[cam_id].predict()
                filtered_2d[cam_id] = self.filter_2d[cam_id].update_2d(tp.x, tp.y)
            else:
                filtered_2d[cam_id] = self.filter_2d[cam_id].predict()

        points_for_triangulation: Dict[str, Tuple[float, float]] = {}
        for cam_id, state in filtered_2d.items():
            points_for_triangulation[cam_id] = (state.x, state.y)

        point_3d = self.triangulator.triangulate(points_for_triangulation)

        if point_3d is not None:
            point_world = self.transformer.cam_to_world(point_3d)
            self.filter_3d.predict()
            state_3d = self.filter_3d.update_3d(
                point_world[0], point_world[1], point_world[2]
            )
        else:
            state_3d = self.filter_3d.predict()

        t_end = time.perf_counter()
        elapsed_ms = (t_end - t_start) * 1000.0
        self.fps_history.append(elapsed_ms)
        self.frame_count += 1

        return state_3d

    def process_video(
        self, video_path: str, camera_id: str = "cam0", display: bool = False
    ) -> List[BallState]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        states = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = self.frame_count / fps if fps > 0 else time.time()
            state = self.process_frame({camera_id: frame}, timestamp)

            if state is not None:
                states.append(state)

            if display:
                self._display_frame(frame, state)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
        return states

    def _display_frame(self, frame: np.ndarray, state: Optional[BallState]):
        if state is not None:
            text = f"3D: ({state.x:.2f}, {state.y:.2f}, {state.z:.2f}) | "
            text += f"V: ({state.vx:.2f}, {state.vy:.2f}, {state.vz:.2f})"
            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2)

        if self.fps_history:
            avg_latency = np.mean(self.fps_history[-30:])
            fps_text = f"Latency: {avg_latency:.1f}ms"
            cv2.putText(frame, fps_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 255), 2)

        cv2.imshow("Ball Perception Pipeline", frame)

    def get_stats(self) -> dict:
        if not self.fps_history:
            return {}
        arr = np.array(self.fps_history)
        return {
            "frames_processed": self.frame_count,
            "avg_latency_ms": float(np.mean(arr)),
            "std_latency_ms": float(np.std(arr)),
            "max_latency_ms": float(np.max(arr)),
            "min_latency_ms": float(np.min(arr)),
        }


def main():
    parser = argparse.ArgumentParser(description="Ball Perception Pipeline")
    parser.add_argument("--config", type=str, required=True, help="Path to config YAML")
    parser.add_argument("--video", type=str, default=None, help="Path to video file")
    parser.add_argument("--camera", type=str, default="cam0", help="Camera ID for video")
    parser.add_argument("--display", action="store_true", help="Display visualization")
    args = parser.parse_args()

    pipeline = PerceptionPipeline(args.config)

    if args.video:
        states = pipeline.process_video(args.video, args.camera, args.display)
        print(f"Processed {len(states)} frames")
        if states:
            final = states[-1]
            print(f"Final state: pos=({final.x:.3f}, {final.y:.3f}, {final.z:.3f}), "
                  f"vel=({final.vx:.3f}, {final.vy:.3f}, {final.vz:.3f})")
    else:
        print("Pipeline initialized. Use --video to process a video file.")
        print(f"Cameras: {list(pipeline.detectors.keys())}")

    stats = pipeline.get_stats()
    if stats:
        print(f"\nPipeline Stats:")
        print(f"  Frames: {stats['frames_processed']}")
        print(f"  Avg latency: {stats['avg_latency_ms']:.1f} ms")
        print(f"  Std latency: {stats['std_latency_ms']:.1f} ms")


if __name__ == "__main__":
    main()

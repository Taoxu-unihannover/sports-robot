"""
ETH Shuttle Detection — Stage 1: Auto Label Generation

Automated labeling pipeline using GMM background subtraction + YOLOv8-seg
opponent removal + temporal filtering.

Reference: "One-Shot Badminton Shuttle Detection for Mobile Robots" (2026)
Source: https://github.com/leggedrobotics/shuttle_detection

Usage:
    python autogen_labels.py --video_dir /path/to/videos --output_dir ./autogen_output
"""

import argparse
import os
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np


class AutoLabelGenerator:
    def __init__(
        self,
        bg_history: int = 500,
        bg_var_threshold: int = 16,
        min_area: int = 5,
        max_area: int = 2000,
        seg_model: str = "yolov8n-seg.pt",
        temporal_weight: float = 0.7,
        area_weight: float = 0.3,
    ):
        self.bg_history = bg_history
        self.bg_var_threshold = bg_var_threshold
        self.min_area = min_area
        self.max_area = max_area
        self.seg_model_path = seg_model
        self.temporal_weight = temporal_weight
        self.area_weight = area_weight
        self._seg_model = None

    def _get_seg_model(self):
        if self._seg_model is None:
            from ultralytics import YOLO
            self._seg_model = YOLO(self.seg_model_path)
        return self._seg_model

    def _background_subtract(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        bg_sub = cv2.createBackgroundSubtractorMOG2(
            history=self.bg_history, varThreshold=self.bg_var_threshold
        )
        masks = []
        for frame in frames:
            mask = bg_sub.apply(frame)
            _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            masks.append(mask)
        return masks

    def _remove_opponents(self, frame: np.ndarray) -> Optional[np.ndarray]:
        model = self._get_seg_model()
        results = model(frame, verbose=False, classes=0)
        if len(results) == 0 or results[0].masks is None:
            return None
        mask = results[0].masks.data.cpu().numpy()
        combined = np.zeros(frame.shape[:2], dtype=np.uint8)
        for m in mask:
            resized = cv2.resize(m, (frame.shape[1], frame.shape[0]))
            combined = cv2.bitwise_or(combined, (resized * 255).astype(np.uint8))
        return combined

    def _find_candidates(
        self, fg_mask: np.ndarray, opponent_mask: Optional[np.ndarray], h: int, w: int
    ) -> List[Tuple[float, float, float, float, float]]:
        if opponent_mask is not None:
            fg_mask = cv2.bitwise_and(fg_mask, cv2.bitwise_not(opponent_mask))

        lower_half_mask = np.zeros_like(fg_mask)
        lower_half_mask[h // 2:, :] = 255
        fg_mask = cv2.bitwise_and(fg_mask, cv2.bitwise_not(lower_half_mask))

        contours, _ = cv2.findContours(
            fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        candidates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if self.min_area <= area <= self.max_area:
                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    cx = M["m10"] / M["m00"]
                    cy = M["m01"] / M["m00"]
                    x, y, bw, bh = cv2.boundingRect(cnt)
                    candidates.append((cx, cy, float(area), float(bw), float(bh)))
        return candidates

    def _score_candidates(
        self,
        candidates: List[Tuple[float, float, float, float, float]],
        prev_center: Optional[Tuple[float, float]],
        max_area: float,
    ) -> Optional[Tuple[float, float, float, float]]:
        if not candidates:
            return None

        scored = []
        for cx, cy, area, bw, bh in candidates:
            temporal_score = 1.0
            if prev_center is not None:
                dist = np.sqrt((cx - prev_center[0]) ** 2 + (cy - prev_center[1]) ** 2)
                temporal_score = np.exp(-dist / 200.0)

            area_score = min(area / max_area, 1.0)
            total = self.temporal_weight * temporal_score + self.area_weight * area_score
            scored.append((total, cx, cy, bw, bh))

        scored.sort(key=lambda x: x[0], reverse=True)
        _, cx, cy, bw, bh = scored[0]
        return (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)

    def process_video(self, video_path: str) -> List[Optional[Tuple[float, float, float, float]]]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()

        if not frames:
            return []

        fg_masks = self._background_subtract(frames)

        labels = []
        prev_center = None
        for i, (frame, fg_mask) in enumerate(zip(frames, fg_masks)):
            h, w = frame.shape[:2]
            opponent_mask = self._remove_opponents(frame)
            candidates = self._find_candidates(fg_mask, opponent_mask, h, w)
            bbox = self._score_candidates(candidates, prev_center, self.max_area)

            if bbox is not None:
                prev_center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

            labels.append(bbox)

        return labels

    def export_cvat(self, video_path: str, labels: list, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        video_name = Path(video_path).stem

        images_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        images_xml.append('<annotations>')
        images_xml.append(f'  <version>1.1</version>')
        images_xml.append(f'  <meta><task><name>{video_name}</name></task></meta>')

        for i, bbox in enumerate(labels):
            images_xml.append(f'  <image id="{i}" name="frame_{i:06d}.png">')
            if bbox is not None:
                x1, y1, x2, y2 = bbox
                w = x2 - x1
                h = y2 - y1
                images_xml.append(
                    f'    <box label="shuttlecock" xtl="{x1:.1f}" ytl="{y1:.1f}" '
                    f'xbr="{x2:.1f}" ybr="{y2:.1f}" occluded="0"/>'
                )
            images_xml.append('  </image>')

        images_xml.append('</annotations>')

        xml_path = os.path.join(output_dir, "annotations.xml")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write("\n".join(images_xml))

        zip_path = os.path.join(output_dir, f"{video_name}_cvat.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(xml_path, "annotations.xml")
        os.remove(xml_path)

        return zip_path


def main():
    parser = argparse.ArgumentParser(description="Auto-generate shuttlecock labels")
    parser.add_argument("--video_dir", type=str, required=True, help="Directory of raw videos")
    parser.add_argument("--output_dir", type=str, default="./autogen_output", help="Output directory")
    parser.add_argument("--seg_model", type=str, default="yolov8n-seg.pt", help="Segmentation model")
    args = parser.parse_args()

    generator = AutoLabelGenerator(seg_model=args.seg_model)
    video_files = list(Path(args.video_dir).glob("*.mp4")) + list(Path(args.video_dir).glob("*.avi"))

    for vf in video_files:
        print(f"Processing {vf.name}...")
        labels = generator.process_video(str(vf))
        zip_path = generator.export_cvat(str(vf), labels, args.output_dir)
        labeled = sum(1 for l in labels if l is not None)
        print(f"  {len(labels)} frames, {labeled} labeled ({labeled/len(labels)*100:.1f}%)")
        print(f"  CVAT archive: {zip_path}")


if __name__ == "__main__":
    main()

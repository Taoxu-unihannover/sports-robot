"""
ETH Shuttle Detection — Stage 5: Inference / Prediction

Load trained model and run batch inference on images, output CSV results.

Usage:
    python predict.py --weights ./runs/shuttle_detect/weights/best.pt --source /path/to/images
"""

import argparse
import csv
import os
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np


def predict_batch(
    weights_path: str,
    source_dir: str,
    output_csv: str = "predictions.csv",
    confidence_threshold: float = 0.25,
    input_size: int = 1024,
    max_det: int = 1,
    save_visual: bool = False,
    visual_dir: str = "./visualizations",
) -> List[dict]:
    from ultralytics import YOLO

    model = YOLO(weights_path)
    source_path = Path(source_dir)
    images = sorted(source_path.glob("*.jpg")) + sorted(source_path.glob("*.png"))

    if not images:
        print(f"No images found in {source_dir}")
        return []

    if save_visual:
        os.makedirs(visual_dir, exist_ok=True)

    results_list = []

    for img_path in images:
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        results = model(
            img, imgsz=input_size, conf=confidence_threshold,
            max_det=max_det, verbose=False
        )

        row = {
            "image": img_path.name,
            "x1": "", "y1": "", "x2": "", "y2": "",
            "cx": "", "cy": "", "confidence": "",
        }

        if len(results) > 0 and results[0].boxes is not None and len(results[0].boxes) > 0:
            box = results[0].boxes[0]
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2

            row.update({
                "x1": f"{x1:.1f}", "y1": f"{y1:.1f}",
                "x2": f"{x2:.1f}", "y2": f"{y2:.1f}",
                "cx": f"{cx:.1f}", "cy": f"{cy:.1f}",
                "confidence": f"{conf:.4f}",
            })

            if save_visual:
                vis_img = img.copy()
                cv2.rectangle(vis_img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.circle(vis_img, (int(cx), int(cy)), 4, (0, 0, 255), -1)
                cv2.putText(vis_img, f"{conf:.2f}", (int(x1), int(y1) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.imwrite(str(Path(visual_dir) / img_path.name), vis_img)

        results_list.append(row)

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writeheader()
        writer.writerows(results_list)

    detected = sum(1 for r in results_list if r["confidence"])
    print(f"Processed {len(results_list)} images, {detected} detections")
    print(f"Results saved to {output_csv}")

    return results_list


def main():
    parser = argparse.ArgumentParser(description="Run shuttlecock detection inference")
    parser.add_argument("--weights", type=str, required=True, help="Model weights path")
    parser.add_argument("--source", type=str, required=True, help="Image directory")
    parser.add_argument("--output", type=str, default="predictions.csv", help="Output CSV path")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--imgsz", type=int, default=1024, help="Input image size")
    parser.add_argument("--max_det", type=int, default=1, help="Max detections per frame")
    parser.add_argument("--save_visual", action="store_true", help="Save visualization images")
    parser.add_argument("--visual_dir", type=str, default="./visualizations")
    args = parser.parse_args()

    predict_batch(
        args.weights, args.source, args.output,
        args.conf, args.imgsz, args.max_det,
        args.save_visual, args.visual_dir,
    )


if __name__ == "__main__":
    main()

"""
ETH Shuttle Detection — Stage 4: Evaluation

Cross-validation evaluation with background-based and location-based splits.
Uses Distance Precision Rate (DPR) metric: prediction center within 25px of GT center.

Usage:
    python eval.py --weights ./runs/shuttle_detect/weights/best.pt --dataset ./dataset
"""

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np


DISTANCE_THRESHOLD = 25.0


def distance_precision_rate(
    predictions: List[Tuple[float, float]],
    ground_truths: List[Tuple[float, float]],
    threshold: float = DISTANCE_THRESHOLD,
) -> Dict[str, float]:
    tp = 0
    fp = 0
    fn = 0

    for pred, gt in zip(predictions, ground_truths):
        dist = np.sqrt((pred[0] - gt[0]) ** 2 + (pred[1] - gt[1]) ** 2)
        if dist <= threshold:
            tp += 1
        else:
            fp += 1

    fn = sum(1 for gt in ground_truths if gt is not None) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def background_cross_validation(
    weights_path: str, dataset_dir: str, n_folds: int = 11
) -> List[Dict[str, float]]:
    from ultralytics import YOLO

    model = YOLO(weights_path)
    dataset_path = Path(dataset_dir)
    test_img_dir = dataset_path / "images" / "test"

    if not test_img_dir.exists():
        print(f"Test directory not found: {test_img_dir}")
        return []

    images = sorted(test_img_dir.glob("*.jpg")) + sorted(test_img_dir.glob("*.png"))
    if not images:
        print("No test images found")
        return []

    fold_size = max(1, len(images) // n_folds)
    fold_results = []

    for fold in range(n_folds):
        start = fold * fold_size
        end = min(start + fold_size, len(images))
        fold_images = images[start:end]

        predictions = []
        ground_truths = []

        for img_path in fold_images:
            lbl_path = dataset_path / "labels" / "test" / (img_path.stem + ".txt")
            img = cv2.imread(str(img_path))
            if img is None:
                continue

            results = model(img, verbose=False, max_det=1)
            if len(results) > 0 and results[0].boxes is not None and len(results[0].boxes) > 0:
                box = results[0].boxes[0]
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                predictions.append(((x1 + x2) / 2, (y1 + y2) / 2))
            else:
                predictions.append((0.0, 0.0))

            if lbl_path.exists():
                with open(lbl_path, "r") as f:
                    line = f.readline().strip()
                    if line:
                        parts = line.split()
                        cx, cy, w, h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                        ih, iw = img.shape[:2]
                        gt_cx = cx * iw
                        gt_cy = cy * ih
                        ground_truths.append((gt_cx, gt_cy))
                    else:
                        ground_truths.append((0.0, 0.0))
            else:
                ground_truths.append((0.0, 0.0))

        if predictions and ground_truths:
            result = distance_precision_rate(predictions, ground_truths)
            fold_results.append(result)
            print(f"  Fold {fold + 1}/{n_folds}: P={result['precision']:.3f} R={result['recall']:.3f} F1={result['f1']:.3f}")

    if fold_results:
        avg = {
            "precision": np.mean([r["precision"] for r in fold_results]),
            "recall": np.mean([r["recall"] for r in fold_results]),
            "f1": np.mean([r["f1"] for r in fold_results]),
        }
        print(f"\nBackground CV Average: P={avg['precision']:.3f} R={avg['recall']:.3f} F1={avg['f1']:.3f}")

    return fold_results


def evaluate(args):
    print(f"Model: {args.weights}")
    print(f"Dataset: {args.dataset}")
    print(f"Distance threshold: {args.threshold}px")
    print(f"CV strategy: {args.cv_strategy}")
    print()

    if args.cv_strategy == "background":
        background_cross_validation(args.weights, args.dataset, args.n_folds)
    elif args.cv_strategy == "location":
        print("Location-based CV requires location metadata in dataset.")
        print("Falling back to background-based CV.")
        background_cross_validation(args.weights, args.dataset, args.n_folds)
    else:
        background_cross_validation(args.weights, args.dataset, args.n_folds)


def main():
    parser = argparse.ArgumentParser(description="Evaluate shuttlecock detector")
    parser.add_argument("--weights", type=str, required=True, help="Model weights path")
    parser.add_argument("--dataset", type=str, default="./dataset", help="Dataset directory")
    parser.add_argument("--threshold", type=float, default=25.0, help="Distance precision threshold (px)")
    parser.add_argument("--cv_strategy", type=str, default="background", choices=["background", "location"])
    parser.add_argument("--n_folds", type=int, default=11, help="Number of CV folds")
    args = parser.parse_args()

    evaluate(args)


if __name__ == "__main__":
    main()

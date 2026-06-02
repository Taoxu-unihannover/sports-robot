"""
ETH Shuttle Detection — Stage 2: Label Conversion

Convert CVAT-exported YOLO annotations to Ultralytics dataset structure
with difficulty-based splitting (easy/medium/hard).

Usage:
    python convert_labels.py --input /path/to/cvat/export --output ./dataset
"""

import argparse
import os
import shutil
from pathlib import Path


DIFFICULTY_THRESHOLDS = {
    "easy": {"min_area": 100, "max_blur": 5},
    "medium": {"min_area": 30, "max_blur": 15},
    "hard": {"min_area": 0, "max_blur": 999},
}

TRAIN_SPLIT = 0.8
VAL_SPLIT = 0.1
TEST_SPLIT = 0.1


def classify_difficulty(label_line: str, img_w: int, img_h: int) -> str:
    parts = label_line.strip().split()
    if len(parts) < 5:
        return "hard"
    _, cx, cy, w, h = parts
    cx, cy, w, h = float(cx), float(cy), float(w), float(h)
    area_px = w * img_w * h * img_h

    if area_px >= DIFFICULTY_THRESHOLDS["easy"]["min_area"]:
        return "easy"
    elif area_px >= DIFFICULTY_THRESHOLDS["medium"]["min_area"]:
        return "medium"
    else:
        return "hard"


def convert_dataset(input_dir: str, output_dir: str, include_hard: bool = False):
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    for split in ["train", "val", "test"]:
        (output_path / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_path / "labels" / split).mkdir(parents=True, exist_ok=True)

    label_files = sorted(input_path.glob("*.txt"))
    difficulties = {"easy": [], "medium": [], "hard": []}

    for lf in label_files:
        img_candidates = [
            lf.with_suffix(".jpg"),
            lf.with_suffix(".png"),
        ]
        img_file = next((c for c in img_candidates if c.exists()), None)
        if img_file is None:
            continue

        with open(lf, "r") as f:
            lines = f.readlines()

        if not lines:
            continue

        diff = classify_difficulty(lines[0], 1, 1)
        difficulties[diff].append((img_file, lf))

    included = difficulties["easy"] + difficulties["medium"]
    if include_hard:
        included += difficulties["hard"]

    n = len(included)
    n_train = int(n * TRAIN_SPLIT)
    n_val = int(n * VAL_SPLIT)

    import random
    random.seed(42)
    random.shuffle(included)

    splits = {
        "train": included[:n_train],
        "val": included[n_train:n_train + n_val],
        "test": included[n_train + n_val:],
    }

    data_yaml_lines = [
        f"path: {output_path.resolve()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "nc: 1",
        "names: ['shuttlecock']",
    ]

    for split_name, items in splits.items():
        for img_file, lbl_file in items:
            shutil.copy2(img_file, output_path / "images" / split_name / img_file.name)
            shutil.copy2(lbl_file, output_path / "labels" / split_name / lbl_file.name)

    with open(output_path / "data.yaml", "w") as f:
        f.write("\n".join(data_yaml_lines))

    print(f"Dataset created at {output_path}")
    print(f"  easy: {len(difficulties['easy'])}, medium: {len(difficulties['medium'])}, hard: {len(difficulties['hard'])}")
    print(f"  train: {len(splits['train'])}, val: {len(splits['val'])}, test: {len(splits['test'])}")
    print(f"  Included hard samples: {include_hard}")


def main():
    parser = argparse.ArgumentParser(description="Convert CVAT labels to YOLO dataset")
    parser.add_argument("--input", type=str, required=True, help="CVAT export directory")
    parser.add_argument("--output", type=str, default="./dataset", help="Output dataset directory")
    parser.add_argument("--include_hard", action="store_true", help="Include hard difficulty samples")
    args = parser.parse_args()

    convert_dataset(args.input, args.output, args.include_hard)


if __name__ == "__main__":
    main()

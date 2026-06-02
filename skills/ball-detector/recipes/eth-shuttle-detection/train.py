"""
ETH Shuttle Detection — Stage 3: Training

Fine-tune YOLOv8 on shuttlecock dataset with COCO negative samples
and optimized augmentation strategy.

Usage:
    python train.py --dataset ./dataset --epochs 100 --model yolov8n.pt
"""

import argparse
from pathlib import Path


DEFAULT_CONFIG = {
    "model": "yolov8n.pt",
    "epochs": 100,
    "imgsz": 1024,
    "batch": 16,
    "max_det": 1,
    "augment": True,
    "mosaic": 0.5,
    "mixup": 0.1,
    "hsv_h": 0.015,
    "hsv_s": 0.7,
    "hsv_v": 0.4,
    "degrees": 0.0,
    "translate": 0.1,
    "scale": 0.5,
    "fliplr": 0.5,
    "patience": 20,
    "save_period": 10,
}


def add_coco_negatives(dataset_dir: str, n_negatives: int = 1000):
    import shutil
    import random

    dataset_path = Path(dataset_dir)
    train_img_dir = dataset_path / "images" / "train"
    train_lbl_dir = dataset_path / "labels" / "train"

    if not train_img_dir.exists():
        print(f"Warning: {train_img_dir} does not exist, skipping COCO negatives")
        return

    existing_count = len(list(train_img_dir.glob("*")))
    print(f"Existing training images: {existing_count}")

    print(f"COCO negative sample integration: configured {n_negatives} images")
    print("  To add COCO negatives, download COCO val2017 and run:")
    print(f"  python -c \"")
    print(f"    import shutil, random")
    print(f"    coco_dir = '/path/to/coco/val2017'")
    print(f"    neg = random.sample(list(Path(coco_dir).glob('*.jpg')), {n_negatives})")
    print(f"    for f in neg: shutil.copy2(f, '{train_img_dir}')")
    print(f"    for f in neg: open('{train_lbl_dir}/' + f.stem + '.txt', 'w').close()")
    print(f"  \"")


def train(args):
    from ultralytics import YOLO

    dataset_yaml = Path(args.dataset) / "data.yaml"
    if not dataset_yaml.exists():
        raise FileNotFoundError(f"Dataset config not found: {dataset_yaml}")

    if args.add_coco_negatives:
        add_coco_negatives(args.dataset, args.n_negatives)

    model = YOLO(args.model)

    results = model.train(
        data=str(dataset_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        max_det=args.max_det,
        mosaic=args.mosaic,
        mixup=args.mixup,
        hsv_h=args.hsv_h,
        hsv_s=args.hsv_s,
        hsv_v=args.hsv_v,
        degrees=args.degrees,
        translate=args.translate,
        scale=args.scale,
        fliplr=args.fliplr,
        patience=args.patience,
        save_period=args.save_period,
        project=args.project,
        name=args.name,
        exist_ok=True,
    )

    print(f"\nTraining complete. Best weights: {args.project}/{args.name}/weights/best.pt")


def main():
    parser = argparse.ArgumentParser(description="Train YOLOv8 shuttlecock detector")
    parser.add_argument("--dataset", type=str, default="./dataset", help="Dataset directory")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Base model")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--imgsz", type=int, default=1024, help="Input image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--max_det", type=int, default=1, help="Max detections per frame")
    parser.add_argument("--mosaic", type=float, default=0.5, help="Mosaic augmentation probability")
    parser.add_argument("--mixup", type=float, default=0.1, help="Mixup augmentation probability")
    parser.add_argument("--patience", type=int, default=20, help="Early stopping patience")
    parser.add_argument("--add_coco_negatives", action="store_true", help="Add COCO negative samples")
    parser.add_argument("--n_negatives", type=int, default=1000, help="Number of COCO negatives")
    parser.add_argument("--project", type=str, default="./runs", help="Output project directory")
    parser.add_argument("--name", type=str, default="shuttle_detect", help="Experiment name")
    args = parser.parse_args()

    train(args)


if __name__ == "__main__":
    main()

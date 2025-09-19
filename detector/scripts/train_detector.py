"""Train a YOLOv8-based lesion detector/segmenter for SkinPro."""
from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train lesion detector")
    parser.add_argument(
        "--data",
        default="detector/data/roboflow_skin.yaml",
        help="Path to YOLO data.yaml",
    )
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="Model checkpoint or config (e.g. yolov8n.pt, yolov8s.yaml).",
    )
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--img-size", type=int, default=1024)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--project", default="runs/lesion", help="Training output dir")
    parser.add_argument("--name", default="exp", help="Run name")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--device", default="cpu", help="CUDA device string or 'cpu'")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "ultralytics package not found. Install with `pip install ultralytics` before training."
        ) from exc

    model_arg = args.model
    config_path = Path(model_arg)
    if config_path.exists():
        model = YOLO(str(config_path))
    else:
        model = YOLO(model_arg)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.img_size,
        batch=args.batch,
        project=args.project,
        name=args.name,
        resume=args.resume,
        device=args.device,
        pretrained=True,
    )


if __name__ == "__main__":
    main()

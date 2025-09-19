"""Evaluate a trained lesion detector on a dataset split."""
from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate lesion detector")
    parser.add_argument("--weights", required=True, help="Path to model weights (e.g. best.pt)")
    parser.add_argument(
        "--data",
        default="detector/data/roboflow_skin.yaml",
        help="Path to YOLO data.yaml",
    )
    parser.add_argument("--split", default="val", help="Dataset split to evaluate")
    parser.add_argument("--img-size", type=int, default=1024)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="0", help="CUDA device or cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("ultralytics package not found. Install with `pip install ultralytics`.") from exc

    weights_path = Path(args.weights)
    if not weights_path.exists():
        raise SystemExit(f"Weights file not found: {weights_path}")

    model = YOLO(str(weights_path))
    results = model.val(
        data=args.data,
        split=args.split,
        imgsz=args.img_size,
        batch=args.batch,
        device=args.device,
    )
    print(results)


if __name__ == "__main__":
    main()

"""Download the Roboflow skin-problem dataset in YOLOv8 format."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Roboflow dataset")
    parser.add_argument("--api-key", default=os.environ.get("ROBOFLOW_API_KEY"), help="Roboflow API key")
    parser.add_argument("--workspace", default="parin-kittipongdaja-vwmn3", help="Roboflow workspace slug")
    parser.add_argument("--project", default="skin-problem-detection-relabel", help="Roboflow project slug")
    parser.add_argument("--version", type=int, default=1, help="Dataset version to download")
    parser.add_argument("--format", default="yolov8", choices=["yolov8"], help="Export format")
    parser.add_argument(
        "--output",
        default="detector/datasets/skin_problems",
        help="Directory to write the dataset into",
    )
    parser.add_argument(
        "--data-config",
        default="detector/data/roboflow_skin.yaml",
        help="Destination path for copied data.yaml",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing dataset directory")
    return parser.parse_args()


def ensure_api_key(key: str | None) -> str:
    if not key:
        raise SystemExit(
            "Roboflow API key missing. Set ROBOFLOW_API_KEY env var or pass --api-key <key>."
        )
    return key


def copy_data_yaml(dataset_dir: Path, destination: Path) -> None:
    src_yaml = dataset_dir / "data.yaml"
    if not src_yaml.exists():
        print(f"Warning: {src_yaml} not found. Skipping config copy.")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_yaml, destination)
    print(f"Copied {src_yaml} -> {destination}")


def main() -> None:
    args = parse_args()
    api_key = ensure_api_key(args.api_key)

    try:
        from roboflow import Roboflow
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("roboflow package not installed. Run `pip install roboflow`."
                        ) from exc

    output_dir = Path(args.output)
    if output_dir.exists():
        if args.overwrite:
            shutil.rmtree(output_dir)
        else:
            raise SystemExit(
                f"Output directory {output_dir} already exists. Pass --overwrite to replace it."
            )

    rf = Roboflow(api_key=api_key)
    project = rf.workspace(args.workspace).project(args.project)
    dataset = project.version(args.version)
    print(
        f"Downloading workspace={args.workspace} project={args.project} version={args.version} format={args.format}"
    )
    dataset.download(args.format, location=str(output_dir))

    copy_data_yaml(output_dir, Path(args.data_config))

    print("Download complete. Dataset stored in", output_dir)


if __name__ == "__main__":
    main()

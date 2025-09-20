"""Quick CLI client to test the SkinPro API locally."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests


def analyze(base_url: str, image_path: Path) -> dict:
    files = {"file": (image_path.name, image_path.open("rb"), "image/jpeg")}
    resp = requests.post(f"{base_url}/analyze", files=files, timeout=120)
    resp.raise_for_status()
    return resp.json()


def coach(base_url: str, analysis: dict) -> dict:
    payload = {
        "profile": {
            "diet": "Dengeli",
            "stress": "Orta",
            "sleep_hours": 7,
            "hydration": "Yeterli",
            "hormonal": "Stabil",
            "skincare": ["Nazik temizleyici", "SPF"],
        },
        "analysis": {
            "final_grade": analysis.get("final_grade", "Mild"),
            "inflamed_area_pct": analysis.get("inflamed_area_pct", 0.0),
            "lesions": analysis.get("lesions", {}),
        },
    }
    resp = requests.post(f"{base_url}/coach", json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Test SkinPro API")
    parser.add_argument("image", type=Path, help="Path to face photo")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()

    analysis = analyze(args.base_url, args.image)
    print("Analysis result:\n", json.dumps({k: analysis.get(k) for k in ("final_grade", "confidence", "inflamed_area_pct")}, indent=2))

    if analysis.get("lesions", {}).get("detector_overlay"):
        print("Overlay (base64) size:", len(analysis["lesions"]["detector_overlay"]))

    coach_resp = coach(args.base_url, analysis)
    print("Coach response keys:", coach_resp.keys())


if __name__ == "__main__":
    main()

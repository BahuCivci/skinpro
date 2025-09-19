"""Auxiliary computer-vision utilities for SkinPro."""
from __future__ import annotations
from typing import List, Dict

import numpy as np

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    cv2 = None

from PIL import Image


def _ensure_cv() -> bool:
    return cv2 is not None


def detect_inflammation_regions(img: Image.Image, max_regions: int = 5) -> List[Dict[str, float]]:
    """Detect red/inflamed areas using HSV thresholding and contour analysis."""
    if not _ensure_cv():
        return []
    rgb = np.array(img.convert("RGB"))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    # red hue appears near 0 and near 180; cover both bands
    lower1 = np.array([0, 80, 80], dtype=np.uint8)
    upper1 = np.array([12, 255, 255], dtype=np.uint8)
    lower2 = np.array([170, 80, 80], dtype=np.uint8)
    upper2 = np.array([179, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)
    mask = cv2.GaussianBlur(mask, (5, 5), 0)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = mask.shape
    total_area = h * w

    regions: List[Dict[str, float]] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area / total_area < 0.001:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        regions.append(
            {
                "x": float(x / w),
                "y": float(y / h),
                "width": float(bw / w),
                "height": float(bh / h),
                "area_pct": float(area / total_area * 100.0),
            }
        )

    regions.sort(key=lambda r: r["area_pct"], reverse=True)
    return regions[:max_regions]


def compute_redness_heatmap(img: Image.Image) -> float:
    """Re-usable redness ratio in percentage."""
    rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mask = r > (g + b) / 2 + 15
    return float(mask.mean()) * 100.0


def compute_texture_score(img: Image.Image) -> float:
    if not _ensure_cv():
        return 0.0
    gray = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    return float(lap.var())


def compute_pore_proxy(img: Image.Image) -> float:
    if not _ensure_cv():
        return 0.0
    gray = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    diff = cv2.absdiff(gray, blur)
    return float(diff.mean())

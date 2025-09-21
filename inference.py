"""Inference utilities powering SkinPro's AI backend."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import os

import numpy as np
from PIL import Image

from analysis_utils import (
    compute_pore_proxy,
    compute_redness_heatmap,
    compute_texture_score,
    detect_inflammation_regions,
    draw_detector_overlay,
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
_LESION_MODEL_PATH = os.path.join(MODELS_DIR, "skin_lesion.onnx")
_LESION_MODEL_PATH_PT = os.path.join(MODELS_DIR, "skin_lesion.pt")

try:  # pragma: no cover
    from ultralytics import YOLO
except Exception:
    YOLO = None

# --- Optional ONNX backend ---------------------------------------------------
try:
    import onnxruntime as ort
except Exception:  # pragma: no cover - runtime dependency check
    ort = None

# --- Hugging Face pipelines --------------------------------------------------
from transformers import pipeline as hf_pipeline  # type: ignore

_HF_PIPELINES: Dict[str, Any] = {}
_HF_ERRORS: Dict[str, str] = {}
_HF_CANDIDATES = [mid for mid in [
    os.environ.get("SKINPRO_HF_MODEL"),
    "imfarzanansari/skintelligent-acne",
    "afscomercial/dermatologic",
] if mid]

_DETECTOR_SESSION: Optional[Any] = None
_DETECTOR_ERROR: Optional[str] = None
_DETECTOR_MODEL: Optional[Any] = None
_DETECTOR_MODEL_SOURCE: Optional[str] = None
_DETECTOR_CLASS_NAMES: Optional[List[str]] = None
_DETECTOR_CONF_THRES = float(os.environ.get("SKINPRO_DETECTOR_CONF", "0.45"))
_DETECTOR_INPUT_SIZE = int(os.environ.get("SKINPRO_DETECTOR_SIZE", "1024"))

SEVERITY_SCALE = ["Clear", "Mild", "Moderate", "Severe", "Very Severe"]
_HF_LABEL_MAP = {
    "level -1": "Clear",
    "level0": "Clear",
    "level 0": "Mild",
    "level0_mild": "Mild",
    "level 1": "Moderate",
    "level1": "Moderate",
    "level 2": "Severe",
    "level2": "Severe",
    "level 3": "Very Severe",
    "level3": "Very Severe",
}


@dataclass
class SeverityPrediction:
    label: str
    confidence: float
    source: str
    raw_label: str


def _to_rgb(img: Image.Image) -> Image.Image:
    return img.convert("RGB") if img.mode != "RGB" else img


def _normalize_224(pil: Image.Image) -> np.ndarray:
    im = pil.resize((224, 224)).convert("RGB")
    arr = (np.asarray(im).astype("float32") / 255.0).transpose(2, 0, 1)[None, ...]
    return arr


def _severity_index(label: str) -> int:
    try:
        return SEVERITY_SCALE.index(label)
    except ValueError:
        return max(0, min(4, int(label) if label.isdigit() else 2))


def _map_label(raw: str) -> str:
    key = raw.strip().lower()
    mapped = _HF_LABEL_MAP.get(key)
    if mapped:
        return mapped
    lowered = raw.lower()
    for sev in SEVERITY_SCALE:
        if sev.lower() in lowered:
            return sev
    return "Moderate"


def _load_hf_model(model_id: str):
    if model_id in _HF_PIPELINES:
        return _HF_PIPELINES[model_id]
    try:
        pipe = hf_pipeline("image-classification", model=model_id)
        _HF_PIPELINES[model_id] = pipe
        return pipe
    except Exception as exc:  # pragma: no cover - logging path
        _HF_ERRORS[model_id] = str(exc)
        return None


def _run_hf_models(img: Image.Image) -> List[SeverityPrediction]:
    preds: List[SeverityPrediction] = []
    for model_id in _HF_CANDIDATES:
        pipe = _load_hf_model(model_id)
        if pipe is None:
            continue
        try:
            res = pipe(img)
        except Exception as exc:  # pragma: no cover
            _HF_ERRORS[model_id] = str(exc)
            continue
        if not res:
            continue
        best = max(res, key=lambda x: x.get("score", 0.0))
        raw_label = str(best.get("label", ""))
        preds.append(
            SeverityPrediction(
                label=_map_label(raw_label),
                confidence=float(best.get("score", 0.0)),
                source=f"hf::{model_id}",
                raw_label=raw_label,
            )
        )
    return preds


def _run_onnx_model(img: Image.Image) -> Optional[SeverityPrediction]:
    if ort is None:
        return None
    path = os.path.join(MODELS_DIR, "severity_cls.onnx")
    if not os.path.isfile(path):
        return None
    session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
    arr = _normalize_224(img)
    out = session.run(None, {session.get_inputs()[0].name: arr})[0].squeeze()
    out = out - out.max()
    probs = np.exp(out)
    probs /= probs.sum()
    idx = int(np.argmax(probs))
    names = SEVERITY_SCALE
    label = names[idx] if idx < len(names) else f"class_{idx}"
    return SeverityPrediction(
        label=label,
        confidence=float(probs[idx]),
        source="onnx::severity_cls",
        raw_label=label,
    )


def _load_detector_session():
    global _DETECTOR_SESSION, _DETECTOR_ERROR
    if ort is None:
        _DETECTOR_ERROR = "onnxruntime not available"
        return None
    if _DETECTOR_SESSION is not None:
        return _DETECTOR_SESSION
    if not os.path.isfile(_LESION_MODEL_PATH):
        _DETECTOR_ERROR = "skin_lesion.onnx not found"
        return None
    try:
        _DETECTOR_SESSION = ort.InferenceSession(_LESION_MODEL_PATH, providers=["CPUExecutionProvider"])
        _DETECTOR_ERROR = None
        return _DETECTOR_SESSION
    except Exception as exc:  # pragma: no cover
        _DETECTOR_ERROR = str(exc)
        _DETECTOR_SESSION = None
        return None


def _load_detector_model():
    global _DETECTOR_MODEL, _DETECTOR_ERROR, _DETECTOR_CLASS_NAMES, _DETECTOR_MODEL_SOURCE
    if _DETECTOR_MODEL is not None:
        return _DETECTOR_MODEL
    if YOLO is None:
        _DETECTOR_ERROR = "ultralytics not installed"
        return None

    for path in (_LESION_MODEL_PATH, _LESION_MODEL_PATH_PT):
        if not os.path.isfile(path):
            continue
        try:
            model = YOLO(path)
            _DETECTOR_MODEL = model
            _DETECTOR_MODEL_SOURCE = path
            names = model.names
            if isinstance(names, dict):
                _DETECTOR_CLASS_NAMES = [names[k] for k in sorted(names.keys())]
            elif isinstance(names, (list, tuple)):
                _DETECTOR_CLASS_NAMES = list(names)
            else:
                _DETECTOR_CLASS_NAMES = None
            _DETECTOR_ERROR = None
            return _DETECTOR_MODEL
        except Exception as exc:  # pragma: no cover
            _DETECTOR_ERROR = str(exc)
            _DETECTOR_MODEL = None
    _DETECTOR_ERROR = "detector weights not found"
    return None


def _run_lesion_detector(img: Image.Image) -> List[Dict[str, Any]]:
    model = _load_detector_model()
    if model is None:
        return []
    try:
        results = model.predict(img, imgsz=_DETECTOR_INPUT_SIZE, conf=_DETECTOR_CONF_THRES, max_det=150, verbose=False)
    except Exception as exc:  # pragma: no cover
        _DETECTOR_ERROR = str(exc)
        return []

    if not results:
        return []

    res = results[0]
    boxes = getattr(res, "boxes", None)
    if boxes is None or not len(boxes):
        return []

    width, height = img.size
    cls_names = _DETECTOR_CLASS_NAMES or ["Acne", "Blackheads", "Dark-Spots", "Dry-Skin", "Englarged-Pores",
                                         "Eyebags", "Nodules", "Normal-Skin", "Oily-Skin", "Papules",
                                         "Skin-Redness", "Whiteheads", "Wrinkles", "acne marks",
                                         "acne scar", "burned-skin", "pustules"]

    dets: List[Dict[str, Any]] = []
    xyxy = boxes.xyxy.cpu().numpy()
    confs = boxes.conf.cpu().numpy()
    classes = boxes.cls.cpu().numpy().astype(int)
    for (x1, y1, x2, y2), conf, cls in zip(xyxy, confs, classes):
        label = cls_names[cls] if cls < len(cls_names) else f"cls_{cls}"
        x1, y1, x2, y2 = map(float, (x1, y1, x2, y2))
        area = max(0.0, (x2 - x1) * (y2 - y1))
        area_pct = area / (width * height) * 100.0
        dets.append(
            {
                "label": label,
                "confidence": float(conf),
                "bbox": [x1 / width, y1 / height, x2 / width, y2 / height],
                "bbox_abs": [x1, y1, x2, y2],
                "area_pct": float(area_pct),
                "class_id": int(cls),
            }
        )

    dets.sort(key=lambda d: d["confidence"], reverse=True)
    return dets[:10]


def _ensemble_predictions(preds: List[SeverityPrediction]) -> Tuple[str, float]:
    if not preds:
        return "Moderate", 0.5
    scores = []
    weights = []
    for p in preds:
        idx = _severity_index(p.label)
        weight = max(1e-3, p.confidence)
        scores.append(idx * weight)
        weights.append(weight)
    agg = sum(scores) / sum(weights)
    final_idx = int(round(agg))
    final_idx = max(0, min(final_idx, len(SEVERITY_SCALE) - 1))
    confidence = min(0.99, float(sum(weights) / len(preds)))
    return SEVERITY_SCALE[final_idx], confidence


def analyze_image(pil_img: Image.Image) -> Dict[str, Any]:
    img = _to_rgb(pil_img)

    preds: List[SeverityPrediction] = []

    onnx_pred = _run_onnx_model(img)
    if onnx_pred is not None:
        preds.append(onnx_pred)

    preds.extend(_run_hf_models(img))

    inflamed_pct = compute_redness_heatmap(img)
    detector_regions = _run_lesion_detector(img)

    if not preds:
        # fallback heuristics
        if inflamed_pct < 3:
            label = "Clear"
        elif inflamed_pct < 10:
            label = "Mild"
        elif inflamed_pct < 20:
            label = "Moderate"
        else:
            label = "Severe"
        return {
            "final_grade": label,
            "confidence": min(0.95, 0.5 + inflamed_pct / 100),
            "inflamed_area_pct": inflamed_pct,
            "used": {
                "classifier_onnx": False,
                "classifier_hf": False,
                "heuristic": True,
            },
            "meta": {
                "hf_errors": _HF_ERRORS,
                "hf_models": [],
                "ensemble": [],
                "detector": {"error": _DETECTOR_ERROR, "model": _DETECTOR_MODEL_SOURCE},
            },
            "lesions": {
                "regions": detect_inflammation_regions(img),
                "texture_score": compute_texture_score(img),
                "pore_proxy": compute_pore_proxy(img),
                "detector_regions": detector_regions,
            },
        }

    final_label, agg_conf = _ensemble_predictions(preds)

    hf_models = [p.source for p in preds if p.source.startswith("hf::")]

    return {
        "final_grade": final_label,
        "confidence": agg_conf,
        "inflamed_area_pct": inflamed_pct,
        "used": {
            "classifier_onnx": any(p.source.startswith("onnx::") for p in preds),
            "classifier_hf": bool(hf_models),
            "heuristic": False,
        },
        "meta": {
            "hf_errors": _HF_ERRORS,
            "hf_models": hf_models,
            "ensemble": [p.__dict__ for p in preds],
            "detector": {"error": _DETECTOR_ERROR, "model": _DETECTOR_MODEL_SOURCE, "count": len(detector_regions)},
        },
        "lesions": {
            "regions": detect_inflammation_regions(img),
            "texture_score": compute_texture_score(img),
            "pore_proxy": compute_pore_proxy(img),
            "detector_regions": detector_regions,
            "detector_overlay": draw_detector_overlay(img, detector_regions) if detector_regions else None,
        },
    }

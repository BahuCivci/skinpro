"""FastAPI backend for SkinPro analysis and coaching."""
from __future__ import annotations

import base64
import io
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image

from inference import analyze_image
from advisor import build_plan
from knowledge import recommend_remedies, build_safety_alerts, community_highlights

app = FastAPI(title="SkinPro API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _image_to_base64(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _sanitize_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(payload)
    lesions = result.get("lesions")
    if isinstance(lesions, dict):
        overlay = lesions.get("detector_overlay")
        if isinstance(overlay, Image.Image):
            lesions["detector_overlay"] = _image_to_base64(overlay)
    return result


class Profile(BaseModel):
    diet: str = Field(..., description="Beslenme alışkanlığı")
    stress: str = Field(..., description="Stres seviyesi")
    sleep_hours: int = Field(..., ge=0, le=24)
    hydration: str
    hormonal: str
    skincare: List[str] = Field(default_factory=list)


class AnalysisSummary(BaseModel):
    final_grade: str
    inflamed_area_pct: float
    lesions: Optional[Dict[str, Any]] = None


class CoachRequest(BaseModel):
    profile: Profile
    analysis: AnalysisSummary


@app.get("/health", summary="Health check")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/", summary="Service info")
def root() -> Dict[str, Any]:
    return {
        "service": "SkinPro API",
        "version": "0.1.0",
        "endpoints": ["GET /health", "POST /analyze", "POST /coach"],
    }


@app.post("/analyze", summary="Analyze skin photo")
async def analyze(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Yalnızca görüntü dosyaları kabul edilir.")
    data = await file.read()
    try:
        pil_img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail="Görüntü okunamadı.") from exc

    analysis = analyze_image(pil_img)
    return _sanitize_analysis(analysis)


@app.post("/coach", summary="Generate routine recommendations")
def coach(req: CoachRequest) -> Dict[str, Any]:
    analysis = req.analysis
    profile = req.profile.dict()

    plan = build_plan(profile, analysis.final_grade, analysis.inflamed_area_pct)

    concerns: List[str] = []
    if analysis.inflamed_area_pct > 12:
        concerns.append("redness")
    if analysis.inflamed_area_pct > 20:
        concerns.append("inflammation")
    lesions = analysis.lesions or {}
    if float(lesions.get("texture_score", 0)) > 120.0:
        concerns.append("texture")
    if float(lesions.get("pore_proxy", 0)) > 18.0:
        concerns.append("blackheads")

    remedies = recommend_remedies(analysis.final_grade, profile, concerns)
    alerts = build_safety_alerts(analysis.final_grade, analysis.inflamed_area_pct, len(lesions.get("detector_regions", []) if isinstance(lesions, dict) else []))
    community = community_highlights(remedies)

    return {
        "plan": plan,
        "remedies": remedies,
        "alerts": alerts,
        "community": community,
    }


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)

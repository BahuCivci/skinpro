"""Knowledge base and retrieval logic for SkinPro natural solutions."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Any, Tuple
import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CONTENT_PATH = os.path.join(os.path.dirname(__file__), "content", "natural_remedies.json")


@dataclass
class Remedy:
    id: str
    title: str
    summary: str
    evidence: str
    severity: List[str]
    concerns: List[str]
    triggers: List[str]
    instructions: str
    warnings: List[str]
    sources: List[Dict[str, str]]
    community: List[str]


@lru_cache(maxsize=1)
def _load_remedies() -> List[Remedy]:
    with open(CONTENT_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    remedies = [Remedy(**item) for item in data]
    return remedies


def _build_vectorizer(remedies: List[Remedy]):
    corpus = [f"{r.summary} {' '.join(r.concerns)} {' '.join(r.triggers)}" for r in remedies]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus)
    return vectorizer, matrix


@lru_cache(maxsize=1)
def _vectorizer_bundle():
    remedies = _load_remedies()
    return _build_vectorizer(remedies)


def _query_embedding(text: str):
    remedies = _load_remedies()
    vectorizer, matrix = _vectorizer_bundle()
    q_vec = vectorizer.transform([text])
    sims = cosine_similarity(q_vec, matrix)[0]
    return list(zip(remedies, sims))


def _base_score(remedy: Remedy, severity: str, profile: Dict[str, Any], concerns: List[str]) -> float:
    score = 0.0
    if severity in remedy.severity:
        score += 2.0
    # severity neighbors
    severity_order = ["Clear", "Mild", "Moderate", "Severe", "Very Severe"]
    if severity not in remedy.severity:
        try:
            diff = abs(severity_order.index(severity) - min(severity_order.index(s) for s in remedy.severity))
            score += max(0.5, 1.5 - 0.3 * diff)
        except Exception:
            pass
    triggers = profile.get("triggers", [])
    for trig in triggers:
        if trig in remedy.triggers:
            score += 0.75
    for issue in concerns:
        if issue in remedy.concerns:
            score += 0.8
    return score


def recommend_remedies(severity: str, profile: Dict[str, Any], concerns: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
    remedies = _load_remedies()

    triggers = []
    if diet := profile.get("diet"):
        if diet == "Yüksek Şeker":
            triggers.append("high_glycemic")
        if diet == "Süt Ağırlıklı":
            triggers.append("dairy")
    if profile.get("stress") in ("Yüksek", "Çok Yüksek"):
        triggers.append("stress")
    if profile.get("hydration") == "Düşük":
        triggers.append("hydration")
    if profile.get("sleep_hours", 7) < 7:
        triggers.append("sleep")
    if "Occlusive makyaj" in profile.get("skincare", []):
        triggers.append("occlusive")
    profile["triggers"] = triggers

    query_terms = [severity] + concerns + triggers
    query_text = " ".join(query_terms) or severity
    similarity_scores = dict((r.id, sim) for r, sim in _query_embedding(query_text))

    ranked: List[Tuple[float, Remedy]] = []
    for remedy in remedies:
        base = _base_score(remedy, severity, profile, concerns)
        sim = similarity_scores.get(remedy.id, 0.0)
        total = base + 1.5 * sim
        ranked.append((total, remedy))

    ranked.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, remedy in ranked[:top_k]:
        results.append(
            {
                "id": remedy.id,
                "title": remedy.title,
                "summary": remedy.summary,
                "score": round(score, 2),
                "evidence": remedy.evidence,
                "instructions": remedy.instructions,
                "warnings": remedy.warnings,
                "sources": remedy.sources,
                "community": remedy.community,
            }
        )
    return results


def build_safety_alerts(severity: str, inflamed_pct: float, regions: int) -> List[str]:
    alerts: List[str] = []
    if severity in ("Severe", "Very Severe"):
        alerts.append("Şiddetli akne şüphesi: Dermatolog görüşü planla.")
    if inflamed_pct > 25:
        alerts.append("Yaygın inflamasyon tespit edildi, tahriş edici aktifleri azalt.")
    if regions >= 6:
        alerts.append("Birden fazla inflamasyon odağı var, antibakteriyel bakım değerlendir.")
    return alerts


def community_highlights(remedy_data: List[Dict[str, Any]], top_k: int = 3) -> List[str]:
    highlights: List[str] = []
    for item in remedy_data:
        for quote in item.get("community", [])[:1]:
            highlights.append(f"{item['title']}: {quote}")
        if len(highlights) >= top_k:
            break
    return highlights

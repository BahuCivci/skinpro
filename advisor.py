"""Recommendation helpers for SkinPro."""
from __future__ import annotations
from typing import Dict, List

Severity = str

_SEVERITY_NOTES: Dict[Severity, Dict[str, List[str]]] = {
    "Clear": {
        "focus": ["Cildi koru, bariyer dostu ürünler kullan."],
        "actives": ["Nazik temizleyici", "Gündüz SPF 30+"],
    },
    "Mild": {
        "focus": ["Komodojenik olmayan baz ürünler seç."],
        "actives": ["Salicylic asit (haftada 2-3 kez)", "Niacinamide serum"],
    },
    "Moderate": {
        "focus": ["İltihap kontrolü ve komedon temizliği"],
        "actives": ["Benzoyl peroxide (düşük %, spot)", "Retinoid (gece)"],
    },
    "Severe": {
        "focus": ["Profesyonel destek ve anti-inflamatuar bakım"],
        "actives": ["Dermatolog görüşü", "Topikal/ oral tedavi değerlendirmesi"],
    },
    "Very Severe": {
        "focus": ["Acil dermatolog yönlendirmesi"],
        "actives": ["Sistemik tedavi gerektirebilir"],
    },
}

_TRIGGER_NOTES = {
    "high_glycemic": "Düşük glisemik indeksli beslenme planı ekle.",
    "dairy": "Süt ürünlerini sınırlamak bazı kişilerde lezyonları azaltabilir.",
    "stress": "Günlük nefes egzersizleri ve stres yönetimi rutinini ekle.",
    "sleep": "7-8 saat uyku hedefle, uyku hijyeni oluştur.",
    "hydration": "Su tüketimini günde 2L seviyesine çıkar.",
    "occlusive": "Ağır/komedojenik ürünleri hafif dokulu seçeneklerle değiştir.",
}

_DEFICIT_TIPS = {
    "spf": "Günlük SPF kullanımı, leke ve kızarıklıkların kötüleşmesini engeller.",
    "cleanser": "SLS içermeyen nazik temizleyici bariyeri destekler.",
    "moisturizer": "Nem bariyeri bozulduysa seramid veya hyaluronik asit içeren krem ekle.",
}


def _collect_triggers(profile: Dict[str, str]) -> List[str]:
    triggers: List[str] = []
    if profile.get("diet") == "Yüksek Şeker":
        triggers.append(_TRIGGER_NOTES["high_glycemic"])
    if profile.get("diet") == "Süt Ağırlıklı":
        triggers.append(_TRIGGER_NOTES["dairy"])
    if profile.get("stress") in ("Yüksek", "Çok Yüksek"):
        triggers.append(_TRIGGER_NOTES["stress"])
    if profile.get("sleep_hours", 7) < 7:
        triggers.append(_TRIGGER_NOTES["sleep"])
    if profile.get("hydration") == "Düşük":
        triggers.append(_TRIGGER_NOTES["hydration"])
    if "Occlusive makyaj" in profile.get("skincare", []):
        triggers.append(_TRIGGER_NOTES["occlusive"])
    return triggers


def _collect_gaps(routine: List[str]) -> List[str]:
    gaps: List[str] = []
    has = set(routine)
    if "SPF" not in has:
        gaps.append(_DEFICIT_TIPS["spf"])
    if "Nazik temizleyici" not in has and "Temizleyici" not in has:
        gaps.append(_DEFICIT_TIPS["cleanser"])
    if "Nemlendirici" not in has:
        gaps.append(_DEFICIT_TIPS["moisturizer"])
    return gaps


def build_plan(profile: Dict[str, str], severity: Severity, inflamed_pct: float) -> Dict[str, List[str]]:
    severity_block = _SEVERITY_NOTES.get(severity, _SEVERITY_NOTES["Mild"])
    triggers = _collect_triggers(profile)
    routine_items = profile.get("skincare", [])
    deficits = _collect_gaps(routine_items)

    weekly_focus: List[str] = []
    if severity in ("Moderate", "Severe", "Very Severe"):
        weekly_focus.append("Profesyonel bakımla takip için 4 haftada bir fotoğraf karşılaştır.")
    if inflamed_pct > 12:
        weekly_focus.append("Kızarıklığı azaltmak için yeşil çaylı/niacinamide tonik ekle.")
    if profile.get("hormonal") == "Belirgin dalgalanma":
        weekly_focus.append("Dönemsel alevlenmeler için siklik retinoid planı çıkar.")

    return {
        "Focus": severity_block["focus"],
        "Aktif Önerileri": severity_block["actives"],
        "Yaşam Tarzı": triggers,
        "Eksik Rutin": deficits,
        "Haftalık Takip": weekly_focus,
    }

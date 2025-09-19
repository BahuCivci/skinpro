"""Streamlit front-end for the SkinPro super app prototype."""
import io
from typing import Optional

import streamlit as st
from PIL import Image

from advisor import build_plan
from inference import analyze_image
from knowledge import (
    build_safety_alerts,
    community_highlights,
    recommend_remedies,
)

st.set_page_config(page_title="SkinPro — AI", page_icon="💠", layout="wide")

if "latest_result" not in st.session_state:
    st.session_state.latest_result = None
    st.session_state.latest_image = None

st.title("SkinPro · Akıllı Cilt Koçu")
sub = (
    "Bilgisayarlı görü ile akne derecelendirmesi, bilgi bankası ve kişisel rutin koçu bir arada."
)
st.caption(sub)

tab_analysis, tab_learn, tab_coach = st.tabs(["AI Analiz", "Bilgi Bankası", "Rutin Koçu"])


def _ingest_image() -> Optional[Image.Image]:
    method = st.radio("Girdi", ["Yükle", "Selfie"], horizontal=True)
    if method == "Yükle":
        uploaded = st.file_uploader("Yüz fotoğrafı (JPG/PNG)", type=["jpg", "jpeg", "png"])
        if uploaded:
            return Image.open(uploaded).convert("RGB")
    else:
        cam = st.camera_input("Selfie çek")
        if cam:
            return Image.open(io.BytesIO(cam.getvalue())).convert("RGB")
    return None


with tab_analysis:
    st.subheader("Cilt Fotoğrafını Analiz Et")
    st.markdown(
        "- Doğal ışıkta, makyajsız bir fotoğraf tercih edin.\n"
        "- Yerelde ONNX modeli yoksa otomatik olarak buluttan Hugging Face modeli indireceğiz."
    )

    pil_img = _ingest_image()

    if pil_img is None:
        st.info("Başlamak için fotoğraf yükleyin veya selfie çekin.")
    else:
        st.image(pil_img, caption="Analiz Edilen Fotoğraf", use_container_width=True)
        with st.spinner("Analiz ediliyor…"):
            result = analyze_image(pil_img)
        st.success("Analiz tamamlandı")

        grade = result["final_grade"]
        conf_pct = int(result["confidence"] * 100)
        redness = result["inflamed_area_pct"]
        lesions = result.get("lesions", {})
        regions = lesions.get("regions", [])
        detector_regions = lesions.get("detector_regions", [])
        texture_score = lesions.get("texture_score", 0.0)
        pore_proxy = lesions.get("pore_proxy", 0.0)

        met1, met2, met3 = st.columns(3)
        met1.metric("Akne Şiddeti", grade)
        met2.metric("Model Güveni", f"%{conf_pct}")
        met3.metric("Kızarıklık Yoğunluğu", f"%{redness:.1f}")

        st.progress(min(100, int(redness)), text="Kızarıklık göstergesi")

        used = result.get("used", {})
        st.caption(
            "Kullanılan modeller → "
            f"ONNX: {used.get('classifier_onnx')}, "
            f"HF: {used.get('classifier_hf')}, "
            f"Heuristik: {used.get('heuristic')}"
        )

        meta = result.get("meta", {})
        if meta.get("hf_models"):
            st.caption("HF modelleri: " + ", ".join(meta["hf_models"]))
        if meta.get("hf_errors"):
            with st.expander("Yüklenemeyen modeller", icon="⚠️"):
                for model_id, err in meta["hf_errors"].items():
                    st.write(f"- {model_id}: {err}")

        detector_meta = meta.get("detector", {})
        if detector_meta.get("error"):
            st.caption(f"Lesyon dedektörü hazır değil: {detector_meta['error']}")
        elif detector_meta.get("count"):
            st.caption(f"Lesyon dedektörü {detector_meta['count']} bulgu döndürdü.")

        with st.expander("Model ensembli ayrıntıları", icon="🧠"):
            for pred in meta.get("ensemble", []):
                st.write(
                    f"{pred['source']}: {pred['label']} (ham etiket: {pred['raw_label']}, güven: {pred['confidence']:.2f})"
                )

        if regions:
            st.markdown("**Algılanan inflamasyon odakları**")
            st.write(f"Toplam {len(regions)} odak, tahmini kızarıklık kapsama %{sum(r['area_pct'] for r in regions):.1f}")
            top_regions = regions[:3]
            for idx, box in enumerate(top_regions, start=1):
                st.write(
                    f"{idx}. Bölge → alan %{box['area_pct']:.1f}, konum (x={box['x']:.2f}, y={box['y']:.2f})"
                )
        else:
            st.write("Belirgin inflamasyon odağı tespit edilmedi.")

        if detector_regions:
            st.markdown("**Lesyon dedektörü**")
            st.write(f"Toplam {len(detector_regions)} tespit")
            preview = detector_regions[:5]
            for det in preview:
                st.write(
                    f"- Tür: {det.get('label','?')} · Güven: {det.get('confidence',0):.2f} · Alan %{det.get('area_pct',0):.1f}"
                )
        elif not detector_meta.get("error"):
            st.write("Lesyon dedektörü mevcut ancak henüz tespit döndürmedi.")

        st.caption(
            f"Doku skoru: {texture_score:.1f} · Gözenek göstergesi: {pore_proxy:.1f}"
        )

        st.session_state.latest_result = result
        st.session_state.latest_image = pil_img

with tab_learn:
    st.subheader("Cilt Problemleri ve Nedenleri")
    st.markdown(
        "**Akne türleri** — komedonal (siyah/beyaz noktalar), inflamatuvar (papül, püstül), nodül/kist.\n"
        "**Kızarıklık ve hassasiyet** — rosacea, seboroik dermatit, bariyer zayıflığı.\n"
        "**Leke ve düzensizlik** — post-inflamatuvar hiperpigmentasyon, melazma, güneş lekeleri."
    )

    st.subheader("Başlıca Tetikleyiciler")
    st.markdown(
        "- **Genetik & hormonlar**: Androjen dalgalanmaları, PCOS, dönemsel değişimler.\n"
        "- **Beslenme**: Yüksek glisemik indeks, süt ürünleri, omega-3 eksikliği.\n"
        "- **Yaşam tarzı**: Stres, uyku yetersizliği, yetersiz su tüketimi.\n"
        "- **Çevresel**: Kirlilik, UV, yüksek nem veya maske kullanımı."
    )

    st.subheader("AI Tabanlı Değer")
    st.markdown(
        "- Görüntü tabanlı şiddet skoru ile ilerlemeyi takip et.\n"
        "- Kızarıklık, doku ve leke trendlerini zaman içinde ölç.\n"
        "- Tehlikeli lezyonları tespit edip dermatoloğa yönlendir (yolda)."
    )

with tab_coach:
    st.subheader("Kişisel Rutin Koçu")
    latest = st.session_state.latest_result
    if latest is None:
        st.info("Önce AI Analiz sekmesinde bir fotoğraf analiz edin.")
    else:
        col_a, col_b = st.columns([2, 1])
        with col_b:
            if st.session_state.latest_image is not None:
                st.image(st.session_state.latest_image, caption="Son Analiz", use_container_width=True)
        with col_a:
            st.markdown(
                f"**Mevcut Durum**: {latest['final_grade']} · Model güveni %{int(latest['confidence']*100)} · "
                f"Kızarıklık %{latest['inflamed_area_pct']:.1f}"
            )

        with st.form("coach_form"):
            diet = st.selectbox("Beslenme alışkanlığı", ["Dengeli", "Yüksek Şeker", "Süt Ağırlıklı"])
            stress = st.select_slider("Stres seviyesi", options=["Düşük", "Orta", "Yüksek", "Çok Yüksek"], value="Orta")
            sleep_hours = st.slider("Günlük uyku", 4, 10, 7)
            hydration = st.selectbox("Su tüketimi", ["Yeterli", "Düşük"])
            hormonal = st.selectbox("Hormonal durum", ["Stabil", "Belirgin dalgalanma"])
            skincare = st.multiselect(
                "Rutininde olanlar",
                [
                    "Nazik temizleyici",
                    "Temizleyici",
                    "Nemlendirici",
                    "SPF",
                    "Retinoid",
                    "Salicylic asit",
                    "Benzoyl peroxide",
                    "Niacinamide",
                    "Occlusive makyaj",
                ],
            )
            submitted = st.form_submit_button("Plan Oluştur")

        if submitted:
            profile = {
                "diet": diet,
                "stress": stress,
                "sleep_hours": sleep_hours,
                "hydration": hydration,
                "hormonal": hormonal,
                "skincare": skincare,
            }
            concerns = []
            if latest["inflamed_area_pct"] > 12:
                concerns.append("redness")
            if latest["inflamed_area_pct"] > 20:
                concerns.append("inflammation")
            lesion_meta = latest.get("lesions", {})
            if lesion_meta.get("texture_score", 0) > 120.0:
                concerns.append("texture")
            if lesion_meta.get("pore_proxy", 0) > 18.0:
                concerns.append("blackheads")

            plan = build_plan(profile, latest["final_grade"], latest["inflamed_area_pct"])
            st.success("Rutin önerisi hazır")
            for heading, items in plan.items():
                if not items:
                    continue
                st.markdown(f"**{heading}**")
                for item in items:
                    st.write(f"- {item}")

            recs = recommend_remedies(latest["final_grade"], profile, concerns)
            alerts = build_safety_alerts(
                latest["final_grade"], latest["inflamed_area_pct"], len(lesion_meta.get("regions", []))
            )
            highlights = community_highlights(recs)

            if alerts:
                st.error("\n".join(alerts))

            st.markdown("**Doğal & klinik çözümler**")
            for rec in recs:
                with st.expander(f"{rec['title']} · Skor {rec['score']}"):
                    st.write(rec["summary"])
                    st.write(f"_Kanıt düzeyi_: {rec['evidence']}")
                    st.write(f"**Uygulama**: {rec['instructions']}")
                    if rec["warnings"]:
                        st.warning("; ".join(rec["warnings"]))
                    if rec["sources"]:
                        for src in rec["sources"]:
                            st.caption(f"Kaynak: [{src['label']}]({src['url']})")
                    if rec["community"]:
                        st.caption("Topluluk notları: " + " | ".join(rec["community"]))

            if highlights:
                st.markdown("**Topluluk Deneyimleri**")
                for quote in highlights:
                    st.write(f"- {quote}")

        st.info("Profesyonel tedavi gerektiren durumlarda dermatoloğa danışmayı unutmayın.")

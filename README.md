# SkinPro — AI Cilt Analiz ve Koç

Bu repo; Streamlit tabanlı ön yüz, yerel/Hugging Face sınıflandırıcıların birleşimi ve YOLOv8 tabanlı lezyon dedektörü ile cilt analizi yapan “super app” prototipini içerir. Aşağıdaki notlar projenin nasıl kurulduğunu, modeli nasıl eğittiğimizi ve uygulamanın onu nasıl kullandığını özetler.

## 1. Uygulamayı Çalıştır
```bash
cd /Users/bahu/saglik/skinpro
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
- Varsayılan port `http://localhost:8501`
- Watchdog önerisi çıkarsa `python -m pip install watchdog` ile yükleyebilirsiniz.

## 2. Model Mimarisinin Özeti
- **Şiddet sınıflandırma**: `inference.py` önce yerel `severity_cls.onnx` (varsa) sonra Hugging Face modellerini (`imfarzanansari/skintelligent-acne`, `afscomercial/dermatologic`) çağırır.
- **Lezyon dedektörü**: `models/skin_lesion.onnx` (ve yedeği `skin_lesion.pt`) bizim Colab’de YOLOv8 ile eğittiğimiz ağ. `inference._run_lesion_detector` Ultralytics `YOLO` API’si ile model dosyasını açar ve sonuçları 0.30 güven eşiği üzerinde döndürür.
- **Analiz sonuçları**: `analysis_utils.draw_detector_overlay` ile kutular verile fotoğraf üzerine çizilir; Streamlit “Lesyon dedektörü” bölümünde overlay ve ilk 10 kutu listelenir.

## 3. Eğitim Süreci (Colab)
1. **Repo & bağımlılıklar**
   ```python
   !git clone <repo-url> skinpro
   %cd skinpro
   !pip install -r requirements.txt
   !pip install ultralytics
   ```
2. **Roboflow veri setini indir**
   ```python
   import os
   os.environ['ROBOFLOW_API_KEY'] = 'emxaIJ01NYmdtUjFcNA2'  # örnek
   !python detector/scripts/download_dataset.py \
       --api-key $ROBOFLOW_API_KEY \
       --workspace mta-jycu6 \
       --project skin-problem-detection-relabel-kxrif \
       --version 2 \
       --overwrite
   ```
   - Zip `detector/datasets/skin_problems/` altına açılır.
   - `data.yaml` otomatik olarak `detector/data/roboflow_skin.yaml` dosyasına kopyalanır.
3. **YOLOv8 eğitimi**
   ```python
   !python detector/scripts/train_detector.py \
       --data detector/data/roboflow_skin.yaml \
       --model yolov8n.pt \
       --epochs 45 \
       --img-size 1024 \
       --batch 16 \
       --device 0 \
       --project runs/lesion_colab \
       --name exp_gpu2
   ```
   - GPU (T4) üzerinde eğitim ~2 saat sürdü.
   - Sonuçlar `runs/lesion_colab/exp_gpu2/weights/best.pt` içinde.
4. **ONNX’e dışa aktar ve indir**
   ```python
   !yolo export model=runs/lesion_colab/exp_gpu2/weights/best.pt format=onnx imgsz=1024
   from google.colab import files
   files.download('runs/lesion_colab/exp_gpu2/weights/best.pt')
   files.download('runs/lesion_colab/exp_gpu2/weights/best.onnx')
   ```
   - Dosyaları lokal makinedeki `models/skin_lesion.pt` ve `models/skin_lesion.onnx` olarak kaydettik.

## 4. Yerel Entegrasyon
- `inference.py` içinde `_load_detector_model()` önce ONNX, bulunamazsa PT dosyasını dener; Ultralytics `YOLO` nesnesi döner.
- `_run_lesion_detector(img)` modeli çağırıp maksimum 10 kutu döndürür; meta alanında kaç tespit yapıldığını ve kullanılan dosya yolunu gösterir (`meta['detector']['model']`).
- `SKINPRO_DETECTOR_CONF` ortam değişkeni ile eşiği değiştirebilirsiniz. Örn: `SKINPRO_DETECTOR_CONF=0.25 python -m streamlit run app.py`.

## 5. Tipik Çalışma Akışı
1. Uygulama çalışırken “AI Analiz” sekmesinde fotoğraf yükle.
2. “Lesyon dedektörü” girişinde overlay görünür; liste kutu etiketlerini, güven ve alan yüzdesini gösterir.
3. Rutin Koçu sekmesi, tespitlere ve kullanıcı anketine göre plan sunar.

## 6. Kullanılan Başlıca Dosyalar
- `app.py` – Streamlit ön yüzü (tabs, overlay görselleri, raporlar).
- `inference.py` – ONNX/HF/YOLO modellerinin orkestrasyonu.
- `analysis_utils.py` – Görüntü işleme yardımcıları ve overlay çizimi.
- `detector/` – YOLO eğitimi, veri indirme scriptleri, notlar.

## 7. FastAPI Backend (Mobil/harici istemciler)
- API servisi `api/server.py` içinde FastAPI ile tanımlandı.
- Uçlar:
  - `GET /health` → basit sağlık kontrolü.
  - `POST /analyze` → `multipart/form-data` ile `file` alanı (görüntü). Yanıt: `analyze_image` çıktısı, `lesions.detector_overlay` alanı base64 PNG olarak dönüyor.
  - `POST /coach` → JSON gövdesi: `{ "profile": {...}, "analysis": {...} }`. Yanıt: bakım planı, önerilen çözümler, güvenlik uyarıları, topluluk özetleri.
- CORS varsayılan olarak tüm origin’lere açık; mobil/ web istemciler direkt çağırabilir.
- Çalıştırmak için:
  ```bash
  uvicorn api.server:app --host 0.0.0.0 --port 8000
  ```
  (Docker/Cloud Run gibi ortamlarda `PORT` değişkenine göre ayarlayabilirsiniz.)
- Hızlı test için:
  ```bash
  # Health ve root
  curl http://localhost:8000/
  curl http://localhost:8000/health

  # Görüntü analizi
  curl -X POST "http://localhost:8000/analyze" \
       -F "file=@samples/face.jpg" \
       -H "accept: application/json"

  # CLI helper
  python scripts/test_api.py path/to/photo.jpg
  ```

---
Sorular veya yeni veri ile fine-tuning ihtiyacı oluşursa `detector/scripts/train_detector.py` ve `detector/scripts/eval_detector.py` script’lerini kullanarak süreci tekrarlayabilirsin.

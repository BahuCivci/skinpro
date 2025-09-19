# SkinPro Lesion Detector

This directory holds training assets for a multi-class lesion detection/segmentation model (milia, comedones, papules, cysts, scars, erythema).

## Dataset Checklist
- Organize data as YOLOv8 segmentation format (`images/train`, `labels/train`, `images/val`, `labels/val`).
- Each `.txt` label follows: `class x_center y_center width height` or polygon masks for segmentation.
- Maintain a `data.yaml` describing class names and dataset roots.

### Quickstart with Roboflow Universe
We can bootstrap with the public dataset [Skin Problem Detection (Relabel)](https://universe.roboflow.com/parin-kittipongdaja-vwmn3/skin-problem-detection-relabel).

```
export ROBOFLOW_API_KEY=your_key
python detector/scripts/download_dataset.py \
  --version 1 \
  --output detector/datasets/skin_problems \
  --overwrite
```

The script downloads the YOLOv8 export, copies its `data.yaml` to `detector/data/roboflow_skin.yaml`, and keeps the original Roboflow class names (covering acne, blackheads, milia, wrinkles, etc.).

```
path: /absolute/path/to/skinpro_dataset
train: images/train
val: images/val
names:
  0: milia
  1: whitehead
  2: blackhead
  3: papule
  4: pustule
  5: cyst
  6: hyperpigmentation
  7: scar
```

## Labeling Workflow
1. Export initial photo set from the app with anonymized metadata.
2. Label with a dermatology QA loop (Labelbox, Roboflow, or CVAT).
3. Run `scripts/prepare_dataset.py` (todo) to validate polygons and stratify folds.

## Training
```
python detector/scripts/train_detector.py \
  --data detector/data/roboflow_skin.yaml \
  --model yolov8n.pt \
  --epochs 150 \
  --img-size 1024 \
  --device cpu        # GPU varsa '0' gibi değiştir
```

## Evaluation
```
python detector/scripts/eval_detector.py \
  --weights runs/lesion/best.pt \
  --data /path/to/data.yaml \
  --split val
```

## Export for Inference
```
python -m ultralytics export \
  model=runs/lesion/best.pt \
  format=onnx \
  imgsz=1024 \
  opset=13 \
  simplify=True \
  project=exports/ \
  name=lesion_onnx
```
Move the resulting `lesion_onnx/model.onnx` into `models/skin_lesion.onnx` and reference it from the app (see inference integration stub).

## Immediate Next Steps
- Finalize annotation schema with dermatologist review (class definitions, mask granularity).
- Label an initial 500–1,000 high-resolution images stratified by skin tone and lighting.
- Run `train_detector.py` with mixed precision on a GPU box; monitor per-class mAP.
- Validate on a holdout set and collect false positives/negatives for active learning.
- Convert the best checkpoint to ONNX and drop into `models/` to activate detections inside the app.

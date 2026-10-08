# Chest X-ray Two-Stage Triage

![tests](https://github.com/<your-username>/chest-xray-triage/actions/workflows/tests.yml/badge.svg)

A two-stage pipeline for chest X-ray abnormality detection on the public
[VinDr-CXR](https://physionet.org/content/vindr-cxr/) dataset (VinBigData):

1. **Gate:** a ResNet-50 classifier scores each image as normal or abnormal.
2. **Localize:** YOLOv8 runs only on images the gate flags, and predicts boxes for 14 finding classes.
3. **Serve:** a FastAPI service with a web UI, Grad-CAM explanations, and an optional ONNX backend.

It also includes temperature-scaling calibration for the gate, a latency benchmark
(detector-only vs. two-stage, PyTorch vs. ONNX), API contract tests, and CI.

> Independent project built entirely on public data. Research demo only, not for
> clinical use.

```
image ──► ResNet-50 ──► P(abnormal) ≥ τ ? ──no──► "no finding" (detector skipped)
                                        └─yes─► YOLOv8 ──► boxes + classes
```

## Why two stages

About 70% of VinDr-CXR images are "No finding". Sending every image through a
1024-px detector wastes compute on those images. A cheaper classifier screens
them out first, so mean latency drops roughly in proportion to the normal share.

The cost is that any abnormal image the gate misses never reaches the detector.
For that reason the gate threshold τ is **picked on the validation set for a
target sensitivity** (default 95%) rather than at 0.5, and `evaluate.py` reports
mAP for both modes so the trade-off is measured, not assumed.

## Design decisions

| Decision | Reason |
|---|---|
| Image is abnormal if **any** radiologist marked a finding | Favors recall. Majority vote is the alternative, with less label noise. |
| **Weighted Boxes Fusion** across the 3 radiologists | Each image has up to 3 annotators whose boxes disagree. WBF averages overlapping boxes instead of dropping some, as NMS would. |
| **No horizontal flips** in either model | Chest anatomy is lateralized (heart on the left), so a flipped X-ray is not a realistic sample. |
| `pos_weight` in BCE | Handles the ~70/30 class imbalance. |
| Threshold chosen on **val**, reported on **test** | Avoids tuning on the test set. |
| **mAP@0.4** | The VinBigData competition metric. |
| **Temperature scaling** on val | Makes P(abnormal) trustworthy as a probability without changing the ranking (AUC). |
| **Grad-CAM** on the gate | Shows which regions drove a flag. Useful for debugging and for building user trust. |

## Docs

- `docs/GUIDE.md`: a detailed walkthrough of every file, how to read the results, and common errors
- `docs/MODEL_CARD.md`: intended use, data, limitations, and ethical considerations
- `notebooks/kaggle_run.ipynb`: run the whole pipeline on a free Kaggle GPU

## Setup

```bash
pip install -r requirements.txt
```

### Data

Download VinDr-CXR from the VinBigData Kaggle competition, or use any PNG
conversion of it. Then point `configs/default.yaml` at:

- `raw_csv`: `train.csv` (columns `image_id, class_name, class_id, rad_id, x_min, y_min, x_max, y_max`)
- `image_dir`: a folder of `<image_id>.png`
- `meta_csv`: required only if the PNGs were **resized**. It should hold the original
  dims (`image_id, dim0=height, dim1=width`), because the boxes are in original DICOM pixels.
  If your PNG set lacks one, build it from the DICOM headers: `python -m src.make_meta --dicom_dir <dicom dir>`.

## Run

Every step below also has a `make` shortcut (`make help` lists them, and `make all` runs the full pipeline).

```bash
python -m src.data             --config configs/default.yaml   # labels, WBF boxes, YOLO dataset
python -m src.train_classifier --config configs/default.yaml   # stage 1
python -m src.train_detector   --config configs/default.yaml   # stage 2
python -m src.evaluate         --config configs/default.yaml   # AUC, sens/spec, mAP@0.4 -> runs/eval.json
python -m src.benchmark        --config configs/default.yaml --half   # latency -> runs/benchmark_torch.json
python -m src.export_onnx      --config configs/default.yaml          # -> runs/export/*.onnx
python -m src.benchmark        --config configs/default.yaml --backend onnx
python -m src.plots                                                   # figures -> docs/figures/
```

After evaluating, copy `gate_threshold_from_val` and `temperature` from
`runs/eval.json` into the `pipeline` section of the config. Run the benchmark
only after that, so it uses the right threshold.

### Serve

```bash
CLS_CKPT=runs/classifier/best.pt DET_WEIGHTS=runs/detector/yolov8s/weights/best.pt \
  uvicorn app.server:app --port 8000

curl -F "file=@sample.png" "localhost:8000/predict?mode=two_stage"
curl -F "file=@sample.png" localhost:8000/explain -o gradcam.png
```

Open http://localhost:8000 for the web UI. It lets you upload an image, draws the
boxes, shows P(abnormal) and latency, and renders the Grad-CAM overlay. Swagger is
at `/docs`.

Optional environment variables: `GATE_THRESHOLD`, `TEMPERATURE`, `DET_CONF`,
`DET_IMGSZ`, and `HALF=1`. Pointing `CLS_CKPT` and `DET_WEIGHTS` at `.onnx` files
switches to the ONNX backend. Grad-CAM is not available on that backend.

Or use Docker: `docker build -t cxr-triage .` and mount the weights at `/models`.

## Results

Fill these in from `runs/eval.json` and `runs/benchmark_*.json` after training.
`python -m src.plots` writes these figures; commit them so they render here:

| ROC + gate operating point | Calibration | Per-class AP |
|---|---|---|
| ![ROC](docs/figures/roc.png) | ![Reliability](docs/figures/reliability.png) | ![AP](docs/figures/per_class_ap.png) |


| Metric | Value |
|---|---|
| Classifier test AUC | |
| Sensitivity / specificity at τ | |
| mAP@0.4, detector only | |
| mAP@0.4, two-stage | |
| ECE before → after calibration | |
| Mean latency, detector only → two-stage | |
| Mean latency, PyTorch → ONNX | |

## Data and license

The dataset is **not** included in this repo. Get VinDr-CXR from its official
sources and follow their terms of use. Trained weights are not distributed.
The code is released under the MIT License (see `LICENSE`).

## Tests

```bash
python -m pytest -q   # or: make test
ruff check .          # or: make lint
```

These cover the mAP implementation, threshold selection, calibration, data
preparation (WBF fusion, stratified splits, YOLO export), and the API contract
(with a stub model). None of them need a GPU or trained weights, and CI runs them
on every push.

## Possible extensions

- TensorRT engines for both stages
- Batched inference in the server
- Class-specific gate thresholds
- External validation on a US dataset (CheXpert or MIMIC-CXR)

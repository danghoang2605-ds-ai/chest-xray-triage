# Detailed Guide: Chest X-ray Two-Stage Triage

This guide goes from zero to a working demo. It explains every part in enough depth to understand and defend each design choice.

**Contents**
1. Problem and dataset
2. Architecture
3. File flow
4. Running on Kaggle, step by step
5. Code walkthrough
6. Reading the results
7. Common errors
8. Design FAQ

---

## 1. Problem and dataset

**The problem.** Given a chest X-ray, the system answers two questions:
- Is the image normal or abnormal? This is a classification task.
- If it is abnormal, where are the findings and what kind are they? This is a detection task.

**The data.** VinDr-CXR was released by VinBigData and used in the Kaggle competition "VinBigData Chest X-ray Abnormalities Detection".
- The training set has 15,000 images. Each image was read independently by **3 radiologists**, drawn from a pool of 17.
- There are 14 finding classes (0–13), plus class 14 for "No finding".
- About **70% of images are "No finding"**, so the classes are heavily imbalanced.

**`train.csv` format.** Each row is **one box drawn by one radiologist**, not one image:

| image_id | class_name | class_id | rad_id | x_min | y_min | x_max | y_max |
|---|---|---|---|---|---|---|---|
| abc123 | Cardiomegaly | 3 | R9 | 691 | 1375 | 1653 | 1831 |
| abc123 | Cardiomegaly | 3 | R10 | 700 | 1380 | 1640 | 1820 |
| abc123 | Aortic enlargement | 0 | R9 | 1200 | 600 | 1400 | 800 |
| def456 | No finding | 14 | R1 | NaN | NaN | NaN | NaN |

Three things to keep in mind:
1. **One finding can have 2–3 slightly different boxes**, one per radiologist, so the boxes must be fused (section 5.1).
2. **Coordinates are in original DICOM pixels**, usually around 2000–3000 px. If you use PNGs resized to 1024, you need the original dimensions to rescale the boxes.
3. **Radiologists can disagree.** For example, R1 may say "No finding" while R2 draws a box (section 5.1).

---

## 2. Architecture

```
                    ┌──────────────────────┐
 X-ray image ─────► │ Stage 1: ResNet-50    │ ──► P(abnormal) = 0.12
                    │ (fast, 512 px)        │
                    └──────────────────────┘
                               │
                    P ≥ τ ?  ──┴── no ──► "No finding", detector SKIPPED
                               │
                              yes
                               ▼
                    ┌──────────────────────┐
                    │ Stage 2: YOLOv8       │ ──► [Cardiomegaly 0.81, box...]
                    │ (slow, 1024 px)       │     [Pleural effusion 0.64, box...]
                    └──────────────────────┘
```

**Why two stages instead of YOLO alone?**
- YOLO at 1024 px is expensive, and running it on the ~70% of images that are normal wastes compute.
- A ResNet at 512 px is much cheaper. It screens out normal images first, which lowers mean latency.
- **The trade-off:** if the gate misses an abnormal image (a false negative), the detector never sees it and the finding is lost. That is why τ is chosen for **≥ 95% sensitivity** rather than left at 0.5.

**Latency rule of thumb:**
```
latency_two_stage ≈ t_ResNet + (fraction flagged) × t_YOLO
```
For example, with t_ResNet = 8 ms, t_YOLO = 40 ms, and 50% of images flagged, you get 8 + 20 = 28 ms instead of 40 ms, a 30% reduction. These numbers are illustrative only. Your real numbers come from `benchmark.py`.

---

## 3. File flow

```
train.csv + PNGs ──[src/data.py]──► data/processed/labels.csv   (one row per image: abnormal 0/1, split)
                                    data/processed/boxes.csv    (fused boxes, normalized 0–1)
                                    data/processed/yolo/        (YOLO-format dataset)

labels.csv ──[src/train_classifier.py]──► runs/classifier/best.pt
yolo/      ──[src/train_detector.py]────► runs/detector/yolov8s/weights/best.pt

both .pt ──[src/evaluate.py]──► runs/eval.json       (AUC, sens/spec, mAP, threshold τ)
         ──[src/benchmark.py]─► runs/benchmark.json  (latency)
         ──[app/server.py]────► API at http://localhost:8000/predict
```

---

## 4. Running on Kaggle, step by step

Kaggle gives you about 30 free GPU hours per week, and the competition data is already hosted there.

### Step 0: Account setup
- Verify your phone number in Kaggle Settings. Notebooks need this before you can turn on **Internet** and **GPU**.
- Open the *VinBigData Chest X-ray Abnormalities Detection* competition page and accept the rules so you can use the data.

### Step 1: Put the code on Kaggle
1. Go to Kaggle → **Datasets** → **New Dataset**, and upload `chest-xray-triage.zip`.
2. Name it something like `cxr-triage-code` and set it to Private or Public.

### Step 2: Create a notebook
1. Go to **Code** → **New Notebook**.
2. In the right panel, set **Accelerator: GPU T4 x2** (or P100) and **Internet: On**. Internet is needed to download pretrained weights.
3. Under **Add Input**, add three things:
   - the competition `vinbigdata-chest-xray-abnormalities-detection` (for `train.csv` and the DICOMs),
   - a resized PNG version of VinBigData (search Datasets for "vinbigdata png 1024"),
   - your `cxr-triage-code` dataset.
4. Open `notebooks/kaggle_run.ipynb` from the repo. Every cell is ready to copy over.

### Step 3: Check paths
```python
!ls /kaggle/input
!ls /kaggle/input/<png-dataset-name> | head
```
Note down:
- the path to `train.csv`,
- the PNG folder (files named `<image_id>.png`),
- the meta file, if the PNG dataset includes one (usually `train_meta.csv` with `image_id, dim0, dim1`).

**If there is no meta file**, build one from the DICOM headers. This reads headers only, so it takes a few minutes:
```bash
python -m src.make_meta --dicom_dir /kaggle/input/vinbigdata-chest-xray-abnormalities-detection/train \
                        --out data/raw/train_meta.csv
```

**Critical:** if the PNGs are resized and you skip the meta file, every box ends up in the wrong place. The code would treat original ~2500 px coordinates as 1024 px coordinates. Training still runs, but mAP comes out near zero.

### Step 4: Prepare the data
```bash
python -m src.data --config configs/kaggle.yaml
```
The output should look roughly like this:
```
images: 15000 | abnormal: 29.3% | fused boxes: ...
       count   mean
split
test    1500   0.293
train  12000   0.293
val     1500   0.293
```
Two checks:
- The `mean` column should be nearly identical across splits, because the split is stratified.
- The fused box count should be well below the number of box rows in `train.csv`, because WBF merged the duplicates.

### Step 5: Train the classifier (~45–90 min on a T4)
```bash
python -m src.train_classifier --config configs/kaggle.yaml
```
Each epoch prints a line like this:
```
epoch 01 | loss 0.6123 | val AUC 0.8734 | 312s
```
AUC should rise over the first few epochs and then plateau. `best.pt` is saved at the epoch with the highest AUC.

### Step 6: Train YOLO (several hours)
```bash
python -m src.train_detector --config configs/kaggle.yaml
```
**Do a small run first.** Set `img_size: 640` and `epochs: 10` to confirm the whole pipeline works end to end, then run the full version.

Ultralytics prints mAP50 each epoch. That is mAP@0.5, not the mAP@0.4 that `evaluate.py` computes, but the trend is the same.

### Step 7: Save your outputs (important)
Everything in `/kaggle/working` **disappears when the session ends**. You have two options:
- Use **Save Version → Save & Run All (Commit)**. The notebook runs in the background, even after you close the tab, and the outputs are kept. Use this for long training runs.
- Download the two `best.pt` files right away.

### Step 8: Evaluate and benchmark
```bash
python -m src.evaluate    --config configs/kaggle.yaml
python -m src.benchmark   --config configs/kaggle.yaml --half            # PyTorch
python -m src.export_onnx --config configs/kaggle.yaml
python -m src.benchmark   --config configs/kaggle.yaml --backend onnx    # ONNX
```
`benchmark.py` reads `gate_threshold_from_val` and `temperature` from `runs/eval.json` automatically, so run it after `evaluate.py`. To serve the API with the same values, pass them as `GATE_THRESHOLD` and `TEMPERATURE` (the notebook also writes them into the config).

Finally, `python -m src.plots` draws the figures and `python -m src.report` writes the real numbers and figures into the README's Results section. Only outputs that exist are included, so the README never shows broken images.

### Step 9: Serve the API locally (optional)
```bash
pip install -r requirements.txt
CLS_CKPT=weights/classifier.pt DET_WEIGHTS=weights/detector.pt uvicorn app.server:app --port 8000
```
Open http://localhost:8000 for the web UI. You can upload an image, see the boxes drawn on it, read P(abnormal) and latency, and click **Explain** to get the Grad-CAM overlay. **This is the part to demo.** Swagger is at `/docs` if you want to show the raw API.

---

## 5. Code walkthrough

### 5.1 `src/data.py`: data preparation

**Image-level labels** (`prepare`)
```python
labels["abnormal"] = labels["image_id"].isin(set(abn["image_id"])).astype(int)
```
An image counts as abnormal if **at least one** radiologist drew a box.
- *Pro:* high recall, so fewer misses.
- *Con:* noisier labels, since sometimes only 1 of 3 radiologists saw something.
- *Alternative:* majority vote (≥ 2 of 3), which trades some recall for cleaner labels.

**Box fusion with WBF** (`fuse_boxes`)

Three radiologists can produce three boxes for the same finding. There are three ways to handle that:

| Option | Problem |
|---|---|
| Keep all 3 | The model learns that one finding has 3 boxes, and it predicts duplicates |
| NMS (keep 1, drop the rest) | Throws away two radiologists' input |
| **WBF (Weighted Boxes Fusion)** | Averages overlapping (IoU ≥ 0.4), same-class boxes into one consensus box |

The function works in four steps:
1. Group boxes by `rad_id`, since WBF treats each radiologist as a "model".
2. Normalize coordinates to 0–1 by dividing by the original image size. WBF requires this.
3. Call `weighted_boxes_fusion`.
4. Convert (x1, y1, x2, y2) to YOLO format (x_center, y_center, w, h).

**Splitting** (`split_ids`): an 80/10/10 train/val/test split, **stratified** on the abnormal label. A purely random split could leave 35% abnormal images in test and 27% in train, which would skew evaluation.

**YOLO export** (`write_yolo`)

YOLO expects this layout:
```
yolo/images/train/abc.png      yolo/labels/train/abc.txt
                               └─ "3 0.512 0.640 0.380 0.190"   (class xc yc w h)
```
Normal images get an empty label file, which makes them **background images**. Only 10% of normal images are included (`normal_bg_frac`):
- With no background images, YOLO never learns what "nothing" looks like, and it produces many false positives.
- Including all ~10k normal images would make training slow and very imbalanced. Stage 1 already handles filtering normals.

### 5.2 `src/dataset.py`: loading images for the ResNet

```python
Image.open(path).convert("L").convert("RGB")
```
X-rays are grayscale (one channel), but ImageNet-pretrained ResNets expect three. This line copies the gray channel into three identical channels.

**Augmentation**
- Used: small rotation (±7°), 5% shift, 0.9–1.1 zoom, and brightness/contrast jitter. These mimic patient positioning and scanner differences.
- **Not used: horizontal flips.** The heart sits on the left, so a flipped X-ray is not a realistic sample. Classes like Cardiomegaly and Aortic enlargement depend on side.

**Normalization** uses ImageNet mean/std, because the backbone was pretrained on that distribution.

### 5.3 `src/models.py`
```python
m.fc = nn.Linear(m.fc.in_features, 1)
```
This replaces the 1000-class ImageNet head with a single logit. A sigmoid on that logit gives P(abnormal).

### 5.4 `src/train_classifier.py`

| Piece | Purpose |
|---|---|
| `BCEWithLogitsLoss(pos_weight=...)` | Binary cross-entropy. `pos_weight = n_neg / n_pos ≈ 2.4`, so errors on abnormal images cost ~2.4× more, which offsets the imbalance |
| `AdamW`, lr 3e-4 | Standard fine-tuning optimizer |
| `CosineAnnealingLR` | Smooth learning-rate decay |
| `autocast` + `GradScaler` | Mixed precision: roughly 2× faster with less VRAM |
| Checkpoint on **val AUC** | AUC is threshold-free, so it is a fair way to compare epochs |

### 5.5 `src/train_detector.py`
Ultralytics does most of the work. The settings that matter:
- `weights: yolov8s.pt`: the small model, pretrained on COCO.
- `imgsz: 1024`: small findings such as nodules can vanish at 640 px.
- `fliplr=0.0`: no horizontal flips, for the same reason as the classifier.

### 5.6 `src/metrics.py`

**mAP@0.4** (`mean_ap`) is computed per class:
1. Sort predictions by confidence, highest first.
2. For each prediction, mark it TP if it matches an unmatched ground-truth box with IoU ≥ 0.4. Otherwise mark it FP.
3. Build the precision–recall curve and take the area under it (AP).
4. Average AP over the 14 classes to get mAP.

Why 0.4 instead of 0.5? Radiologists' boxes already disagree a lot, so the competition chose a looser match threshold.

**Threshold selection** (`threshold_for_sensitivity`): finds the **highest** threshold that still catches ≥ 95% of abnormal images. A higher threshold filters more images and saves more time, so this picks the best speed you can get within the safety constraint.

### 5.7 `src/evaluate.py`
- τ is chosen **on val** and applied **on test**. Choosing it on test would inflate the results (data leakage).
- YOLO runs at `conf=0.01` for mAP, because mAP needs the full precision–recall curve.
- It reports **two** mAPs, detector-only and two-stage. The gap between them is the cost of the gate.

### 5.8 `src/pipeline.py`
- `torch.cuda.synchronize()`: GPU calls are asynchronous. Without a sync, the timer stops early and latency looks better than it is.
- `half=True`: FP16 inference. It is faster on GPU with negligible accuracy loss.

### 5.9 `src/benchmark.py`
- Images are preloaded into RAM, so disk I/O is excluded from the timing.
- It runs a **warmup** first, because the first GPU calls are slow (kernel initialization and memory allocation).
- It reports **p95** alongside the mean. Production systems care about tail latency.

### 5.10 `app/server.py` and `app/static/index.html`
- Models load **once** at startup (`lifespan`), not on every request.
- Handlers are plain `def`, not `async def`. Inference is CPU/GPU-bound, so FastAPI runs it in a threadpool and the event loop stays free.
- Uploads are capped at 20 MB, and unreadable files return 400 instead of crashing the server.
- `/explain` returns a PNG, with the probability sent in an `X-Abnormal-Prob` header.
- The UI is a single static HTML file with no build step. It draws boxes on a `<canvas>` and shows a "not for clinical use" banner. For a medical demo aimed at US teams, that banner is expected.

### 5.11 `src/calibration.py`: temperature scaling
**The problem.** Fine-tuned CNNs are usually over-confident. A model might say 0.95 for images that are abnormal only 70% of the time. If anyone reads P(abnormal) as a real probability, that is misleading.

**The fix.** Learn a single number T on the validation set and use `p = sigmoid(logit / T)`:
- T > 1 softens over-confident predictions, and T < 1 sharpens under-confident ones.
- T is fit by minimizing negative log-likelihood on val (`fit_temperature`).
- Dividing by T is monotonic, so **the ranking and therefore AUC do not change**. Only the meaning of the number improves.

**Measuring it: ECE (Expected Calibration Error).** Bucket predictions by confidence (0–0.07, 0.07–0.13, ...). In each bucket, compare the average predicted probability with the actual abnormal rate. ECE is the weighted average gap, and lower is better. `evaluate.py` reports ECE before and after calibration.

**Order matters.** `evaluate.py` fits T first, then picks the gate threshold on the *calibrated* val probabilities, because the pipeline applies T at inference. Picking τ on raw probabilities and then applying T would shift the operating point.

### 5.12 `src/gradcam.py`: explainability
Grad-CAM answers the question: which regions pushed the abnormal score up?
1. Take the activations of the last conv block (`layer4`, a 2048 × 16 × 16 map for a 512 px input).
2. Backpropagate the logit to get the gradient for each channel.
3. Average each channel's gradient into a weight that measures how much that channel matters.
4. Take the weighted sum of the channels, apply ReLU to keep positive evidence, upsample to image size, and normalize to 0–1.

Two implementation details are worth knowing:
- The hook uses `tensor.register_hook` inside a forward hook, and only when gradients are on. Normal `no_grad` inference pays no cost.
- `register_full_backward_hook` was avoided, because it can break with ResNet's in-place ReLUs.

**Caveat:** a heatmap shows where the model looked, not that it reasoned correctly. A classic failure is a model attending to a hospital's text marker or to chest tubes rather than to pathology. Grad-CAM is exactly how you would catch that.

### 5.13 `src/export_onnx.py` and the ONNX backend
- **ONNX** is a framework-neutral model format. **onnxruntime** runs it with graph optimizations such as operator fusion and constant folding, and without Python-side PyTorch overhead.
- The classifier is exported with a dynamic batch dimension, and a sidecar `.json` file stores its input size.
- YOLO is exported through Ultralytics, which can then load the `.onnx` file directly.
- The pipeline chooses the backend from the file extension. `benchmark.py --backend onnx` lets you compare the two backends side by side.
- Trade-off: you lose Grad-CAM, which needs gradients, and FP16 through this path. On a server you would usually serve ONNX or TensorRT and keep a PyTorch copy for explanations.

### 5.13a Confidence intervals, subgroups and impact
- **Bootstrap CIs** (`metrics.bootstrap_ci`): resample test studies with replacement 1,000 times, recompute the metric, take the 2.5th and 97.5th percentiles. Resamples with one class are skipped.
- **Subgroups** (`src/subgroups.py`): `make_meta.py` reads `PatientSex` and `PatientAge` from DICOM headers; `evaluate.py` reports AUC, sensitivity and specificity by sex and age band (<40, 40–59, 60+). Groups under 30 studies or 10 abnormal studies are flagged as small.
- **Impact** (`src/impact.py`): GPU time = mean latency × volume on one GPU; studies cleared by the gate = volume × prevalence × (1 − sensitivity). Assumptions live in the `impact` config section and are written into `impact.json`.
- **Quick profile** (`configs/quick.yaml`): 30% stratified subset, fewer epochs, 640 px detector. Every output carries the profile name, so preliminary numbers are never mistaken for full results.
- **τ and T flow automatically:** `benchmark.py` reads them from `runs/eval.json`, so there is no manual copy step.

### 5.13b Error analysis and external validation
- **`src/error_analysis.py`** reads `eval_preds.npz` (which now stores image ids) and `boxes.csv`. For each finding class it counts abnormal test studies containing that finding and how many the gate cleared. It also writes `gate_false_negatives.csv`, lowest score first, for manual review with Grad-CAM.
- **`src/external_eval.py`** runs the gate on NIH ChestX-ray14 with the same weights, T and τ (no retuning). Frontal views only, stratified sample (`external.n_studies`). "Abnormal" = any NIH label; NIH labels are NLP-mined, so the caveats are written into the output and shown wherever the numbers appear.
- Why it matters: error analysis tells you what to fix next; external validation tells you whether the result travels. Both are standard questions from US healthcare ML teams.

### 5.14a `site/`: the GitHub Pages site
A static page (HTML, CSS and JavaScript, no build step) deployed by `.github/workflows/deploy-pages.yml`. Its structure and rules are written down first in `docs/SITE_SPEC.md`, and `tests/test_site.py` checks the page against that spec.

| Section | How it works |
|---|---|
| Playground | Three small models that run in the browser with simulated data: the gate threshold trade-off, WBF box fusion with live IoU, and temperature scaling. They explain the design; they are not model output. |
| Results | Loads `results.json`, written by `python -m src.report` from a real run. Shows an empty state until then. |
| Live demo | Calls an API address the visitor enters (default `http://localhost:8000`). The server allows the Pages origin through `CORS_ORIGINS`, and answers Chrome's private-network preflight so an HTTPS page can reach `localhost`. |

Preview locally with `make site`. To publish, set **Settings → Pages → Source** to **GitHub Actions** once; every push that touches `site/` or `docs/figures/` redeploys.

### 5.14 `src/plots.py`: figures
`train_classifier.py` now logs `history.csv` every epoch, and `evaluate.py` saves the raw test predictions to `eval_preds.npz`. `plots.py` turns those into four figures in `docs/figures/`:

| Figure | What to look for |
|---|---|
| `roc.png` | The red dot is the gate's operating point: high sensitivity, with whatever specificity that costs |
| `reliability.png` | Points should move onto the diagonal after temperature scaling |
| `per_class_ap.png` | Large, common findings (cardiomegaly, aortic enlargement) score high; small ones (nodule) score low |
| `training.png` | Loss falls while val AUC rises and then flattens. If AUC drops while loss keeps falling, the model is overfitting |

Commit these figures. They render in the README, and recruiters look at pictures before they read code.

### 5.15 Tests, lint and CI
| Test file | What it checks |
|---|---|
| `test_prepare.py` | WBF fusion, stratified split, YOLO export, on fake images |
| `test_metrics.py` | mAP edge cases (FP ranked above TP, duplicates, missed classes) and threshold choice |
| `test_calibration.py` | T is recovered on synthetic over-confident data, and ECE drops after scaling |
| `test_server.py` | API contract with a stub model: status codes, bad input, PNG output, UI served |
| `test_plots.py` | Every figure function writes a file |

`ruff` (configured in `pyproject.toml`) checks style and common bugs. The `Makefile` wraps every command (`make test`, `make lint`, `make all`).

None of these need a GPU or weights, so `.github/workflows/tests.yml` runs lint and tests on every push.

---

## 6. Reading the results

| Metric | Meaning | Notes |
|---|---|---|
| AUC | How well the model ranks abnormal images above normal ones. 0.5 is chance, 1.0 is perfect | |
| Temperature T | Calibration factor | T > 1 means the raw model was over-confident, which is typical |
| ECE | Gap between predicted probability and observed frequency | Should drop noticeably after calibration |
| Sensitivity | Share of abnormal images caught | Should be near 0.95, since τ targets that |
| Specificity | Share of normal images correctly filtered | Higher means more detector calls skipped |
| `frac_sent_to_detector` | Share of images that reach YOLO | Directly drives the latency savings |
| mAP@0.4 | Localization quality | **Expect a low number.** This is a hard task, and top competition entries scored only around 0.3 (from memory) |

Red flags and their usual causes:
- **mAP near 0:** almost certainly a coordinate problem. Recheck the meta file (Step 3).
- **High val AUC but much lower test AUC:** leakage, or a test set that is too small.
- **Two-stage mAP far below detector-only mAP:** the gate is dropping too many real findings. Raise `target_sensitivity`, for example to 0.98.

---

## 7. Common errors

| Error | Fix |
|---|---|
| `CUDA out of memory` | Lower `batch_size` / `batch`, or lower `img_size` |
| YOLO reports `no labels found` | Symlinks are failing. Set `copy_images: true` |
| `KeyError` reading the meta file | Column names differ from `dim0` / `dim1`. Rename them |
| `yolov8s.pt` won't download | Internet is off in the notebook |
| DataLoader hangs or worker errors | Set `num_workers: 2` or `0` |
| Session dies mid-training | Use Save & Run All (Commit), see Step 7 |

---

## 8. Design FAQ

Short answers to the questions people usually ask about this design.

**1. Why two stages?**
About 70% of images are normal, so a cheap classifier screening first saves compute. The risk is that the gate drops real findings. This is handled by tuning the threshold for a target sensitivity on validation, and by measuring mAP in both modes so the cost is visible.

**2. How did you handle class imbalance?**
`pos_weight` in the loss, a sensitivity-based threshold instead of 0.5, only a fraction of normal images as YOLO background, and evaluation with AUC and sensitivity rather than accuracy.

**3. Why not accuracy?**
A model that always predicts "normal" gets about 70% accuracy and is useless. In medicine, a false negative (a missed finding) costs far more than a false positive.

**4. How did you handle disagreement between radiologists?**
WBF is used to average overlapping boxes. NMS throws information away, and keeping every box teaches the model to predict duplicates. For image-level labels, the choice is between "any radiologist" and majority vote.

**5. Why no flip augmentation?**
Chest anatomy is asymmetric. The heart sits on the left, and some classes depend on which side a finding is on.

**6. How did you reduce latency?**
Gating, FP16, loading the models once, and an ONNX backend benchmarked against PyTorch. Next steps would be TensorRT and request batching.

**7. How do you measure latency correctly?**
Warm up first, call `cuda.synchronize`, exclude I/O, and report both p50 and p95.

**8. What would production need?**
- Monitoring for data drift, since different scanners and hospitals produce different images
- Probability calibration
- Radiologist review (human in the loop)
- Audit logging
- Grad-CAM to explain why an image was flagged

**9. Is P(abnormal) a real probability?**
Not out of the box, because fine-tuned CNNs are over-confident. Temperature scaling is fit on validation, which leaves AUC unchanged, and ECE is reported before and after. The gate threshold is chosen on the calibrated scale so the operating point stays consistent at inference.

**10. How would a clinician know why an image was flagged?**
Grad-CAM on the gate classifier gives a heatmap of the regions that raised the score. It is presented as a debugging and trust aid, not as an explanation of disease. It is also useful for catching shortcut learning, such as a model attending to text markers or tubes.

**11. How did you test the service?**
With API contract tests that swap in a stub model, so they cover status codes, input validation, and response shapes without weights or a GPU. They run in GitHub Actions on every push. The data prep, metrics, and calibration code are unit-tested on synthetic data.

**12. What are the limitations?**
- Labels are noisy because radiologists disagree.
- The data comes from Vietnamese hospitals only, so the model may not generalize to US populations or scanners. Expect this question from a US team.
- AP on small findings such as nodules is low.
- The gate is a single point of failure: if it is wrong, the whole system is wrong.

See `docs/MODEL_CARD.md` for the full write-up.

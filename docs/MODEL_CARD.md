# Model Card: Chest X-ray Two-Stage Triage

## Overview
| | |
|---|---|
| Models | ResNet-50 binary gate (normal vs. abnormal) + YOLOv8s detector (14 finding classes) |
| Training data | VinDr-CXR (VinBigData), 15,000 labeled posteroanterior chest X-rays |
| Output | P(abnormal), and bounding boxes with class labels for flagged images |
| Status | **Research demo. Not a medical device. Not cleared or approved for clinical use.** |

## Intended use
This model is for education and research only. It demonstrates a compute-saving triage design, along with calibration and explainability techniques.

It is **not** intended for diagnosis, screening, or any clinical decision. Its outputs have not been validated against clinical outcomes.

## Data
- **Source:** VinDr-CXR, collected at Vietnamese hospitals. Each training image was labeled by 3 radiologists drawn from a pool of 17.
- **Labels:** 14 finding classes plus "No finding". Image-level abnormal = at least one radiologist marked a finding. Boxes were fused across radiologists with Weighted Boxes Fusion.
- **Splits:** stratified 80/10/10 train/val/test at the image level, with a fixed seed.
- **Class balance:** about 70% of images are "No finding".

## Evaluation
Fill these in from `runs/eval.json`, `runs/gate_misses.json`, `runs/external_nih.json`, `runs/benchmark_*.json` and `runs/impact.json`. The README Results section (`python -m src.report`) shows the same numbers automatically. State the run profile (quick or full) next to any number.

| Metric | Value |
|---|---|
| Gate test AUC (95% CI) | |
| Gate sensitivity / specificity at τ (target sensitivity 0.95, chosen on val), with 95% CIs | |
| ECE before → after temperature scaling | |
| Gate AUC, sensitivity, specificity by sex and age band (small groups flagged) | |
| Findings most often cleared by the gate (miss rate by class) | |
| External: NIH ChestX-ray14 AUC, sensitivity, specificity at the same τ (95% CI) | |
| Detector mAP@0.4, detector only | |
| Detector mAP@0.4, two-stage | |
| Mean latency, detector only → two-stage (GPU, FP16) | |
| Mean latency, PyTorch → ONNX | |

## Limitations
- **Population shift.** All training data comes from Vietnamese hospitals. The NIH ChestX-ray14 check measures transfer to one US source, but its labels are NLP-mined and defined differently, so it is a transfer check, not a clinical validation. Prospective validation on the target population would be required before any use.
- **Label noise.** Radiologists often disagree. Image-level labels use an "any radiologist" rule, which favors recall at the cost of noise.
- **Small findings.** Localization of small lesions such as nodules is typically weak.
- **Gate failure.** A false negative at the gate means the detector never runs, so that finding is lost entirely.
- **View coverage.** The model is trained on frontal views only. Lateral or portable AP images are out of distribution.

## Ethical considerations
- **Automation bias.** Clinicians may over-trust model outputs. Any real deployment would need radiologist review of every case (human in the loop).
- **Subgroup performance.** Performance by sex and age band is reported from DICOM header fields, which are sometimes missing; device and site subgroups are not available in the metadata.
- **Grad-CAM.** Heatmaps show where the classifier attended. They are not proof of correct reasoning and must not be read as a localization of disease.

## Responsible use
Do not upload real patient images with protected health information (PHI) to any deployment of this demo.

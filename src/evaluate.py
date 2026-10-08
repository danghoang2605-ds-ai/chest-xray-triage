"""Evaluate both stages on the held-out test split.

- Gate threshold is chosen on VAL for a target sensitivity, then applied to TEST.
- Detection mAP@0.4 is reported for detector-only vs. two-stage, so you can see
  what the gate costs in missed findings.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score
from torch.utils.data import DataLoader
from ultralytics import YOLO

from src.calibration import expected_calibration_error, fit_temperature, sigmoid, to_logits
from src.config import load_config
from src.data import CLASS_NAMES
from src.dataset import CXRDataset
from src.metrics import mean_ap, sens_spec, threshold_for_sensitivity
from src.models import load_classifier, predict_probs


def gt_boxes(boxes: pd.DataFrame, sizes: dict) -> dict:
    gts = {iid: [] for iid in sizes}
    for r in boxes[boxes["image_id"].isin(sizes)].itertuples(index=False):
        W, H = sizes[r.image_id]
        gts[r.image_id].append((int(r.class_id), [
            (r.xc - r.w / 2) * W, (r.yc - r.h / 2) * H,
            (r.xc + r.w / 2) * W, (r.yc + r.h / 2) * H,
        ]))
    return gts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--out", default="runs/eval.json")
    args = p.parse_args()
    cfg = load_config(args.config)
    c, dc, pc = cfg["classifier"], cfg["detector"], cfg["pipeline"]
    out_dir = Path(cfg["data"]["out_dir"])

    labels = pd.read_csv(out_dir / "labels.csv")
    boxes = pd.read_csv(out_dir / "boxes.csv")
    va, te = labels[labels.split == "val"], labels[labels.split == "test"]
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # ---- stage 1 ----
    model, img_size = load_classifier(c["out"], device)

    def probs(df):
        dl = DataLoader(CXRDataset(df, img_size, train=False), batch_size=32, num_workers=c["num_workers"])
        return predict_probs(model, dl, device)

    y_va, p_va = probs(va)
    y_te, p_te_raw = probs(te)

    # Calibrate on val with temperature scaling, then pick the gate threshold
    # on the calibrated val probabilities (the pipeline uses calibrated probs too).
    T = fit_temperature(to_logits(p_va), y_va)
    p_va = sigmoid(to_logits(p_va) / T)
    p_te = sigmoid(to_logits(p_te_raw) / T)
    thr = threshold_for_sensitivity(y_va, p_va, pc["target_sensitivity"])
    sens, spec = sens_spec(y_te, p_te >= thr)

    # ---- stage 2 ----
    det = YOLO(dc["best"])
    preds, sizes = [], {}
    for r in det.predict(te["path"].tolist(), imgsz=dc["img_size"], conf=pc["eval_conf"], stream=True,
                         verbose=False, device=0 if device == "cuda" else "cpu"):
        iid = Path(r.path).stem
        h, w = r.orig_shape
        sizes[iid] = (w, h)
        for b, cl, s in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.cls.cpu().numpy(), r.boxes.conf.cpu().numpy()):
            preds.append({"image_id": iid, "class_id": int(cl), "score": float(s), "box": b})

    gts = gt_boxes(boxes, sizes)
    map_det, ap_det = mean_ap(preds, gts, pc["map_iou"])
    prob_by_id = dict(zip(te["image_id"], p_te))
    gated = [q for q in preds if prob_by_id[q["image_id"]] >= thr]
    map_two, _ = mean_ap(gated, gts, pc["map_iou"])

    report = {
        "classifier": {
            "val_auc": float(roc_auc_score(y_va, p_va)),
            "test_auc": float(roc_auc_score(y_te, p_te)),
            "temperature": T,
            "test_ece_before_calibration": expected_calibration_error(p_te_raw, y_te),
            "test_ece_after_calibration": expected_calibration_error(p_te, y_te),
            "gate_threshold_from_val": thr,
            "test_sensitivity": sens,
            "test_specificity": spec,
            "test_frac_sent_to_detector": float(np.mean(p_te >= thr)),
        },
        "detector": {
            f"mAP@{pc['map_iou']}_detector_only": map_det,
            f"mAP@{pc['map_iou']}_two_stage": map_two,
            "per_class_AP_detector_only": {CLASS_NAMES[k]: round(v, 4) for k, v in ap_det.items()},
        },
        "n_test_images": int(len(te)),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    # raw arrays for src/plots.py
    np.savez(Path(args.out).with_name("eval_preds.npz"), y_test=y_te, p_test_raw=p_te_raw,
             p_test=p_te, threshold=thr)
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

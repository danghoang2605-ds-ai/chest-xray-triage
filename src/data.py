"""Prepare VinDr-CXR for the two-stage pipeline.

Outputs in data.out_dir:
  labels.csv  image_id, abnormal, path, split          -> classifier
  boxes.csv   image_id, class_id, xc, yc, w, h        -> fused GT boxes (normalized)
  yolo/       images/{split}, labels/{split}, dataset.yaml -> detector
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from ensemble_boxes import weighted_boxes_fusion
from PIL import Image
from sklearn.model_selection import train_test_split

from src.config import load_config

CLASS_NAMES = [
    "Aortic enlargement", "Atelectasis", "Calcification", "Cardiomegaly",
    "Consolidation", "ILD", "Infiltration", "Lung Opacity", "Nodule/Mass",
    "Other lesion", "Pleural effusion", "Pleural thickening", "Pneumothorax",
    "Pulmonary fibrosis",
]
NO_FINDING = 14


def image_dims(image_ids, image_dir, meta_csv=None) -> dict:
    """(width, height) of the coordinate system the raw boxes are in.

    VinDr boxes are in original DICOM pixels. If the PNGs were resized, pass a
    meta CSV with the original dims (dim0 = height, dim1 = width).
    """
    if meta_csv and Path(meta_csv).exists():
        meta = pd.read_csv(meta_csv).set_index("image_id")
        return {i: (int(meta.at[i, "dim1"]), int(meta.at[i, "dim0"])) for i in image_ids}
    dims = {}
    for i in image_ids:
        with Image.open(Path(image_dir) / f"{i}.png") as im:  # reads header only
            dims[i] = im.size
    return dims


def fuse_boxes(ann: pd.DataFrame, width: int, height: int, iou_thr: float = 0.4):
    """Fuse boxes from up to 3 radiologists with Weighted Boxes Fusion.

    Returns [(class_id, xc, yc, w, h)] normalized to [0, 1].
    A box drawn by a single radiologist is kept (WBF lowers its score, we ignore scores).
    """
    boxes_list, scores_list, labels_list = [], [], []
    for _, g in ann.groupby("rad_id"):
        b = g[["x_min", "y_min", "x_max", "y_max"]].to_numpy(dtype=float)
        b[:, [0, 2]] /= width
        b[:, [1, 3]] /= height
        boxes_list.append(np.clip(b, 0.0, 1.0))
        scores_list.append(np.ones(len(b)))
        labels_list.append(g["class_id"].to_numpy(dtype=int))
    boxes, _, labels = weighted_boxes_fusion(
        boxes_list, scores_list, labels_list, iou_thr=iou_thr, skip_box_thr=0.0
    )
    out = []
    for (x1, y1, x2, y2), c in zip(boxes, labels):
        w, h = x2 - x1, y2 - y1
        if w > 0 and h > 0:
            out.append((int(c), (x1 + x2) / 2, (y1 + y2) / 2, w, h))
    return out


def take_subset(labels: pd.DataFrame, frac: float, seed: int) -> pd.DataFrame:
    """Stratified subset for quick runs (frac = 1.0 keeps everything)."""
    if frac >= 1.0:
        return labels
    keep, _ = train_test_split(labels, train_size=frac, stratify=labels["abnormal"], random_state=seed)
    return keep.sort_values("image_id").reset_index(drop=True)


def add_demographics(labels: pd.DataFrame, meta_csv) -> pd.DataFrame:
    """Attach sex and age from the meta CSV when present, for subgroup analysis."""
    if not meta_csv or not Path(meta_csv).exists():
        return labels
    meta = pd.read_csv(meta_csv)
    cols = [c for c in ("sex", "age") if c in meta.columns]
    return labels.merge(meta[["image_id", *cols]], on="image_id", how="left") if cols else labels


def split_ids(labels: pd.DataFrame, val_frac: float, test_frac: float, seed: int) -> np.ndarray:
    """Stratified train/val/test split at image level."""
    train, rest = train_test_split(
        labels["image_id"], test_size=val_frac + test_frac,
        stratify=labels["abnormal"], random_state=seed,
    )
    rest_y = labels.set_index("image_id").loc[rest.values, "abnormal"]
    val, test = train_test_split(
        rest, test_size=test_frac / (val_frac + test_frac),
        stratify=rest_y, random_state=seed,
    )
    split = pd.Series("train", index=labels["image_id"].values)
    split.loc[val.values] = "val"
    split.loc[test.values] = "test"
    return split.values


def _place(src: Path, dst: Path, copy: bool) -> None:
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    if copy:
        shutil.copy2(src, dst)
        return
    try:
        os.symlink(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def write_yolo(labels, boxes, root: Path, normal_bg_frac: float, seed: int, copy: bool) -> None:
    rng = np.random.default_rng(seed)
    by_image = {iid: g for iid, g in boxes.groupby("image_id")}
    for split in ("train", "val", "test"):
        (root / "images" / split).mkdir(parents=True, exist_ok=True)
        (root / "labels" / split).mkdir(parents=True, exist_ok=True)

    for r in labels.itertuples(index=False):
        g = by_image.get(r.image_id)
        if g is None:  # normal image: keep a fraction as background (empty label file)
            if rng.random() >= normal_bg_frac:
                continue
            lines = []
        else:
            lines = [
                f"{int(c)} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}"
                for c, xc, yc, w, h in g[["class_id", "xc", "yc", "w", "h"]].itertuples(index=False)
            ]
        _place(Path(r.path).resolve(), root / "images" / r.split / f"{r.image_id}.png", copy)
        (root / "labels" / r.split / f"{r.image_id}.txt").write_text("\n".join(lines))

    spec = {
        "path": str(root.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": dict(enumerate(CLASS_NAMES)),
    }
    with open(root / "dataset.yaml", "w") as f:
        yaml.safe_dump(spec, f, sort_keys=False)


def prepare(cfg: dict):
    d = cfg["data"]
    out = Path(d["out_dir"])
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(d["raw_csv"])
    abn = df[df["class_id"] != NO_FINDING]

    # An image is abnormal if ANY radiologist marked a finding.
    # (Alternative: majority vote. Trade-off: recall vs. label noise.)
    labels = pd.DataFrame({"image_id": sorted(df["image_id"].unique())})
    labels["abnormal"] = labels["image_id"].isin(set(abn["image_id"])).astype(int)
    labels = take_subset(labels, d.get("subset_frac", 1.0), d["seed"])
    df, abn = df[df["image_id"].isin(labels["image_id"])], abn[abn["image_id"].isin(labels["image_id"])]
    labels = add_demographics(labels, d.get("meta_csv"))
    labels["path"] = [str(Path(d["image_dir"]) / f"{i}.png") for i in labels["image_id"]]
    labels["split"] = split_ids(labels, d["val_frac"], d["test_frac"], d["seed"])
    labels.to_csv(out / "labels.csv", index=False)

    dims = image_dims(sorted(abn["image_id"].unique()), d["image_dir"], d.get("meta_csv"))
    rows = []
    for iid, g in abn.groupby("image_id"):
        for c, xc, yc, w, h in fuse_boxes(g, *dims[iid], iou_thr=d["wbf_iou"]):
            rows.append((iid, c, xc, yc, w, h))
    boxes = pd.DataFrame(rows, columns=["image_id", "class_id", "xc", "yc", "w", "h"])
    boxes.to_csv(out / "boxes.csv", index=False)

    write_yolo(labels, boxes, out / "yolo", d["normal_bg_frac"], d["seed"], d.get("copy_images", False))

    print(f"images: {len(labels)} | abnormal: {labels['abnormal'].mean():.1%} | fused boxes: {len(boxes)}")
    print(labels.groupby("split")["abnormal"].agg(["count", "mean"]))
    return labels, boxes


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    prepare(load_config(p.parse_args().config))

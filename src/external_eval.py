"""External validation of the gate on NIH ChestX-ray14 (NIH Clinical Center, US).

python -m src.external_eval --config configs/default.yaml   (after evaluate)
-> runs/external_nih.json

The gate is applied exactly as deployed: same weights, temperature T and threshold τ
from runs/eval.json, no retuning on the new data. This answers "does it transfer to a
US hospital?" honestly, including when the answer is "less well".

Caveats written into the output:
- NIH labels were mined from radiology reports by NLP and are noisier than VinDr's.
- "Abnormal" means any of NIH's 14 labels; its label set differs from VinDr's.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from src.calibration import sigmoid, to_logits
from src.config import load_config
from src.metrics import bootstrap_ci, sens_spec
from src.subgroups import age_band, subgroup_table

CAVEATS = [
    "NIH ChestX-ray14 labels were mined from reports by NLP and are noisier than radiologist boxes.",
    "Abnormal = any of NIH's 14 labels; the label set differs from VinDr-CXR's.",
    "Gate weights, T and τ are reused unchanged from the VinDr-CXR validation split.",
]


def index_images(root) -> dict:
    """Map file name -> path for every PNG under root (NIH ships images in images_0xx/images/)."""
    return {p.name: str(p) for p in Path(root).rglob("*.png")}


def nih_table(csv_path, image_index: dict) -> pd.DataFrame:
    """Labels and demographics from Data_Entry_2017.csv, for images that exist on disk."""
    df = pd.read_csv(csv_path)
    df = df[df["Image Index"].isin(image_index)].copy()
    df["path"] = df["Image Index"].map(image_index)
    df["abnormal"] = (df["Finding Labels"].str.strip() != "No Finding").astype(int)
    df["sex"] = df["Patient Gender"].map({"M": "Male", "F": "Female"})
    df["age"] = pd.to_numeric(df["Patient Age"], errors="coerce")
    df.loc[df["age"] > 110, "age"] = np.nan  # a few records have impossible ages
    return df[["Image Index", "path", "abnormal", "sex", "age", "View Position"]]


def sample(df: pd.DataFrame, n: int, seed: int, views=("PA", "AP")) -> pd.DataFrame:
    """Frontal views only (the gate was trained on frontal images), stratified sample of n studies."""
    df = df[df["View Position"].isin(views)]
    if n and n < len(df):
        df, _ = train_test_split(df, train_size=n, stratify=df["abnormal"], random_state=seed)
    return df.reset_index(drop=True)


def main():
    # torch-dependent imports stay here so the data functions above import without a GPU stack
    import torch
    from torch.utils.data import DataLoader

    from src.dataset import CXRDataset
    from src.models import load_classifier, predict_probs

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--eval", default="runs/eval.json")
    ap.add_argument("--out", default="runs/external_nih.json")
    args = ap.parse_args()
    cfg = load_config(args.config)
    ext, c = cfg["external"], cfg["classifier"]
    if not ext.get("nih_csv") or not ext.get("nih_images"):
        raise SystemExit("Set external.nih_csv and external.nih_images in the config.")

    ev = json.loads(Path(args.eval).read_text())["classifier"]
    T, thr = ev["temperature"], ev["gate_threshold_from_val"]
    df = sample(nih_table(ext["nih_csv"], index_images(ext["nih_images"])), ext.get("n_studies", 3000),
                cfg["data"]["seed"])

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, img_size = load_classifier(c["out"], device)
    dl = DataLoader(CXRDataset(df, img_size, train=False), batch_size=32, num_workers=c["num_workers"])
    y, p_raw = predict_probs(model, dl, device)
    p = sigmoid(to_logits(p_raw) / T)
    sens, spec = sens_spec(y, p >= thr)

    result = {
        "dataset": "NIH ChestX-ray14 (frontal views)",
        "n_studies": int(len(df)),
        "prevalence": float(np.mean(y)),
        "temperature": T,
        "threshold": thr,
        "auc": float(roc_auc_score(y, p)),
        "auc_ci95": bootstrap_ci(y, p, roc_auc_score),
        "sensitivity": sens,
        "sensitivity_ci95": bootstrap_ci(y, p, lambda a, b: sens_spec(a, b >= thr)[0]),
        "specificity": spec,
        "specificity_ci95": bootstrap_ci(y, p, lambda a, b: sens_spec(a, b >= thr)[1]),
        "frac_sent_to_detector": float(np.mean(p >= thr)),
        "subgroups": {
            "sex": subgroup_table(y, p, thr, df["sex"]),
            "age": subgroup_table(y, p, thr, [age_band(a) for a in df["age"]]),
        },
        "caveats": CAVEATS,
    }
    Path(args.out).write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "subgroups"}, indent=2))


if __name__ == "__main__":
    main()

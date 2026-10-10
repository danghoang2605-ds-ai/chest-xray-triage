"""Where does the gate fail? Gate misses broken down by finding class.

python -m src.error_analysis --config configs/default.yaml   (after evaluate)
-> runs/gate_misses.json           miss rate per finding class on the test split
-> runs/gate_false_negatives.csv   abnormal test studies the gate cleared, lowest score first

A missed study is abnormal (any radiologist marked a finding) but scored below τ,
so the detector never reads it. Knowing which findings these are is the most
useful input for the next iteration (data, resolution, class-specific thresholds).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_config
from src.data import CLASS_NAMES


def gate_misses_by_class(image_ids, y, p, threshold: float, boxes: pd.DataFrame) -> list[dict]:
    """For each finding class: abnormal test studies that contain it, how many the gate cleared."""
    ids = np.asarray(image_ids).astype(str)
    y, p = np.asarray(y).astype(int), np.asarray(p, float)
    cleared = {i for i, yi, pi in zip(ids, y, p) if yi == 1 and pi < threshold}
    abnormal = {i for i, yi in zip(ids, y) if yi == 1}
    b = boxes[boxes["image_id"].astype(str).isin(abnormal)]
    rows = []
    for c, g in b.groupby("class_id"):
        studies = set(g["image_id"].astype(str))
        missed = len(studies & cleared)
        rows.append({"class_id": int(c), "finding": CLASS_NAMES[int(c)], "abnormal_studies": len(studies),
                     "missed_by_gate": missed, "miss_rate": missed / len(studies)})
    return sorted(rows, key=lambda r: (-r["miss_rate"], -r["abnormal_studies"]))


def false_negatives(image_ids, y, p, threshold: float, boxes: pd.DataFrame) -> pd.DataFrame:
    """Abnormal studies scored below τ, with their findings, lowest score first."""
    df = pd.DataFrame({"image_id": np.asarray(image_ids).astype(str), "y": y, "p_abnormal": p})
    fn = df[(df.y == 1) & (df.p_abnormal < threshold)].drop(columns="y")
    names = (boxes.assign(image_id=boxes["image_id"].astype(str),
                          finding=boxes["class_id"].map(lambda c: CLASS_NAMES[int(c)]))
             .groupby("image_id")["finding"].agg(lambda s: "; ".join(sorted(set(s)))))
    return fn.assign(findings=fn["image_id"].map(names).fillna("")).sort_values("p_abnormal")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--runs", default="runs")
    args = ap.parse_args()
    cfg = load_config(args.config)
    runs = Path(args.runs)
    d = np.load(runs / "eval_preds.npz")
    boxes = pd.read_csv(Path(cfg["data"]["out_dir"]) / "boxes.csv")
    thr = float(d["threshold"])

    rows = gate_misses_by_class(d["image_ids"], d["y_test"], d["p_test"], thr, boxes)
    (runs / "gate_misses.json").write_text(json.dumps({"threshold": thr, "by_class": rows}, indent=2))
    fn = false_negatives(d["image_ids"], d["y_test"], d["p_test"], thr, boxes)
    fn.to_csv(runs / "gate_false_negatives.csv", index=False)

    print(f"{len(fn)} abnormal test studies cleared by the gate (τ = {thr:.3f})")
    for r in rows:
        print(f"  {r['finding']:<20} {r['missed_by_gate']:>4}/{r['abnormal_studies']:<5} {r['miss_rate']:.1%}")


if __name__ == "__main__":
    main()

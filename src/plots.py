"""Figures for the README and interviews.

python -m src.plots   (after train_classifier and evaluate)
-> docs/figures/roc.png, reliability.png, per_class_ap.png, training.png
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import roc_auc_score, roc_curve  # noqa: E402

from src.calibration import expected_calibration_error  # noqa: E402
from src.config import load_config  # noqa: E402


def plot_roc(y, p, threshold, out: Path):
    fpr, tpr, thr = roc_curve(y, p)
    i = int(np.argmin(np.abs(thr - threshold)))
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(fpr, tpr, lw=2, label=f"AUC = {roc_auc_score(y, p):.3f}")
    ax.plot([0, 1], [0, 1], "--", color="gray", lw=1)
    ax.scatter([fpr[i]], [tpr[i]], color="red", zorder=3,
               label=f"gate τ = {threshold:.2f} (sens {tpr[i]:.2f}, spec {1 - fpr[i]:.2f})")
    ax.set(xlabel="False positive rate (1 − specificity)", ylabel="True positive rate (sensitivity)",
           title="Gate classifier ROC (test)")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def _reliability(ax, y, p, n_bins, label):
    bins = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(p, bins[1:-1]), 0, n_bins - 1)
    conf, acc = [], []
    for b in range(n_bins):
        m = idx == b
        if m.any():
            conf.append(p[m].mean())
            acc.append(y[m].mean())
    ece = expected_calibration_error(p, y, n_bins)
    ax.plot(conf, acc, "o-", label=f"{label} (ECE {ece:.3f})")


def plot_reliability(y, p_raw, p_cal, out: Path, n_bins: int = 15):
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "--", color="gray", lw=1, label="perfect calibration")
    _reliability(ax, y, p_raw, n_bins, "before")
    _reliability(ax, y, p_cal, n_bins, "after temperature scaling")
    ax.set(xlabel="Predicted P(abnormal)", ylabel="Observed abnormal rate", title="Reliability diagram (test)",
           xlim=(0, 1), ylim=(0, 1))
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_per_class_ap(ap: dict, out: Path):
    items = sorted(ap.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.barh([k for k, _ in items], [v for _, v in items])
    ax.set(xlabel="AP@0.4", title="Per-class AP, detector only (test)", xlim=(0, 1))
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_training(history: pd.DataFrame, out: Path):
    fig, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(history["epoch"], history["train_loss"], "o-", label="train loss")
    ax1.set(xlabel="epoch", ylabel="train loss")
    ax2 = ax1.twinx()
    ax2.plot(history["epoch"], history["val_auc"], "s-", color="tab:orange", label="val AUC")
    ax2.set_ylabel("val AUC")
    fig.legend(loc="lower center", ncol=2, fontsize=8)
    ax1.set_title("Gate classifier training")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runs", default="runs")
    p.add_argument("--out", default="docs/figures")
    p.add_argument("--config", default=None, help="locates history.csv next to the classifier checkpoint")
    args = p.parse_args()
    runs, out = Path(args.runs), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    preds = np.load(runs / "eval_preds.npz")
    y = preds["y_test"].astype(float)
    plot_roc(y, preds["p_test"], float(preds["threshold"]), out / "roc.png")
    plot_reliability(y, preds["p_test_raw"], preds["p_test"], out / "reliability.png")

    report = json.loads((runs / "eval.json").read_text())
    plot_per_class_ap(report["detector"]["per_class_AP_detector_only"], out / "per_class_ap.png")

    hist = (Path(load_config(args.config)["classifier"]["out"]).parent / "history.csv" if args.config
            else runs / "classifier" / "history.csv")
    if not hist.exists():  # e.g. the quick profile keeps checkpoints under runs/quick/
        hist = next(iter(sorted(runs.rglob("history.csv"))), hist)
    if hist.exists():
        plot_training(pd.read_csv(hist), out / "training.png")
    print(f"figures -> {out}")


if __name__ == "__main__":
    main()

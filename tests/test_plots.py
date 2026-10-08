import numpy as np
import pandas as pd

from src.plots import plot_per_class_ap, plot_reliability, plot_roc, plot_training


def test_plots_write_files(tmp_path):
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 500).astype(float)
    p = np.clip(y * 0.6 + rng.random(500) * 0.4, 0, 1)
    plot_roc(y, p, 0.5, tmp_path / "roc.png")
    plot_reliability(y, p, np.clip(p * 0.9 + 0.05, 0, 1), tmp_path / "rel.png")
    plot_per_class_ap({"Cardiomegaly": 0.7, "Nodule/Mass": 0.1}, tmp_path / "ap.png")
    plot_training(pd.DataFrame({"epoch": [1, 2], "train_loss": [0.6, 0.4], "val_auc": [0.8, 0.85]}),
                  tmp_path / "train.png")
    for f in ["roc.png", "rel.png", "ap.png", "train.png"]:
        assert (tmp_path / f).stat().st_size > 1000

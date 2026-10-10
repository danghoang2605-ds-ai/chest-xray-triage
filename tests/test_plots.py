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


def test_main_finds_history_for_quick_profile(tmp_path, monkeypatch):
    import json
    import sys

    from src import plots
    runs = tmp_path / "runs"
    (runs / "quick" / "classifier").mkdir(parents=True)
    pd.DataFrame({"epoch": [1, 2], "train_loss": [0.6, 0.4], "val_auc": [0.8, 0.85]}).to_csv(
        runs / "quick" / "classifier" / "history.csv", index=False)
    rng = np.random.default_rng(1)
    y = rng.integers(0, 2, 200)
    p = np.clip(y * 0.5 + rng.random(200) * 0.5, 0, 1)
    np.savez(runs / "eval_preds.npz", y_test=y, p_test=p, p_test_raw=p, threshold=0.5)
    (runs / "eval.json").write_text(json.dumps({"detector": {"per_class_AP_detector_only": {"Nodule/Mass": 0.1}}}))
    out = tmp_path / "figs"
    monkeypatch.setattr(sys, "argv", ["plots", "--runs", str(runs), "--out", str(out)])
    plots.main()
    assert (out / "training.png").exists() and (out / "roc.png").exists()

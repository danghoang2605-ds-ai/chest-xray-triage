"""Temperature scaling for the gate classifier, plus Expected Calibration Error.

A probability of 0.8 should mean "abnormal about 80% of the time". Fine-tuned
CNNs tend to be over-confident, so we fit one scalar T on validation logits:
p = sigmoid(z / T). T is monotonic, so ranking (AUC) does not change, only
how trustworthy the probabilities are.
"""
import numpy as np
from scipy.optimize import minimize_scalar


def to_logits(p, eps: float = 1e-7):
    p = np.clip(np.asarray(p, dtype=float), eps, 1 - eps)
    return np.log(p / (1 - p))


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


def _nll(T, z, y, eps=1e-7):
    p = np.clip(sigmoid(z / T), eps, 1 - eps)
    return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))


def fit_temperature(logits, y) -> float:
    z, y = np.asarray(logits, float), np.asarray(y, float)
    res = minimize_scalar(_nll, bounds=(0.05, 20.0), args=(z, y), method="bounded")
    return float(res.x)


def expected_calibration_error(probs, y, n_bins: int = 15) -> float:
    """Weighted mean |accuracy - confidence| over equal-width probability bins."""
    probs, y = np.asarray(probs, float), np.asarray(y, float)
    bins = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(probs, bins[1:-1]), 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        m = idx == b
        if m.any():
            ece += m.mean() * abs(y[m].mean() - probs[m].mean())
    return float(ece)

import numpy as np
import pytest

from src.calibration import expected_calibration_error, fit_temperature, sigmoid, to_logits


def test_logit_sigmoid_roundtrip():
    p = np.array([0.01, 0.3, 0.5, 0.9])
    assert sigmoid(to_logits(p)) == pytest.approx(p, abs=1e-6)


def test_fit_temperature_recovers_overconfidence():
    rng = np.random.default_rng(0)
    true_logits = rng.normal(0, 2, 20000)
    y = (rng.random(20000) < sigmoid(true_logits)).astype(float)
    overconfident = true_logits * 3          # model is 3x too sharp
    T = fit_temperature(overconfident, y)
    assert T == pytest.approx(3.0, rel=0.1)


def test_calibration_lowers_ece():
    rng = np.random.default_rng(1)
    z = rng.normal(0, 2, 20000)
    y = (rng.random(20000) < sigmoid(z)).astype(float)
    raw = sigmoid(z * 3)
    T = fit_temperature(to_logits(raw), y)
    calibrated = sigmoid(to_logits(raw) / T)
    assert expected_calibration_error(calibrated, y) < expected_calibration_error(raw, y) / 2


def test_ece_perfect_is_zero():
    assert expected_calibration_error([0.0, 0.0, 1.0, 1.0], [0, 0, 1, 1]) == pytest.approx(0.0)

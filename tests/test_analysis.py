import math

import numpy as np
import pytest
from sklearn.metrics import roc_auc_score

from src.impact import operational_impact
from src.metrics import bootstrap_ci
from src.subgroups import age_band, parse_age, subgroup_table


def test_bootstrap_ci_contains_estimate_and_shrinks_with_n():
    rng = np.random.default_rng(0)

    def make(n):
        y = rng.integers(0, 2, n)
        return y, np.clip(y * 0.4 + rng.random(n) * 0.6, 0, 1)

    y_small, p_small = make(200)
    y_big, p_big = make(4000)
    lo_s, hi_s = bootstrap_ci(y_small, p_small, roc_auc_score, n_boot=300)
    lo_b, hi_b = bootstrap_ci(y_big, p_big, roc_auc_score, n_boot=300)
    assert lo_s <= roc_auc_score(y_small, p_small) <= hi_s
    assert (hi_b - lo_b) < (hi_s - lo_s)


@pytest.mark.parametrize("raw,years", [
    ("045Y", 45), ("006M", 0.5), (62, 62), ("", math.nan), (None, math.nan), ("XXX", math.nan),
])
def test_parse_age(raw, years):
    got = parse_age(raw)
    assert (math.isnan(got) and math.isnan(years)) or got == pytest.approx(years)


def test_age_band():
    assert [age_band(a) for a in (25, 40, 59.9, 60, math.nan)] == ["<40", "40-59", "40-59", "60+", None]


def test_subgroup_table_counts_and_small_flag():
    y = [1, 0, 1, 0, 1, 0]
    p = [0.9, 0.1, 0.2, 0.8, 0.7, 0.3]
    rows = subgroup_table(y, p, 0.5, ["F", "F", "F", "M", "M", None])
    f, m = rows
    assert (f["group"], f["n"], f["n_abnormal"]) == ("F", 3, 2)
    assert f["sensitivity"] == pytest.approx(0.5) and f["specificity"] == pytest.approx(1.0)
    assert m["n"] == 2 and m["small_sample"]


def test_operational_impact_arithmetic():
    r = operational_impact(studies_per_day=3600, prevalence=0.3, sensitivity=0.95,
                           detector_only_ms=40, two_stage_ms=20, gpu_cost_per_hour=2.0)
    assert r["gpu_hours_per_day_detector_only"] == pytest.approx(0.04)
    assert r["gpu_hours_per_day_two_stage"] == pytest.approx(0.02)
    assert r["cost_saved_per_month"] == pytest.approx(0.02 * 30 * 2.0)
    assert r["throughput_gain"] == pytest.approx(2.0)
    assert r["missed_at_gate_per_day"] == pytest.approx(3600 * 0.3 * 0.05)
    assert r["missed_at_gate_per_1000_abnormal"] == pytest.approx(50)

"""Performance by patient subgroup (sex, age band).

US healthcare teams expect this: a model that works on average can still fail
for a group. Groups that are too small are flagged instead of over-interpreted.
"""
import math

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

AGE_BANDS = [(0, 40, "<40"), (40, 60, "40-59"), (60, 200, "60+")]
MIN_N, MIN_POS = 30, 10


def parse_age(value):
    """DICOM PatientAge is like '045Y'; return years as float, or NaN if unknown."""
    if value is None:
        return math.nan
    if isinstance(value, (int, float)):
        return float(value) if not (isinstance(value, float) and math.isnan(value)) else math.nan
    s = str(value).strip().upper()
    if not s:
        return math.nan
    unit = s[-1] if s[-1] in "DWMY" else "Y"
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return math.nan
    n = float(digits)
    return {"Y": n, "M": n / 12, "W": n / 52, "D": n / 365}[unit]


def age_band(age):
    if age is None or (isinstance(age, float) and math.isnan(age)):
        return None
    for lo, hi, name in AGE_BANDS:
        if lo <= age < hi:
            return name
    return None


def subgroup_table(y, p, threshold: float, groups) -> list[dict]:
    """One row per group: n, abnormal count, AUC, sensitivity and specificity at the threshold."""
    df = pd.DataFrame({"y": np.asarray(y).astype(int), "p": np.asarray(p, float), "g": list(groups)})
    df = df.dropna(subset=["g"])
    rows = []
    for g, d in df.groupby("g", sort=True):
        pos, neg = int(d.y.sum()), int((1 - d.y).sum())
        pred = d.p >= threshold
        rows.append({
            "group": str(g),
            "n": int(len(d)),
            "n_abnormal": pos,
            "auc": float(roc_auc_score(d.y, d.p)) if pos and neg else None,
            "sensitivity": float((pred & (d.y == 1)).sum() / pos) if pos else None,
            "specificity": float((~pred & (d.y == 0)).sum() / neg) if neg else None,
            "small_sample": bool(len(d) < MIN_N or pos < MIN_POS),
        })
    return rows

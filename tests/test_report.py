import json

from src.report import END, PENDING, START, build_section, build_site_json, update_readme


def _readme(tmp_path):
    r = tmp_path / "README.md"
    r.write_text(f"# Title\n\n## Results\n\n{START}\nOLD_CONTENT\n{END}\n\n## Next\n")
    return r


def test_pending_when_no_runs(tmp_path):
    section = build_section(tmp_path / "runs", tmp_path / "docs" / "figures", tmp_path)
    assert section == PENDING


def test_fills_numbers_and_existing_figures_only(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "eval.json").write_text(json.dumps({
        "classifier": {"test_auc": 0.9, "gate_threshold_from_val": 0.27, "test_sensitivity": 0.95,
                       "test_specificity": 0.6, "temperature": 1.8, "test_ece_before_calibration": 0.08,
                       "test_ece_after_calibration": 0.02, "test_frac_sent_to_detector": 0.55},
        "detector": {"mAP@0.4_detector_only": 0.25, "mAP@0.4_two_stage": 0.24},
        "n_test_images": 1500,
    }))
    (runs / "benchmark_torch.json").write_text(json.dumps({
        "half": True, "mean_latency_reduction": 0.3,
        "detector_only": {"mean_ms": 40.0, "p95_ms": 55.0},
        "two_stage": {"mean_ms": 28.0, "p95_ms": 50.0},
    }))
    figs = tmp_path / "docs" / "figures"
    figs.mkdir(parents=True)
    (figs / "roc.png").write_bytes(b"png")

    section = build_section(runs, figs, tmp_path)
    assert "| Gate test AUC | 0.900 |" in section
    assert "| Specificity at τ | 0.600 |" in section and "40.0 → 28.0 ms (30.0% lower)" in section
    assert "![ROC + gate operating point](docs/figures/roc.png)" in section
    assert "reliability.png" not in section  # missing figure is not linked

    readme = _readme(tmp_path)
    update_readme(readme, section)
    text = readme.read_text()
    assert "OLD_CONTENT" not in text and "## Next" in text and text.count(START) == 1


def test_site_json(tmp_path):
    assert build_site_json(tmp_path / "runs", tmp_path / "figs") is None
    figs = tmp_path / "figs"
    figs.mkdir()
    (figs / "reliability.png").write_bytes(b"png")
    data = build_site_json(tmp_path / "runs", figs)
    assert data["rows"] == [] and data["figures"] == [{"file": "figures/reliability.png", "title": "Calibration"}]


def test_ci_subgroups_impact_and_profile(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "eval.json").write_text(json.dumps({
        "run_profile": {"name": "quick", "note": "30% subset."},
        "classifier": {"test_auc": 0.9, "test_auc_ci95": [0.88, 0.92], "gate_threshold_from_val": 0.27,
                       "test_sensitivity": 0.95, "test_sensitivity_ci95": [0.93, 0.97], "test_specificity": 0.6,
                       "temperature": 1.8, "test_ece_before_calibration": 0.08, "test_ece_after_calibration": 0.02,
                       "test_frac_sent_to_detector": 0.55},
        "detector": {},
        "subgroups": {"sex": [{"group": "Female", "n": 20, "n_abnormal": 4, "auc": 0.8, "sensitivity": 1.0,
                               "specificity": 0.5, "small_sample": True}]},
        "n_test_images": 1500,
    }))
    (runs / "impact.json").write_text(json.dumps({
        "assumptions": {"studies_per_day": 1000, "gpu_cost_per_hour": 1.0, "prevalence": 0.3, "model": "simple"},
        "gpu_hours_per_day_detector_only": 0.011, "gpu_hours_per_day_two_stage": 0.008,  # 0.66 and 0.48 min
        "cost_saved_per_month": 12.0, "throughput_gain": 1.43, "missed_at_gate_per_1000_abnormal": 50,
    }))
    section = build_section(runs, tmp_path / "figs", tmp_path)
    assert "Run profile: quick" in section
    assert "0.900 (95% CI 0.880–0.920)" in section
    assert "| Female ⚠ small sample | 20 | 4 |" in section
    assert "Operational impact" in section and "1.43×" in section and "| 50 |" in section
    assert "0.7 min → 0.5 min" in section and "$12.00" in section
    data = build_site_json(runs, tmp_path / "figs")
    assert data["profile"]["name"] == "quick" and data["subgroups"]["sex"][0]["n"] == 20 and data["impact"]


def test_gate_misses_and_external(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "gate_misses.json").write_text(json.dumps({"threshold": 0.3, "by_class": [
        {"class_id": 8, "finding": "Nodule/Mass", "abnormal_studies": 40, "missed_by_gate": 6, "miss_rate": 0.15}]}))
    (runs / "external_nih.json").write_text(json.dumps({
        "n_studies": 3000, "prevalence": 0.46, "threshold": 0.27, "auc": 0.8, "auc_ci95": [0.78, 0.82],
        "sensitivity": 0.9, "sensitivity_ci95": [0.88, 0.92], "specificity": 0.4, "specificity_ci95": [0.38, 0.42],
        "frac_sent_to_detector": 0.7, "subgroups": {"sex": []}, "caveats": ["NLP-mined labels."]}))
    section = build_section(runs, tmp_path / "figs", tmp_path)
    assert "| Nodule/Mass | 40 | 6 | 15.0% |" in section
    assert "External validation: NIH ChestX-ray14" in section and "NLP-mined labels." in section
    assert "0.800 (95% CI 0.780–0.820)" in section
    data = build_site_json(runs, tmp_path / "figs")
    assert data["gate_misses"][0]["finding"] == "Nodule/Mass" and data["external"] and data["external_caveats"]

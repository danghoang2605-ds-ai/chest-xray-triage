"""Fill the README "Results" section and site/results.json from real run outputs.

python -m src.report            (after evaluate, benchmark, impact and plots)

Reads runs/eval.json, runs/benchmark_torch.json, runs/benchmark_onnx.json,
runs/impact.json, runs/gate_misses.json, runs/external_nih.json and
docs/figures/*.png. Anything missing is left out, so the
README and the site never show broken images or invented numbers.
"""
import argparse
import json
from pathlib import Path

START, END = "<!-- RESULTS:START -->", "<!-- RESULTS:END -->"
FIGURES = [
    ("roc", "ROC + gate operating point"),
    ("reliability", "Calibration"),
    ("per_class_ap", "Per-class AP"),
    ("training", "Gate training"),
]
PENDING = (
    "_No results yet. Run `notebooks/kaggle_run.ipynb` (or `make all`), then "
    "`python -m src.report` fills this section from `runs/` and `docs/figures/`._"
)


def _load(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def _f(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}"


def _dur(hours):
    return f"{hours * 60:.1f} min" if hours < 1 else f"{hours:.2f} h"


def _usd(x):
    return f"${x:.2f}" if x < 100 else f"${x:,.0f}"


def _ci(value, ci, nd=3):
    """'0.912 (95% CI 0.897–0.926)' when a CI exists, else just the value."""
    return _f(value, nd) + (f" (95% CI {ci[0]:.{nd}f}–{ci[1]:.{nd}f})" if ci else "")


def collect(runs: Path, fig_dir: Path) -> dict:
    """Everything real that exists, in one structure used by both README and site."""
    ev, bt = _load(runs / "eval.json"), _load(runs / "benchmark_torch.json")
    bo, im = _load(runs / "benchmark_onnx.json"), _load(runs / "impact.json")
    gm, ex = _load(runs / "gate_misses.json"), _load(runs / "external_nih.json")

    rows = []
    if ev:
        c, d = ev["classifier"], ev["detector"]
        map_det = next((v for k, v in d.items() if k.startswith("mAP@") and k.endswith("detector_only")), None)
        map_two = next((v for k, v in d.items() if k.startswith("mAP@") and k.endswith("two_stage")), None)
        rows += [
            ("Gate test AUC", _ci(c["test_auc"], c.get("test_auc_ci95"))),
            (f"Sensitivity at τ = {_f(c['gate_threshold_from_val'])}",
             _ci(c["test_sensitivity"], c.get("test_sensitivity_ci95"))),
            ("Specificity at τ", _ci(c["test_specificity"], c.get("test_specificity_ci95"))),
            (f"ECE before → after calibration (T = {_f(c['temperature'], 2)})",
             f"{_f(c['test_ece_before_calibration'])} → {_f(c['test_ece_after_calibration'])}"),
            ("Share of test studies sent to the detector", f"{c['test_frac_sent_to_detector']:.1%}"),
            ("mAP@0.4, detector only", _f(map_det)),
            ("mAP@0.4, two-stage", _f(map_two)),
        ]
    if bt:
        det, two = bt["detector_only"], bt["two_stage"]
        rows.append((f"Mean latency, detector only → two-stage ({'FP16' if bt.get('half') else 'FP32'}, PyTorch)",
                     f"{det['mean_ms']:.1f} → {two['mean_ms']:.1f} ms ({bt['mean_latency_reduction']:.1%} lower)"))
        rows.append(("p95 latency, detector only → two-stage", f"{det['p95_ms']:.1f} → {two['p95_ms']:.1f} ms"))
    if bt and bo:
        rows.append(("Two-stage mean latency, PyTorch → ONNX",
                     f"{bt['two_stage']['mean_ms']:.1f} → {bo['two_stage']['mean_ms']:.1f} ms"))

    impact = []
    if im:
        a = im["assumptions"]
        impact = [
            (f"GPU time per day at {a['studies_per_day']:,} studies/day, detector only → two-stage",
             f"{_dur(im['gpu_hours_per_day_detector_only'])} → {_dur(im['gpu_hours_per_day_two_stage'])}"),
            (f"GPU cost saved per month at ${a['gpu_cost_per_hour']:.2f}/GPU-hour", _usd(im["cost_saved_per_month"])),
            ("Throughput gain on one GPU", f"{im['throughput_gain']:.2f}×" if im["throughput_gain"] else "n/a"),
            ("Abnormal studies cleared by the gate, per 1,000 abnormal",
             f"{im['missed_at_gate_per_1000_abnormal']:.0f}"),
        ]

    external = []
    if ex:
        external = [
            ("Studies (frontal views), abnormal share", f"{ex['n_studies']:,}, {ex['prevalence']:.1%}"),
            ("Gate AUC", _ci(ex["auc"], ex.get("auc_ci95"))),
            (f"Sensitivity at τ = {_f(ex['threshold'])} (unchanged)",
             _ci(ex["sensitivity"], ex.get("sensitivity_ci95"))),
            ("Specificity at τ", _ci(ex["specificity"], ex.get("specificity_ci95"))),
            ("Share sent to the detector", f"{ex['frac_sent_to_detector']:.1%}"),
        ]

    figs = [(name, title) for name, title in FIGURES if (fig_dir / f"{name}.png").exists()]
    return {
        "profile": (ev or {}).get("run_profile"),
        "n_test": ev["n_test_images"] if ev else None,
        "rows": rows,
        "subgroups": (ev or {}).get("subgroups") or {},
        "impact": impact,
        "impact_assumptions": im["assumptions"] if im else None,
        "gate_misses": (gm or {}).get("by_class") or [],
        "external": external,
        "external_subgroups": (ex or {}).get("subgroups") or {},
        "external_caveats": (ex or {}).get("caveats") or [],
        "figures": figs,
    }


def _subgroup_md(subgroups: dict) -> list[str]:
    out = []
    for key, title in (("sex", "Sex"), ("age", "Age band")):
        rows = subgroups.get(key)
        if not rows:
            continue
        out += [f"\n**{title}**\n",
                "| Group | n | Abnormal | AUC | Sensitivity | Specificity |",
                "|---|---|---|---|---|---|"]
        for r in rows:
            flag = " ⚠ small sample" if r["small_sample"] else ""
            out.append(f"| {r['group']}{flag} | {r['n']} | {r['n_abnormal']} | {_f(r['auc'])} | "
                       f"{_f(r['sensitivity'])} | {_f(r['specificity'])} |")
    return out


def _has_results(data: dict) -> bool:
    return any(data[k] for k in ("rows", "figures", "gate_misses", "external", "impact"))


def build_section(runs: Path, fig_dir: Path, readme_dir: Path) -> str:
    data = collect(runs, fig_dir)
    parts = []
    if not _has_results(data):
        return PENDING
    prof = data["profile"]
    if prof and prof.get("name") != "full":
        parts.append(f"> **Run profile: {prof['name']}.** {prof.get('note', '')}\n")
    if data["rows"]:
        n = data["n_test"]
        parts.append(f"Held-out test split{f' ({n} studies)' if n else ''}. Thresholds and temperature were chosen "
                     "on validation only. Confidence intervals: 1,000-sample bootstrap over studies.\n")
        parts += ["| Metric | Value |", "|---|---|"] + [f"| {k} | {v} |" for k, v in data["rows"]]
    if data["subgroups"]:
        parts.append("\n#### Performance by subgroup (test split, at τ)")
        parts += _subgroup_md(data["subgroups"])
    if data["gate_misses"]:
        parts.append("\n#### Where the gate misses (test split)")
        parts.append("Abnormal studies the gate cleared, by finding class. "
                     "These are the studies the detector never read.\n")
        parts += ["| Finding | Abnormal studies | Missed by gate | Miss rate |", "|---|---|---|---|"]
        parts += [f"| {g['finding']} | {g['abnormal_studies']} | {g['missed_by_gate']} | {g['miss_rate']:.1%} |"
                  for g in data["gate_misses"]]
    if data["external"]:
        parts.append("\n#### External validation: NIH ChestX-ray14 (US)")
        parts.append("Gate applied unchanged (same weights, T and τ). Caveats: "
                     + " ".join(data["external_caveats"]) + "\n")
        parts += ["| Metric | Value |", "|---|---|"] + [f"| {k} | {v} |" for k, v in data["external"]]
        parts += _subgroup_md(data["external_subgroups"])
    if data["impact"]:
        a = data["impact_assumptions"]
        parts.append("\n#### Operational impact (estimate)")
        parts.append(f"Assumptions: {a['studies_per_day']:,} studies/day, ${a['gpu_cost_per_hour']:.2f} per GPU-hour, "
                     f"prevalence {a['prevalence']:.1%}. Model: {a['model']}. "
                     "Change them in `configs/*.yaml` (`impact`).\n")
        parts += ["| Quantity | Value |", "|---|---|"] + [f"| {k} | {v} |" for k, v in data["impact"]]
    if data["figures"]:
        rel = fig_dir.resolve().relative_to(readme_dir.resolve()).as_posix()
        figs = data["figures"]
        parts += ["", "| " + " | ".join(t for _, t in figs) + " |", "|" + "---|" * len(figs),
                  "| " + " | ".join(f"![{t}]({rel}/{n}.png)" for n, t in figs) + " |"]
    return "\n".join(parts)


def build_site_json(runs: Path, fig_dir: Path) -> dict | None:
    """Results for the Pages site; None when there is nothing real to show."""
    data = collect(runs, fig_dir)
    if not _has_results(data):
        return None
    return {
        "profile": data["profile"],
        "n_test_images": data["n_test"],
        "rows": [{"metric": k, "value": v} for k, v in data["rows"]],
        "subgroups": data["subgroups"],
        "impact": [{"metric": k, "value": v} for k, v in data["impact"]],
        "impact_assumptions": data["impact_assumptions"],
        "gate_misses": data["gate_misses"],
        "external": [{"metric": k, "value": v} for k, v in data["external"]],
        "external_subgroups": data["external_subgroups"],
        "external_caveats": data["external_caveats"],
        "figures": [{"file": f"figures/{name}.png", "title": title} for name, title in data["figures"]],
    }


def update_readme(readme: Path, section: str) -> None:
    text = readme.read_text()
    if START not in text or END not in text:
        raise SystemExit(f"Markers {START} / {END} not found in {readme}")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    readme.write_text(f"{head}{START}\n{section}\n{END}{tail}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runs", default="runs")
    p.add_argument("--figures", default="docs/figures")
    p.add_argument("--readme", default="README.md")
    p.add_argument("--site", default="site/results.json")
    args = p.parse_args()
    readme = Path(args.readme)
    section = build_section(Path(args.runs), Path(args.figures), readme.parent)
    update_readme(readme, section)
    print(section)

    data = build_site_json(Path(args.runs), Path(args.figures))
    if data is not None and Path(args.site).parent.exists():
        Path(args.site).write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"site results -> {args.site}")


if __name__ == "__main__":
    main()

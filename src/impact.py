"""Turn measured results into operational numbers a hospital or product team cares about.

python -m src.impact   (after evaluate and benchmark) -> runs/impact.json

The model is deliberately simple and every assumption is written into the output:
- studies are processed one at a time on one GPU, so GPU time = latency x volume;
- missed abnormal studies at the gate = volume x prevalence x (1 - sensitivity).
"""
import argparse
import json
from pathlib import Path

from src.config import load_config


def operational_impact(studies_per_day: float, prevalence: float, sensitivity: float,
                       detector_only_ms: float, two_stage_ms: float, gpu_cost_per_hour: float) -> dict:
    hours = lambda ms: studies_per_day * ms / 1000 / 3600  # noqa: E731
    det_h, two_h = hours(detector_only_ms), hours(two_stage_ms)
    return {
        "gpu_hours_per_day_detector_only": det_h,
        "gpu_hours_per_day_two_stage": two_h,
        "gpu_hours_saved_per_month": (det_h - two_h) * 30,
        "cost_saved_per_month": (det_h - two_h) * 30 * gpu_cost_per_hour,
        "throughput_gain": detector_only_ms / two_stage_ms if two_stage_ms else None,
        "abnormal_studies_per_day": studies_per_day * prevalence,
        "missed_at_gate_per_day": studies_per_day * prevalence * (1 - sensitivity),
        "missed_at_gate_per_1000_abnormal": 1000 * (1 - sensitivity),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--runs", default="runs")
    args = p.parse_args()
    cfg = load_config(args.config)["impact"]
    runs = Path(args.runs)
    ev = json.loads((runs / "eval.json").read_text())
    bt = json.loads((runs / "benchmark_torch.json").read_text())

    prevalence = cfg.get("prevalence") or ev["classifier"].get("test_prevalence")
    result = {
        "assumptions": {
            "studies_per_day": cfg["studies_per_day"],
            "gpu_cost_per_hour_usd": cfg["gpu_cost_per_hour"],
            "prevalence": prevalence,
            "sensitivity": ev["classifier"]["test_sensitivity"],
            "detector_only_mean_ms": bt["detector_only"]["mean_ms"],
            "two_stage_mean_ms": bt["two_stage"]["mean_ms"],
            "model": "one GPU, one study at a time; GPU time = latency x volume",
        },
        **operational_impact(cfg["studies_per_day"], prevalence, ev["classifier"]["test_sensitivity"],
                             bt["detector_only"]["mean_ms"], bt["two_stage"]["mean_ms"], cfg["gpu_cost_per_hour"]),
    }
    (runs / "impact.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

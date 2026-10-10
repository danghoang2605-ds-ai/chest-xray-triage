"""Latency: detector-only vs. two-stage, on a sample of test images.

The saving comes from skipping the detector on images the gate calls normal,
so it scales with the share of normal images in the traffic.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_config
from src.imaging import load_image
from src.pipeline import TwoStagePipeline


def summarize(ms):
    a = np.asarray(ms)
    return {"mean_ms": round(float(a.mean()), 2), "p50_ms": round(float(np.percentile(a, 50)), 2),
            "p95_ms": round(float(np.percentile(a, 95)), 2), "throughput_img_s": round(1000 / float(a.mean()), 2)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--half", action="store_true", help="FP16 on GPU (torch backend)")
    p.add_argument("--backend", choices=["torch", "onnx"], default="torch",
                   help="onnx uses the files written by src/export_onnx.py")
    p.add_argument("--out", default=None, help="default: runs/benchmark_<backend>.json")
    p.add_argument("--eval", default="runs/eval.json",
                   help="take τ and T from this file when it exists, instead of the config")
    args = p.parse_args()
    cfg = load_config(args.config)
    pc = cfg["pipeline"]

    labels = pd.read_csv(Path(cfg["data"]["out_dir"]) / "labels.csv")
    te = labels[labels.split == "test"]
    te = te.sample(min(args.n, len(te)), random_state=cfg["data"]["seed"])
    imgs = [load_image(path) for path in te["path"]]  # preload: exclude disk I/O

    if args.backend == "onnx":
        exp = Path(cfg["export"]["dir"])
        cls_path, det_path = exp / "classifier.onnx", exp / "detector.onnx"
    else:
        cls_path, det_path = cfg["classifier"]["out"], cfg["detector"]["best"]
    tau, temp = pc["gate_threshold"], pc.get("temperature", 1.0)
    if Path(args.eval).exists():
        ev = json.loads(Path(args.eval).read_text())["classifier"]
        tau, temp = ev["gate_threshold_from_val"], ev["temperature"]
        print(f"using τ = {tau:.3f} and T = {temp:.2f} from {args.eval}")
    pipe = TwoStagePipeline(cls_path, det_path, gate_threshold=tau,
                            det_conf=pc["det_conf"], det_imgsz=cfg["detector"]["img_size"],
                            temperature=temp, half=args.half)

    results = {"n_images": len(imgs), "abnormal_share": float(te["abnormal"].mean()),
               "backend": args.backend, "half": pipe.half}
    for mode in ("detector_only", "two_stage"):
        for img in imgs[: args.warmup]:
            pipe(img, mode)
        outs = [pipe(img, mode) for img in imgs]
        results[mode] = summarize([o["timings"]["total_ms"] for o in outs])
        results[mode]["frac_sent_to_detector"] = float(np.mean([o["flagged"] for o in outs]))

    results["mean_latency_reduction"] = round(
        1 - results["two_stage"]["mean_ms"] / results["detector_only"]["mean_ms"], 4)
    out = Path(args.out or f"runs/benchmark_{args.backend}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

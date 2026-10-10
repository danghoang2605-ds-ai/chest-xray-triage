"""End-to-end smoke test on synthetic data, CPU only, a few minutes.

python scripts/smoke_test.py            (needs torch, torchvision, ultralytics, onnx, onnxruntime)

Builds a tiny fake VinDr-style dataset (bright rectangles = findings, boxes from
three jittered "radiologists", DICOM-style sex/age) plus a fake NIH set, then runs
every stage of the real pipeline with tiny models: data, both trainings, evaluate,
error analysis, external validation, benchmark, ONNX export + benchmark, impact,
plots, report, and the API with Grad-CAM. It checks that each stage produces its
outputs. It says nothing about model quality.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RNG = np.random.default_rng(0)


def make_vindr(root: Path, n: int = 80, size: int = 128):
    img_dir = root / "png"
    img_dir.mkdir(parents=True)
    rows, meta = [], []
    for i in range(n):
        iid = f"img{i:03d}"
        im = Image.fromarray((RNG.normal(70, 12, (size, size))).clip(0, 255).astype(np.uint8))
        if i % 3 == 0:  # abnormal: a bright blob, boxed by 3 jittered radiologists
            cls = [3, 8][i % 2]
            x, y, w = int(RNG.integers(20, 70)), int(RNG.integers(20, 70)), int(RNG.integers(18, 36))
            ImageDraw.Draw(im).ellipse([x, y, x + w, y + w], fill=200)
            for r in ("R1", "R2", "R3"):
                j = RNG.integers(-2, 3, 4)
                rows.append((iid, "x", cls, r, x + j[0], y + j[1], x + w + j[2], y + w + j[3]))
        else:
            rows += [(iid, "No finding", 14, r, np.nan, np.nan, np.nan, np.nan) for r in ("R1", "R2", "R3")]
        im.save(img_dir / f"{iid}.png")
        meta.append((iid, size, size, "M" if i % 2 else "F", float(20 + (i * 7) % 60)))
    pd.DataFrame(rows, columns=["image_id", "class_name", "class_id", "rad_id", "x_min", "y_min", "x_max", "y_max"]
                 ).to_csv(root / "train.csv", index=False)
    pd.DataFrame(meta, columns=["image_id", "dim0", "dim1", "sex", "age"]).to_csv(root / "meta.csv", index=False)


def make_nih(root: Path, n: int = 40, size: int = 128):
    d = root / "nih" / "images_001" / "images"
    d.mkdir(parents=True)
    rows = []
    for i in range(n):
        name = f"{i:08d}_000.png"
        im = Image.fromarray((RNG.normal(70, 12, (size, size))).clip(0, 255).astype(np.uint8))
        if i % 2:
            ImageDraw.Draw(im).ellipse([40, 40, 70, 70], fill=200)
        im.save(d / name)
        rows.append({"Image Index": name, "Finding Labels": "Mass" if i % 2 else "No Finding",
                     "Patient Gender": "MF"[i % 2], "Patient Age": 30 + i, "View Position": "PA"})
    pd.DataFrame(rows).to_csv(root / "nih" / "Data_Entry_2017.csv", index=False)


def run(*args):
    print("\n$ python -m", " ".join(args), flush=True)
    subprocess.run([sys.executable, "-m", *args], cwd=ROOT, check=True)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cxr_smoke_"))
    runs = ROOT / "runs"
    backup = None
    if runs.exists():  # never clobber a real run
        backup = runs.with_name("runs_before_smoke")
        shutil.rmtree(backup, ignore_errors=True)
        runs.rename(backup)
    try:
        make_vindr(tmp)
        make_nih(tmp)
        cfg = yaml.safe_load((ROOT / "configs" / "default.yaml").read_text())
        cfg["profile"] = {"name": "smoke", "note": "Synthetic data. Pipeline check only."}
        cfg["data"].update(raw_csv=str(tmp / "train.csv"), image_dir=str(tmp / "png"), meta_csv=str(tmp / "meta.csv"),
                           out_dir=str(tmp / "processed"), val_frac=0.25, test_frac=0.25, normal_bg_frac=0.3,
                           copy_images=True)
        cfg["classifier"].update(arch="resnet18", pretrained=False, img_size=64, epochs=1, batch_size=8,
                                 num_workers=0, out=str(tmp / "cls" / "best.pt"))
        cfg["detector"].update(weights="yolov8n.yaml", img_size=128, epochs=1, batch=4, workers=0, plots=False,
                               project=str(tmp / "det"), name="smoke",
                               best=str(tmp / "det" / "smoke" / "weights" / "best.pt"))
        cfg["export"]["dir"] = str(tmp / "export")
        cfg["external"].update(nih_csv=str(tmp / "nih" / "Data_Entry_2017.csv"), nih_images=str(tmp / "nih"),
                               n_studies=30)
        conf = tmp / "smoke.yaml"
        conf.write_text(yaml.safe_dump(cfg, sort_keys=False))
        c = str(conf)

        run("src.data", "--config", c)
        run("src.train_classifier", "--config", c)
        run("src.train_detector", "--config", c)
        run("src.evaluate", "--config", c)
        run("src.error_analysis", "--config", c)
        run("src.external_eval", "--config", c)
        run("src.benchmark", "--config", c, "--n", "8", "--warmup", "2")
        run("src.export_onnx", "--config", c)
        run("src.benchmark", "--config", c, "--n", "8", "--warmup", "2", "--backend", "onnx")
        run("src.impact", "--config", c)
        run("src.plots", "--out", str(tmp / "figures"), "--config", c)
        readme = tmp / "README.md"
        readme.write_text("# t\n<!-- RESULTS:START -->\n<!-- RESULTS:END -->\n")
        run("src.report", "--figures", str(tmp / "figures"), "--readme", str(readme),
            "--site", str(tmp / "results.json"))

        expected = ["eval.json", "eval_preds.npz", "gate_misses.json", "gate_false_negatives.csv", "external_nih.json",
                    "benchmark_torch.json", "benchmark_onnx.json", "impact.json"]
        missing = [f for f in expected if not (runs / f).exists()]
        missing += [f"figures/{f}.png" for f in ("roc", "reliability", "per_class_ap", "training")
                    if not (tmp / "figures" / f"{f}.png").exists()]
        assert not missing, f"missing outputs: {missing}"
        section = readme.read_text()
        for needle in ("Gate test AUC", "Run profile: smoke", "External validation", "Operational impact"):
            assert needle in section, needle
        assert json.loads((tmp / "results.json").read_text())["rows"]

        # API with the real pipeline: predict + Grad-CAM
        os.environ.update(CLS_CKPT=cfg["classifier"]["out"], DET_WEIGHTS=cfg["detector"]["best"],
                          DET_IMGSZ="128", GATE_THRESHOLD="0.0")
        sys.path.insert(0, str(ROOT))
        from fastapi.testclient import TestClient

        from app.server import app
        img = next((tmp / "png").glob("*.png")).read_bytes()
        with TestClient(app) as client:
            r = client.post("/predict", files={"file": ("x.png", img, "image/png")})
            assert r.status_code == 200 and r.json()["flagged"], r.text
            r = client.post("/explain", files={"file": ("x.png", img, "image/png")})
            assert r.status_code == 200 and r.headers["content-type"] == "image/png", r.text
        print("\nSMOKE TEST PASSED: every stage ran and produced its outputs.")
    finally:
        shutil.rmtree(runs, ignore_errors=True)
        if backup is not None:
            backup.rename(runs)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()

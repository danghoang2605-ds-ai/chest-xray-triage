"""Export both stages to ONNX for faster, framework-light inference.

python -m src.export_onnx --config configs/default.yaml
-> runs/export/classifier.onnx (+ classifier.onnx.json with img_size)
-> runs/export/detector.onnx
"""
import argparse
import inspect
import json
import shutil
from pathlib import Path

import torch
from ultralytics import YOLO

from src.config import load_config
from src.models import load_classifier


def export_classifier(ckpt: str, out: Path, opset: int = 17) -> Path:
    model, img_size = load_classifier(ckpt, "cpu")
    dummy = torch.randn(1, 3, img_size, img_size)
    kwargs = dict(input_names=["input"], output_names=["logit"],
                  dynamic_axes={"input": {0: "batch"}, "logit": {0: "batch"}}, opset_version=opset)
    # Newer PyTorch defaults to the dynamo exporter, which needs the extra onnxscript package.
    if "dynamo" in inspect.signature(torch.onnx.export).parameters:
        kwargs["dynamo"] = False
    torch.onnx.export(model, dummy, str(out), **kwargs)
    Path(str(out) + ".json").write_text(json.dumps({"img_size": img_size}))
    return out


def export_detector(weights: str, out: Path, imgsz: int) -> Path:
    produced = YOLO(weights).export(format="onnx", imgsz=imgsz, dynamic=False, simplify=True)
    shutil.copy(produced, out)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    cfg = load_config(p.parse_args().config)
    out_dir = Path(cfg["export"]["dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    cls = export_classifier(cfg["classifier"]["out"], out_dir / "classifier.onnx")
    det = export_detector(cfg["detector"]["best"], out_dir / "detector.onnx", cfg["detector"]["img_size"])
    print(f"classifier -> {cls}\ndetector   -> {det}")


if __name__ == "__main__":
    main()

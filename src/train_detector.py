"""Stage 2: YOLOv8 lesion localization (14 classes)."""
import argparse
from pathlib import Path

from ultralytics import YOLO

from src.config import load_config


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    cfg = load_config(p.parse_args().config)
    d = cfg["detector"]

    model = YOLO(d["weights"])
    model.train(
        data=str(Path(cfg["data"]["out_dir"]) / "yolo" / "dataset.yaml"),
        imgsz=d["img_size"],
        epochs=d["epochs"],
        batch=d["batch"],
        project=d["project"],
        name=d["name"],
        fliplr=0.0,  # same reason as the classifier: no left-right flips on CXR
        seed=cfg["data"]["seed"],
        exist_ok=True,
    )
    print(f"weights -> {Path(d['project']) / d['name'] / 'weights' / 'best.pt'}")


if __name__ == "__main__":
    main()

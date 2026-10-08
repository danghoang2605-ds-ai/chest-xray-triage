import numpy as np
import pandas as pd
import pytest
import yaml
from PIL import Image

from src.data import CLASS_NAMES, prepare


@pytest.fixture
def fake_vindr(tmp_path):
    img_dir = tmp_path / "png"
    img_dir.mkdir()
    rows = []
    for i in range(20):
        iid = f"img{i:02d}"
        Image.fromarray(np.zeros((64, 64), np.uint8)).save(img_dir / f"{iid}.png")
        if i < 10:  # abnormal: two radiologists agree on a cardiomegaly box, a third says no finding
            rows += [(iid, "Cardiomegaly", 3, "R1", 10, 10, 30, 30),
                     (iid, "Cardiomegaly", 3, "R2", 12, 12, 32, 32),
                     (iid, "No finding", 14, "R3", np.nan, np.nan, np.nan, np.nan)]
        else:
            rows += [(iid, "No finding", 14, r, np.nan, np.nan, np.nan, np.nan) for r in ("R1", "R2", "R3")]
    csv = tmp_path / "train.csv"
    pd.DataFrame(rows, columns=["image_id", "class_name", "class_id", "rad_id",
                                "x_min", "y_min", "x_max", "y_max"]).to_csv(csv, index=False)
    cfg = {"data": {"raw_csv": str(csv), "image_dir": str(img_dir), "meta_csv": None,
                    "out_dir": str(tmp_path / "out"), "val_frac": 0.2, "test_frac": 0.2,
                    "wbf_iou": 0.4, "normal_bg_frac": 1.0, "copy_images": False, "seed": 0}}
    return cfg, tmp_path / "out"


def test_prepare(fake_vindr):
    cfg, out = fake_vindr
    labels, boxes = prepare(cfg)

    assert len(labels) == 20 and labels["abnormal"].sum() == 10
    assert labels["split"].value_counts().to_dict() == {"train": 12, "val": 4, "test": 4}
    # each split keeps the 50/50 class balance
    assert (labels.groupby("split")["abnormal"].mean() == 0.5).all()

    # WBF fuses the two radiologists' boxes into one averaged box
    assert len(boxes) == 10
    b = boxes.iloc[0]
    assert b.class_id == 3
    assert b.xc == pytest.approx(21 / 64) and b.w == pytest.approx(20 / 64)

    spec = yaml.safe_load(open(out / "yolo" / "dataset.yaml"))
    assert len(spec["names"]) == len(CLASS_NAMES) == 14
    label_files = list((out / "yolo" / "labels").rglob("*.txt"))
    assert len(label_files) == 20  # bg frac 1.0 -> all normals included as background
    assert sum(1 for f in label_files if f.read_text().strip()) == 10

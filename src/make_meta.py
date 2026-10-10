"""Build a meta CSV with original image dims (and patient sex/age) from DICOM headers.

Needed when your resized-PNG dataset does not ship one. Only headers are read
(stop_before_pixels), so this takes minutes, not hours.

python -m src.make_meta --dicom_dir /kaggle/input/vinbigdata-chest-xray-abnormalities-detection/train \
                        --out data/raw/train_meta.csv
"""
import argparse
from pathlib import Path

import pandas as pd
import pydicom
from tqdm import tqdm

from src.subgroups import parse_age


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dicom_dir", required=True)
    p.add_argument("--out", default="data/raw/train_meta.csv")
    args = p.parse_args()

    rows = []
    for f in tqdm(sorted(Path(args.dicom_dir).glob("*.dicom"))):
        ds = pydicom.dcmread(f, stop_before_pixels=True)
        sex = str(getattr(ds, "PatientSex", "") or "").strip().upper() or None
        rows.append((f.stem, int(ds.Rows), int(ds.Columns),  # Rows = height, Columns = width
                     sex if sex in {"M", "F"} else None, parse_age(getattr(ds, "PatientAge", None))))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["image_id", "dim0", "dim1", "sex", "age"]).to_csv(args.out, index=False)
    print(f"{len(rows)} images -> {args.out}")


if __name__ == "__main__":
    main()

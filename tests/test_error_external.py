import pandas as pd
import pytest
from PIL import Image

from src.error_analysis import false_negatives, gate_misses_by_class
from src.external_eval import index_images, nih_table, sample

BOXES = pd.DataFrame({
    "image_id": ["a", "a", "b", "c", "d"],
    "class_id": [3, 8, 8, 8, 3],          # 3 = Cardiomegaly, 8 = Nodule/Mass
    "xc": .5, "yc": .5, "w": .1, "h": .1,
})


def test_gate_misses_by_class():
    ids = ["a", "b", "c", "d", "n1"]
    y = [1, 1, 1, 1, 0]
    p = [0.9, 0.1, 0.2, 0.8, 0.05]      # b and c are missed at τ = 0.3
    rows = {r["finding"]: r for r in gate_misses_by_class(ids, y, p, 0.3, BOXES)}
    assert rows["Nodule/Mass"]["abnormal_studies"] == 3 and rows["Nodule/Mass"]["missed_by_gate"] == 2
    assert rows["Cardiomegaly"]["missed_by_gate"] == 0
    assert list(rows)[0] == "Nodule/Mass"   # sorted by miss rate


def test_false_negatives_lists_findings_lowest_score_first():
    fn = false_negatives(["a", "b", "c", "n1"], [1, 1, 1, 0], [0.9, 0.2, 0.1, 0.0], 0.3, BOXES)
    assert fn["image_id"].tolist() == ["c", "b"]
    assert fn["findings"].tolist() == ["Nodule/Mass", "Nodule/Mass"]


@pytest.fixture
def fake_nih(tmp_path):
    imgs = tmp_path / "images_001" / "images"
    imgs.mkdir(parents=True)
    rows = []
    for i in range(40):
        name = f"{i:08d}_000.png"
        Image.new("L", (8, 8)).save(imgs / name)
        rows.append({"Image Index": name, "Finding Labels": "No Finding" if i % 2 else "Effusion|Mass",
                     "Patient Gender": "M" if i % 3 else "F", "Patient Age": 150 if i == 0 else 30 + i,
                     "View Position": "PA" if i < 36 else "LL"})
    rows.append({"Image Index": "missing.png", "Finding Labels": "Mass", "Patient Gender": "M",
                 "Patient Age": 50, "View Position": "PA"})
    csv = tmp_path / "Data_Entry_2017.csv"
    pd.DataFrame(rows).to_csv(csv, index=False)
    return csv, tmp_path


def test_nih_table_and_sample(fake_nih):
    csv, root = fake_nih
    index = index_images(root)
    df = nih_table(csv, index)
    assert len(df) == 40                                    # image missing on disk is dropped
    assert df["abnormal"].sum() == 20 and pd.isna(df.loc[0, "age"])   # impossible age removed
    s = sample(df, 20, seed=0)
    assert len(s) == 20 and set(s["View Position"]) <= {"PA", "AP"}   # lateral views excluded
    assert s["abnormal"].sum() == 10                        # stratified

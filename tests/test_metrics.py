import pytest

from src.metrics import mean_ap, sens_spec, threshold_for_sensitivity


def test_perfect_predictions():
    gts = {"a": [(0, [0, 0, 10, 10])], "b": [(1, [5, 5, 20, 20])]}
    preds = [{"image_id": "a", "class_id": 0, "score": 0.9, "box": [0, 0, 10, 10]},
             {"image_id": "b", "class_id": 1, "score": 0.8, "box": [5, 5, 20, 20]}]
    m, _ = mean_ap(preds, gts)
    assert m == pytest.approx(1.0)


def test_higher_scored_false_positive_halves_ap():
    gts = {"a": [(0, [0, 0, 10, 10])], "n": []}
    preds = [{"image_id": "n", "class_id": 0, "score": 0.9, "box": [0, 0, 10, 10]},
             {"image_id": "a", "class_id": 0, "score": 0.8, "box": [0, 0, 10, 10]}]
    m, _ = mean_ap(preds, gts)
    assert m == pytest.approx(0.5)


def test_missed_class_counts_as_zero():
    gts = {"a": [(0, [0, 0, 10, 10]), (1, [20, 20, 30, 30])]}
    preds = [{"image_id": "a", "class_id": 0, "score": 0.9, "box": [0, 0, 10, 10]}]
    m, aps = mean_ap(preds, gts)
    assert aps == {0: 1.0, 1: 0.0} and m == pytest.approx(0.5)


def test_duplicate_detection_is_false_positive():
    gts = {"a": [(0, [0, 0, 10, 10])]}
    preds = [{"image_id": "a", "class_id": 0, "score": 0.9, "box": [0, 0, 10, 10]},
             {"image_id": "a", "class_id": 0, "score": 0.8, "box": [1, 1, 10, 10]}]
    _, aps = mean_ap(preds, gts)
    assert aps[0] == pytest.approx(1.0)  # TP first, the duplicate FP comes after full recall


def test_threshold_for_sensitivity():
    y, s = [0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]
    assert threshold_for_sensitivity(y, s, 1.0) == pytest.approx(0.35)
    assert threshold_for_sensitivity(y, s, 0.5) == pytest.approx(0.8)


def test_sens_spec():
    assert sens_spec([1, 1, 0, 0], [1, 0, 0, 1]) == (0.5, 0.5)

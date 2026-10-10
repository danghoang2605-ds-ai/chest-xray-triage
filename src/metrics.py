import numpy as np
from sklearn.metrics import roc_curve


def box_iou(box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    """IoU of one xyxy box against N xyxy boxes."""
    x1 = np.maximum(box[0], boxes[:, 0])
    y1 = np.maximum(box[1], boxes[:, 1])
    x2 = np.minimum(box[2], boxes[:, 2])
    y2 = np.minimum(box[3], boxes[:, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area = (box[2] - box[0]) * (box[3] - box[1])
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    return inter / np.maximum(area + areas - inter, 1e-9)


def _ap(tp, n_gt: int) -> float:
    """VOC all-point interpolated AP from TP flags sorted by descending score."""
    tp = np.asarray(tp, dtype=float)
    ctp, cfp = np.cumsum(tp), np.cumsum(1 - tp)
    recall = ctp / n_gt
    precision = ctp / np.maximum(ctp + cfp, 1e-9)
    mrec = np.concatenate([[0.0], recall, [1.0]])
    mpre = np.concatenate([[0.0], precision, [0.0]])
    mpre = np.maximum.accumulate(mpre[::-1])[::-1]
    idx = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


def mean_ap(preds, gts, iou_thr: float = 0.4, num_classes: int = 14):
    """preds: [{image_id, class_id, score, box(xyxy)}]; gts: {image_id: [(class_id, box)]}.

    Images with no GT still count: predictions on them are false positives.
    Returns (mAP over classes that have GT, {class_id: AP}).
    """
    aps = {}
    for c in range(num_classes):
        gt_c = {iid: np.array([b for cc, b in g if cc == c], dtype=float).reshape(-1, 4)
                for iid, g in gts.items()}
        n_gt = sum(len(v) for v in gt_c.values())
        if n_gt == 0:
            continue
        p_c = sorted((p for p in preds if p["class_id"] == c), key=lambda p: -p["score"])
        matched = {iid: np.zeros(len(v), bool) for iid, v in gt_c.items()}
        tp = []
        for p in p_c:
            g = gt_c.get(p["image_id"])
            if g is None or len(g) == 0:
                tp.append(0)
                continue
            ious = box_iou(np.asarray(p["box"], float), g)
            j = int(ious.argmax())
            if ious[j] >= iou_thr and not matched[p["image_id"]][j]:
                matched[p["image_id"]][j] = True
                tp.append(1)
            else:
                tp.append(0)
        aps[c] = _ap(tp, n_gt) if tp else 0.0
    return (float(np.mean(list(aps.values()))) if aps else float("nan")), aps


def threshold_for_sensitivity(y_true, y_score, target: float = 0.95) -> float:
    """Highest threshold whose sensitivity (TPR) reaches the target."""
    _, tpr, thr = roc_curve(y_true, y_score, drop_intermediate=False)
    idx = int(np.argmax(tpr >= target))
    return float(min(thr[idx], 1.0))


def sens_spec(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true).astype(bool), np.asarray(y_pred).astype(bool)
    sens = (y_pred & y_true).sum() / max(y_true.sum(), 1)
    spec = (~y_pred & ~y_true).sum() / max((~y_true).sum(), 1)
    return float(sens), float(spec)


def bootstrap_ci(y_true, y_score, stat, n_boot: int = 1000, alpha: float = 0.05, seed: int = 0):
    """Percentile bootstrap CI for stat(y_true, y_score), resampling studies with replacement.

    Resamples that contain only one class are skipped (AUC and sensitivity need both).
    """
    y_true, y_score = np.asarray(y_true), np.asarray(y_score)
    rng = np.random.default_rng(seed)
    n, vals = len(y_true), []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        yt = y_true[idx]
        if yt.min() == yt.max():
            continue
        vals.append(stat(yt, y_score[idx]))
    lo, hi = np.percentile(vals, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)

import numpy as np
import torch
import torch.nn as nn
from torchvision import models

_ARCHS = {
    "resnet18": (models.resnet18, models.ResNet18_Weights.DEFAULT),
    "resnet50": (models.resnet50, models.ResNet50_Weights.DEFAULT),
}


def build_classifier(arch: str = "resnet50", pretrained: bool = True) -> nn.Module:
    fn, weights = _ARCHS[arch]
    m = fn(weights=weights if pretrained else None)
    m.fc = nn.Linear(m.fc.in_features, 1)  # single logit: P(abnormal)
    return m


def load_classifier(ckpt_path: str, device: str):
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=True)
    m = build_classifier(ckpt["arch"], pretrained=False)
    m.load_state_dict(ckpt["state_dict"])
    return m.to(device).eval(), ckpt["img_size"]


@torch.no_grad()
def predict_probs(model, loader, device):
    model.eval()
    ys, ps = [], []
    for x, y in loader:
        logits = model(x.to(device)).squeeze(1)
        # float64 so very confident logits are not rounded to exactly 0 or 1 (calibration needs them)
        ps.append(torch.sigmoid(logits.double()).cpu().numpy())
        ys.append(np.asarray(y))
    return np.concatenate(ys), np.concatenate(ps)

"""Grad-CAM for the gate classifier: which regions pushed P(abnormal) up."""
import numpy as np
import torch
import torch.nn.functional as F
from matplotlib import colormaps
from PIL import Image


class GradCAM:
    """Hooks a conv layer (ResNet layer4 by default) and builds a heatmap from
    the gradient-weighted activations of that layer."""

    def __init__(self, model: torch.nn.Module, target_layer: torch.nn.Module = None):
        self.model = model
        self.acts = None
        self.grads = None
        layer = target_layer if target_layer is not None else model.layer4
        layer.register_forward_hook(self._forward_hook)

    def _forward_hook(self, module, inputs, output):
        # Only capture when gradients are on, so normal no_grad inference is unaffected.
        if output.requires_grad:
            self.acts = output.detach()
            output.register_hook(self._save_grad)

    def _save_grad(self, grad):
        self.grads = grad.detach()

    def __call__(self, x: torch.Tensor):
        """x: (1, 3, H, W). Returns (heatmap HxW in [0, 1], logit)."""
        self.model.zero_grad(set_to_none=True)
        with torch.enable_grad():
            x = x.clone().requires_grad_(True)
            logit = self.model(x).squeeze()
            logit.backward()
        weights = self.grads.float().mean(dim=(2, 3), keepdim=True)          # importance per channel
        cam = F.relu((weights * self.acts.float()).sum(dim=1, keepdim=True))  # weighted sum of maps
        cam = F.interpolate(cam, size=x.shape[-2:], mode="bilinear", align_corners=False)[0, 0]
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)
        return cam.cpu().numpy(), float(logit.detach().float().item())


def overlay(img: Image.Image, cam: np.ndarray, alpha: float = 0.4) -> Image.Image:
    """Blend a [0, 1] heatmap over the image with the jet colormap."""
    base = img.convert("RGB")
    heat = Image.fromarray((cam * 255).astype(np.uint8)).resize(base.size, Image.BILINEAR)
    colored = colormaps["jet"](np.asarray(heat) / 255.0)[..., :3]
    colored = Image.fromarray((colored * 255).astype(np.uint8))
    return Image.blend(base, colored, alpha)

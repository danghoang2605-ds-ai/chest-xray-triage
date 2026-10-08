"""Two-stage inference: ResNet gate -> YOLOv8 only on images flagged abnormal.

Backends:
  torch: .pt checkpoints; supports FP16 and Grad-CAM
  onnx:  .onnx files from src/export_onnx.py, run with onnxruntime
The backend is picked from the classifier file extension.
"""
import json
import math
import time
from pathlib import Path

import torch
from PIL import Image
from ultralytics import YOLO

from src.data import CLASS_NAMES
from src.dataset import build_transform
from src.models import load_classifier


class TwoStagePipeline:
    def __init__(self, cls_ckpt, det_weights, gate_threshold=0.3, det_conf=0.15,
                 det_imgsz=1024, temperature=1.0, device=None, half=False):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.backend = "onnx" if str(cls_ckpt).endswith(".onnx") else "torch"
        self.half = half and self.device == "cuda" and self.backend == "torch"
        self.gate_threshold = gate_threshold
        self.det_conf = det_conf
        self.det_imgsz = det_imgsz
        self.temperature = temperature
        self._cam = None

        if self.backend == "torch":
            self.cls, img_size = load_classifier(cls_ckpt, self.device)
            if self.half:
                self.cls.half()
        else:
            import onnxruntime as ort
            img_size = json.loads(Path(str(cls_ckpt) + ".json").read_text())["img_size"]
            wanted = ["CUDAExecutionProvider", "CPUExecutionProvider"] if self.device == "cuda" \
                else ["CPUExecutionProvider"]
            providers = [p for p in wanted if p in ort.get_available_providers()]
            self.sess = ort.InferenceSession(str(cls_ckpt), providers=providers)

        self.tf = build_transform(img_size, train=False)
        self.det = YOLO(det_weights, task="detect")
        self.det_device = 0 if self.device == "cuda" else "cpu"

    # ---------- helpers ----------
    def _sync(self):
        if self.device == "cuda":
            torch.cuda.synchronize()

    def _logit(self, img: Image.Image) -> float:
        x = self.tf(img).unsqueeze(0)
        if self.backend == "onnx":
            return float(self.sess.run(None, {"input": x.numpy()})[0].reshape(-1)[0])
        x = x.to(self.device)
        if self.half:
            x = x.half()
        with torch.no_grad():
            return float(self.cls(x).float().item())

    def _prob(self, logit: float) -> float:
        # temperature scaling (see src/calibration.py)
        return 1.0 / (1.0 + math.exp(-logit / self.temperature))

    # ---------- public API ----------
    def abnormal_prob(self, img: Image.Image) -> float:
        return self._prob(self._logit(img))

    def detect(self, img: Image.Image):
        r = self.det.predict(img, imgsz=self.det_imgsz, conf=self.det_conf, half=self.half,
                             device=self.det_device, verbose=False)[0]
        return [
            {"class_id": int(c), "class_name": CLASS_NAMES[int(c)], "confidence": round(float(s), 4),
             "box_xyxy": [round(float(v), 1) for v in b]}
            for b, c, s in zip(r.boxes.xyxy.cpu().tolist(), r.boxes.cls.cpu().tolist(),
                               r.boxes.conf.cpu().tolist())
        ]

    def explain(self, img: Image.Image, alpha: float = 0.4):
        """Grad-CAM overlay for the gate decision. Torch backend only."""
        if self.backend != "torch":
            raise RuntimeError("Grad-CAM needs the PyTorch backend (.pt checkpoint).")
        from src.gradcam import GradCAM, overlay
        if self._cam is None:
            self._cam = GradCAM(self.cls)
        img = img.convert("L").convert("RGB")
        x = self.tf(img).unsqueeze(0).to(self.device)
        if self.half:
            x = x.half()
        cam, logit = self._cam(x)
        return overlay(img, cam, alpha), self._prob(logit)

    def __call__(self, img: Image.Image, mode: str = "two_stage") -> dict:
        img = img.convert("L").convert("RGB")
        timings, prob, flagged = {}, None, True
        t0 = time.perf_counter()
        if mode == "two_stage":
            prob = self.abnormal_prob(img)
            self._sync()
            timings["classifier_ms"] = (time.perf_counter() - t0) * 1000
            flagged = prob >= self.gate_threshold
        t1 = time.perf_counter()
        detections = self.detect(img) if flagged else []
        self._sync()
        timings["detector_ms"] = (time.perf_counter() - t1) * 1000 if flagged else 0.0
        timings["total_ms"] = (time.perf_counter() - t0) * 1000
        return {
            "mode": mode,
            "backend": self.backend,
            "abnormal_prob": None if prob is None else round(prob, 4),
            "gate_threshold": self.gate_threshold,
            "flagged": bool(flagged),
            "detections": detections,
            "image_size": list(img.size),
            "timings": {k: round(v, 2) for k, v in timings.items()},
        }

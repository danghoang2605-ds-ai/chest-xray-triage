"""API contract tests with a stub pipeline (no torch, no weights needed)."""
import io
import sys
import types

import pytest
from PIL import Image

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402


class StubPipeline:
    def __init__(self, *args, gate_threshold=0.3, **kwargs):
        self.backend = "torch"
        self.gate_threshold = gate_threshold

    def __call__(self, img, mode="two_stage"):
        return {"mode": mode, "backend": self.backend, "abnormal_prob": 0.9, "gate_threshold": self.gate_threshold,
                "flagged": True, "image_size": list(img.size), "timings": {"total_ms": 1.0},
                "detections": [{"class_id": 3, "class_name": "Cardiomegaly", "confidence": 0.8,
                                "box_xyxy": [1, 1, 10, 10]}]}

    def explain(self, img):
        return img.convert("RGB"), 0.9


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(sys.modules, "src.pipeline", types.SimpleNamespace(TwoStagePipeline=StubPipeline))
    monkeypatch.setenv("CLS_CKPT", "x.pt")
    monkeypatch.setenv("DET_WEIGHTS", "y.pt")
    monkeypatch.setenv("GATE_THRESHOLD", "0.25")
    sys.modules.pop("app.server", None)
    from app.server import app
    with TestClient(app) as c:
        yield c


def _png():
    buf = io.BytesIO()
    Image.new("L", (32, 32)).save(buf, format="PNG")
    return {"file": ("x.png", buf.getvalue(), "image/png")}


def test_health(client):
    r = client.get("/health").json()
    assert r["model_loaded"] and r["gate_threshold"] == 0.25


def test_predict(client):
    r = client.post("/predict?mode=two_stage", files=_png())
    assert r.status_code == 200
    body = r.json()
    assert body["flagged"] and body["detections"][0]["class_name"] == "Cardiomegaly"


def test_predict_rejects_bad_mode(client):
    assert client.post("/predict?mode=nope", files=_png()).status_code == 422


def test_predict_rejects_non_image(client):
    r = client.post("/predict", files={"file": ("x.txt", b"not an image", "text/plain")})
    assert r.status_code == 400


def test_explain_returns_png(client):
    r = client.post("/explain", files=_png())
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert r.headers["x-abnormal-prob"] == "0.9000"


def test_ui_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "Chest X-ray" in r.text

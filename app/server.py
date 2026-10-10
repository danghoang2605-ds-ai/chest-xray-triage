"""FastAPI inference service with a small web UI.

CLS_CKPT=runs/classifier/best.pt DET_WEIGHTS=runs/detector/yolov8s/weights/best.pt \
    uvicorn app.server:app --port 8000
Then open http://localhost:8000 (UI) or http://localhost:8000/docs (Swagger).

CLS_CKPT may also point to an .onnx file (see src/export_onnx.py); Grad-CAM
is then unavailable.
"""
import inspect
import io
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image

from src.pipeline import TwoStagePipeline

MAX_BYTES = 20 * 1024 * 1024
# The GitHub Pages site and local pages may call this API from the browser.
DEFAULT_ORIGINS = "https://danghoang2605-ds-ai.github.io,http://localhost:8000,http://127.0.0.1:8000"
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip()]
state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["pipe"] = TwoStagePipeline(
        os.environ["CLS_CKPT"], os.environ["DET_WEIGHTS"],
        gate_threshold=float(os.getenv("GATE_THRESHOLD", "0.3")),
        det_conf=float(os.getenv("DET_CONF", "0.15")),
        det_imgsz=int(os.getenv("DET_IMGSZ", "1024")),
        temperature=float(os.getenv("TEMPERATURE", "1.0")),
        half=os.getenv("HALF", "0") == "1",
    )
    yield
    state.clear()


app = FastAPI(title="Chest X-ray two-stage triage (research demo)", lifespan=lifespan)
_cors = dict(allow_origins=CORS_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["*"],
             expose_headers=["X-Abnormal-Prob"])
# Chrome asks before a public HTTPS page (GitHub Pages) calls a server on localhost.
_native_pna = "allow_private_network" in inspect.signature(CORSMiddleware.__init__).parameters
if _native_pna:
    _cors["allow_private_network"] = True
app.add_middleware(CORSMiddleware, **_cors)


if not _native_pna:  # older Starlette: add the header ourselves

    @app.middleware("http")
    async def private_network_access(request: Request, call_next):
        response = await call_next(request)
        if request.headers.get("access-control-request-private-network") == "true":
            response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response
app.mount("/ui", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="ui")


def _read_image(file: UploadFile) -> Image.Image:
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image larger than 20 MB")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        return img
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read image") from None


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/ui/")


@app.get("/health")
def health():
    pipe = state.get("pipe")
    return {"status": "ok", "model_loaded": pipe is not None,
            "backend": pipe.backend if pipe else None,
            "gate_threshold": pipe.gate_threshold if pipe else None}


# Sync handlers: FastAPI runs them in a threadpool, so inference doesn't block the event loop.
@app.post("/predict")
def predict(file: UploadFile = File(...),
            mode: str = Query("two_stage", pattern="^(two_stage|detector_only)$")):
    return state["pipe"](_read_image(file), mode=mode)


@app.post("/explain", responses={200: {"content": {"image/png": {}}}})
def explain(file: UploadFile = File(...)):
    """Grad-CAM heatmap (PNG) showing what drove the gate's decision."""
    try:
        heat, prob = state["pipe"].explain(_read_image(file))
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    buf = io.BytesIO()
    heat.save(buf, format="PNG")
    return Response(buf.getvalue(), media_type="image/png",
                    headers={"X-Abnormal-Prob": f"{prob:.4f}"})

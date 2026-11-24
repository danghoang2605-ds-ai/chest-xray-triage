FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# CPU-only torch keeps the image ~2 GB smaller; build with --build-arg TORCH_INDEX= for the default CUDA wheels.
ARG TORCH_INDEX=https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN if [ -n "$TORCH_INDEX" ]; then pip install --index-url "$TORCH_INDEX" torch torchvision; fi \
    && pip install -r requirements.txt

COPY src ./src
COPY app ./app
COPY configs ./configs

# Mount trained weights at /models (read-only is fine).
ENV CLS_CKPT=/models/classifier.pt \
    DET_WEIGHTS=/models/detector.pt \
    GATE_THRESHOLD=0.3 \
    TEMPERATURE=1.0 \
    YOLO_CONFIG_DIR=/tmp/ultralytics

RUN useradd --create-home --uid 1000 app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]

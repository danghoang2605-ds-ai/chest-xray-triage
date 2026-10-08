FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY app ./app
COPY configs ./configs
# mount trained weights at /models
ENV CLS_CKPT=/models/classifier.pt \
    DET_WEIGHTS=/models/detector.pt \
    GATE_THRESHOLD=0.3 \
    TEMPERATURE=1.0
EXPOSE 8000
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]

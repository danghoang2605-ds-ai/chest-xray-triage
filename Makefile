CONFIG ?= configs/default.yaml

.PHONY: help test lint data train-cls train-det eval bench export bench-onnx figures serve all

help:            ## list targets
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##/ -/'

test:            ## run unit + API tests (no GPU needed)
	python -m pytest -q

lint:            ## ruff static checks
	ruff check .

data:            ## build labels, fused boxes and the YOLO dataset
	python -m src.data --config $(CONFIG)

train-cls:       ## train the ResNet gate
	python -m src.train_classifier --config $(CONFIG)

train-det:       ## train YOLOv8
	python -m src.train_detector --config $(CONFIG)

eval:            ## AUC, calibration, mAP@0.4 -> runs/eval.json
	python -m src.evaluate --config $(CONFIG)

bench:           ## PyTorch latency benchmark
	python -m src.benchmark --config $(CONFIG) --half

export:          ## export both stages to ONNX
	python -m src.export_onnx --config $(CONFIG)

bench-onnx: export  ## ONNX latency benchmark
	python -m src.benchmark --config $(CONFIG) --backend onnx

figures:         ## ROC, reliability, per-class AP, training curves -> docs/figures
	python -m src.plots

serve:           ## run the API + web UI on :8000
	uvicorn app.server:app --port 8000

all: data train-cls train-det eval bench figures  ## full pipeline

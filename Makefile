CONFIG ?= configs/default.yaml

.PHONY: help test lint smoke site quick impact errors external data train-cls train-det eval bench export bench-onnx figures report serve all

help:            ## list targets
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##/ -/'

test:            ## run unit + API tests (no GPU needed)
	python -m pytest -q

lint:            ## ruff static checks
	ruff check .

smoke:           ## end-to-end run on synthetic data, CPU, a few minutes (needs torch + ultralytics)
	python scripts/smoke_test.py

site:            ## preview the GitHub Pages site on :8080
	python -m http.server 8080 -d site

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

errors:          ## gate misses by finding class -> runs/gate_misses.json
	python -m src.error_analysis --config $(CONFIG)

external:        ## gate on NIH ChestX-ray14 (set external.* in the config) -> runs/external_nih.json
	python -m src.external_eval --config $(CONFIG)

impact:          ## GPU hours, cost and missed studies -> runs/impact.json
	python -m src.impact --config $(CONFIG)

figures:         ## ROC, reliability, per-class AP, training curves -> docs/figures
	python -m src.plots --config $(CONFIG)

report:          ## fill the README Results section from runs/ and docs/figures/
	python -m src.report

serve:           ## run the API + web UI on :8000
	uvicorn app.server:app --port 8000

all: data train-cls train-det eval errors bench impact figures report  ## full pipeline (external is optional)

quick:           ## full pipeline on the quick profile (30% subset, fewer epochs)
	$(MAKE) all CONFIG=configs/quick.yaml

# Roadmap

The code, tests and site are in place. What is missing is a published run, so the plan starts there.

## Done (this pass)
- [x] API starts without weights: `/health` and the UI work, `/predict` and `/explain` return `503` (was a `KeyError` at startup)
- [x] Docker: CPU-only torch by default (much smaller image), non-root user, `HEALTHCHECK`, `.dockerignore`
- [x] CI: Python 3.10 and 3.12 matrix, pip cache, cancels superseded runs; Dependabot for actions and pip
- [x] Fixed stale README items (test count, "planned: subgroup analysis" already exists in `src/subgroups.py`)

## Phase 1: publish real numbers (highest value)
- [ ] Run `make quick` on Kaggle, then `make report`, so the Results table and site stop showing *Pending*
- [ ] Full-profile run with 3 seeds; report mean ± std next to the bootstrap CIs
- [ ] Commit figures to `docs/figures/` and let `deploy-pages.yml` publish them
- [ ] Publish weights as a GitHub Release asset so the live demo works with one download

## Phase 2: serving
- [ ] Batched inference endpoint (`POST /predict/batch`) and a throughput benchmark
- [ ] TensorRT / ONNX Runtime GPU engines, compared in `src/benchmark.py`
- [ ] Hosted demo (Hugging Face Spaces, CPU) with sample public images instead of uploads
- [ ] Request size and rate limits, structured JSON logs

## Phase 3: modelling
- [ ] Class-specific gate thresholds tuned for each finding's sensitivity
- [ ] Higher-resolution crops for small findings (nodules), measured on AP-small
- [ ] Prospective-style external check on a second public dataset (e.g. CheXpert / PadChest)

## Phase 4: polish
- [ ] Type hints throughout `src/` and `mypy` in CI
- [ ] Coverage report in CI
- [ ] Short demo video/GIF of the site and live demo

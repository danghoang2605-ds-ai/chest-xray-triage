# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Primary: ML/AI hiring teams in the US (recruiters screening portfolios and the engineers who interview).
They open the project page from a résumé or GitHub link and give it about two minutes. They need to
understand the problem, the method, how seriously it was evaluated, and see the mechanisms working by
playing with them. (Confirmed by the author, Nov 2026.)

## Product Purpose
A research and portfolio project: a two-stage chest X-ray screening pipeline. A calibrated ResNet-50
gate scores every study; a YOLOv8 detector localizes 14 finding types only on studies the gate flags.
Success for the page: a reviewer leaves knowing what the gate trades (compute vs. missed findings),
that the evaluation is honest, and that the author can build and ship the whole system.

## Positioning
The gate threshold is chosen for 95% sensitivity on validation and reported on an untouched test split,
with the cost of gating made explicit (two-stage mAP, gate misses by finding class, operational impact).
Most portfolio detectors report a single mAP; this one measures what skipping studies costs.

## Operating Context
Static GitHub Pages site (site/index.html) plus a FastAPI service with a web UI (app/) that a visitor
can run locally with trained weights. Training runs on a free Kaggle GPU (notebooks/kaggle_run.ipynb).
docs/SITE_SPEC.md is the page's contract; tests/test_site.py enforces it.

## Capabilities and Constraints
- Static HTML/CSS/JS in one file, no build step, no framework; only Google Fonts as an external request
  (plus the API address a visitor types for the live demo).
- No fabricated results: metric values appear only from results.json written by src/report.py.
  No trained run has been published yet, so results show as Pending.
- Interactive figures use simulated data and must say so next to the figure; the impact calculator's
  defaults are illustrative inputs.
- No images that imitate a radiograph; diagrams are schematic.
- Light and dark schemes; responsive from 360 px with no horizontal page scroll.

## Brand Commitments
- Name: "Chest X-ray Triage". Logo: site/logo.svg. Author: Dang Hoang, University of Georgia.
- Voice: plain, specific, no marketing slogans. "Not a medical device" notice is always present.

## Evidence on Hand
- Code, 53 tests, CI, Docker, model card (docs/MODEL_CARD.md), guide (docs/GUIDE.md).
- No trained weights or real metrics yet. Never invent them.

## Product Principles
1. Show the mechanism working before explaining it.
2. Honesty over polish: simulated is labelled, pending stays pending.
3. Every number on the page is traceable to code or to results.json.
4. A reviewer should never have to read a wall of bullets to find the point.

## Accessibility & Inclusion
WCAG AA contrast, visible keyboard focus, labelled controls, keyboard-operable figures,
prefers-reduced-motion respected.

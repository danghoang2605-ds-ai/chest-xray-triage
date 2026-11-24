---
version: 1
slug: "site-index-html"
primary_target: "site/index.html"
related_targets: []
---

Scope: site/index.html, the project page on GitHub Pages. Visitor mode: Read.
Audience: ML/AI hiring teams (recruiters and interviewing engineers), ~2 minutes.
Job: understand problem, method, evaluation rigor; play with the mechanisms.
Constraints: docs/SITE_SPEC.md and tests/test_site.py; no fabricated results; simulated labelled.
Memorable moment: studies stamped "Cleared" as the reader drags the gate threshold.
User feedback driving the redesign: too much text and bullets, monotone, weak first viewport,
interactive figures hard to understand.

## Direction contract

THESIS: The page is a requisition for one pipeline. Every section is a numbered field on the order, and the gate is the one checkbox that decides whether the detector test gets ordered. It refuses the centered academic project page and its wall of bullets.

OWN-WORLD: White form stock ruled in requisition blue ink; near-black ink for text. Specimen-tube cap colours from the clinical order of draw (lavender, gold, light blue, green, red, grey) code the sections and figures as round cap chips. Condensed grotesk for field labels and headings, a hyper-legible face for reading, its mono sibling for IDs and code. Fields are boxed with hairline form rules; results are empty boxes marked Pending.

STORY: The reader sees studies routed through the gate, learns the trade (compute vs. missed findings), sees how it was evaluated, and can run the live demo or reproduce it.

FIRST VIEWPORT: Left rail with cap-chip contents. Requisition header across the top: logo, title, author, status and link fields. Directly below, the triage strip: 40 simulated study tickets, a τ slider, live counts (cleared, sent to detector, missed abnormal) and a 95% sensitivity button; labelled Simulated data.

FORM: Lab requisition and specimen labelling; candidate 7 of 7 on the resonance list; seed:17800e0be020ade1.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

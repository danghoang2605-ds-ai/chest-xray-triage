# Site specification (the "contract" for site/index.html)

Written before the code. Every change to the site is checked against this file.

## Goal
- A technical reviewer (recruiter, engineer, interviewer) understands the problem, method, evaluation protocol and current status in under two minutes.
- Three mechanisms can be explored hands-on: the gate threshold trade-off, box fusion (WBF), and temperature scaling.
- A product reader can translate the system into operational terms (GPU hours, cost, missed studies) with their own inputs.

## Audience and tone
- Engineers and hiring teams in the US. English only.
- Written like a research project page: numbered sections, short bullets, figures with numbered captions, references.
- Plain, specific language. No marketing slogans.

## Structure (in order)
1. Title block: name, one-line description, author, links (code, model card, guide, notebook), status line.
2. Safety notice.
3. Summary: 4–5 bullets.
4. Problem.
5. Method: Fig. 1 pipeline diagram with real specs (input sizes, outputs), then one bullet list per stage.
6. Design decisions: table with decision, rationale, alternative.
7. Interactive figures: Fig. 2 gate threshold, Fig. 3 box fusion, Fig. 4 calibration, each labeled "Simulated data"; Fig. 5 operational impact calculator, labeled "Illustrative inputs". Each has a caption and "What it shows" and "Try" bullets.
8. Evaluation protocol: splits, metrics, selection rules, confidence intervals, subgroup analysis, error analysis, external validation, latency protocol, impact model.
9. Results: every metric that will be reported, shown as "Pending" until `results.json` exists. When results exist, also show the run profile (quick or full), subgroup tables with small-sample flags, gate misses by finding class, external validation with its caveats, and the impact table with its assumptions.
10. Live demo: connect to a running API.
11. Reproduce: commands.
12. Limitations.
13. References.

## Constraints
- Static HTML, CSS and JavaScript in one file. No build step, no framework.
- The only external requests are Google Fonts (with a full fallback stack), plus the optional API address a visitor types in.
- No fabricated results: numbers appear only from `results.json` written by `src/report.py` from a real run.
- No images that imitate a radiograph. Diagrams are schematic.
- Everything simulated is labeled as simulated, next to the figure. Calculator defaults are labeled as illustrative inputs.
- Results from a quick run are labeled with the run profile; they are never presented as full-run results.
- Accessibility: WCAG AA contrast, visible keyboard focus, labelled controls, keyboard-operable figures, reduced motion respected.
- Responsive from 360 px wide with no horizontal page scroll. Wide figures scroll inside their own frame.
- Light and dark color schemes.
- Body text lines under 80 characters.

## Failure conditions (any one fails the build)
- A metric value is shown that did not come from `results.json`.
- Results are shown without their run profile, or without confidence intervals when the run provides them.
- External validation is shown without its caveats (label source and definition differences).
- A JavaScript error in the console on load or during interaction.
- Horizontal page scroll at 360 px.
- An interactive control without a label, or a figure without a caption.
- A section from the structure list is missing.
- Marketing-style hero copy, decorative illustrations, or generic template chrome (all-caps eyebrows, arrow-suffixed buttons).

## Verification
- `tests/test_site.py`: sections present, captions present, simulated labels present, no hard-coded metric values, local references resolve.
- Manual pass in a headless browser at 1360 px and 390 px: screenshots, console errors, scroll width, interactions.

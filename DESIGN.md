---
name: Chest X-ray Triage
description: "A project page set as a lab requisition: white form stock ruled in requisition blue, pipeline stages coded by specimen-tube cap colours."
colors:
  form: "#1C3F94"
  form-soft: "#E6ECF8"
  cap-lav: "#6F4FA8"
  cap-blue: "#2F7FC1"
  cap-gold: "#A77D10"
  cap-green: "#24794C"
  cap-red: "#B3312F"
  cap-grey: "#6B7384"
  normal: "#8A93A6"
  ok: "#1D6E46"
  paper: "#FFFFFF"
  field: "#F4F6FB"
  ink: "#141A28"
  muted: "#4B5568"
  rule: "#CCD5EA"
  rule-strong: "#93A5D2"
  form-dark: "#8DADF5"
  form-soft-dark: "#1A2540"
  cap-lav-dark: "#B49BE6"
  cap-blue-dark: "#6FB4EC"
  cap-gold-dark: "#E3BD55"
  cap-green-dark: "#5CC690"
  cap-red-dark: "#F0807C"
  cap-grey-dark: "#9AA3B5"
  normal-dark: "#8E98AD"
  ok-dark: "#5CC690"
  paper-dark: "#0D1322"
  field-dark: "#141C30"
  ink-dark: "#E8EDF6"
  muted-dark: "#A9B4CA"
  rule-dark: "#263354"
  rule-strong-dark: "#3D5185"
typography:
  display:
    fontFamily: "Archivo, 'Arial Narrow', 'Roboto Condensed', system-ui, sans-serif"
    fontSize: "clamp(2.1rem, 4.4vw, 3.4rem)"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 78"
  headline:
    fontFamily: "Archivo, 'Arial Narrow', 'Roboto Condensed', system-ui, sans-serif"
    fontSize: "1.9rem"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.005em"
    fontVariation: "'wdth' 80"
  title:
    fontFamily: "Archivo, 'Arial Narrow', 'Roboto Condensed', system-ui, sans-serif"
    fontSize: "1.15rem"
    fontWeight: 700
    lineHeight: 1.3
    fontVariation: "'wdth' 90"
  figure-head:
    fontFamily: "Archivo, 'Arial Narrow', 'Roboto Condensed', system-ui, sans-serif"
    fontSize: "14.5px"
    fontWeight: 700
    lineHeight: 1.2
    fontVariation: "'wdth' 88"
  label:
    fontFamily: "Archivo, 'Arial Narrow', 'Roboto Condensed', system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.02em"
    fontVariation: "'wdth' 85"
  stamp:
    fontFamily: "Archivo, 'Arial Narrow', 'Roboto Condensed', system-ui, sans-serif"
    fontSize: "10px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "0.04em"
    fontVariation: "'wdth' 80"
  body:
    fontFamily: "'Atkinson Hyperlegible Next', 'Atkinson Hyperlegible', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.62
  body-sm:
    fontFamily: "'Atkinson Hyperlegible Next', 'Atkinson Hyperlegible', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
    fontSize: "15.5px"
    fontWeight: 400
    lineHeight: 1.62
  caption:
    fontFamily: "'Atkinson Hyperlegible Next', 'Atkinson Hyperlegible', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.62
  readout:
    fontFamily: "'Atkinson Hyperlegible Mono', ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace"
    fontSize: "1.15rem"
    fontWeight: 700
    lineHeight: 1.35
    fontFeature: "'tnum' 1"
  code:
    fontFamily: "'Atkinson Hyperlegible Mono', ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
  tag:
    fontFamily: "'Atkinson Hyperlegible Mono', ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.5
rounded:
  stamp: "2px"
  field: "3px"
  sheet: "4px"
  cap: "50%"
spacing:
  ticket-gap: "6px"
  cell: "12px"
  inset: "18px"
  figure-gap: "22px"
  column-gap: "24px"
  page-x: "48px"
  page-x-mobile: "16px"
  section: "56px"
components:
  button-primary:
    backgroundColor: "{colors.form}"
    textColor: "{colors.paper}"
    rounded: "{rounded.field}"
    padding: "8px 13px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.form}"
    rounded: "{rounded.field}"
    padding: "8px 13px"
  button-secondary-hover:
    backgroundColor: "{colors.form-soft}"
    textColor: "{colors.form}"
  input:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "8px 10px"
  cap-chip:
    backgroundColor: "{colors.cap-grey}"
    rounded: "{rounded.cap}"
    size: "14px"
  section-number:
    textColor: "{colors.form}"
    rounded: "{rounded.field}"
    padding: "4px 6px"
  field-label:
    textColor: "{colors.form}"
    typography: "{typography.label}"
  requisition-header:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sheet}"
    padding: "20px 22px 18px"
  figure-frame:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "{spacing.inset}"
  figure-head:
    backgroundColor: "{colors.form-soft}"
    textColor: "{colors.form}"
    typography: "{typography.figure-head}"
    padding: "10px 18px"
  guide:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ink}"
    typography: "{typography.caption}"
    rounded: "{rounded.field}"
    padding: "10px 12px"
  table-header:
    backgroundColor: "{colors.form-soft}"
    textColor: "{colors.form}"
    padding: "10px 14px"
  ticket:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.muted}"
    rounded: "{rounded.field}"
    padding: "6px 7px 5px"
  ticket-cleared:
    backgroundColor: "{colors.field}"
    textColor: "{colors.muted}"
  ticket-missed:
    textColor: "{colors.cap-red}"
  stamp:
    textColor: "{colors.muted}"
    typography: "{typography.stamp}"
    rounded: "{rounded.stamp}"
    padding: "1px 4px"
  stamp-missed:
    textColor: "{colors.cap-red}"
  pending:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.muted}"
    rounded: "{rounded.stamp}"
    padding: "1px 8px"
    width: "92px"
  tag:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    typography: "{typography.tag}"
    rounded: "{rounded.stamp}"
    padding: "0 6px"
  safety-notice:
    textColor: "{colors.ink}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.sheet}"
    padding: "12px 16px"
  contents-link:
    textColor: "{colors.muted}"
    rounded: "{rounded.sheet}"
    padding: "6px 8px"
  contents-link-hover:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ink}"
  contents-link-active:
    backgroundColor: "{colors.form-soft}"
    textColor: "{colors.ink}"
  step-counter:
    backgroundColor: "{colors.form}"
    textColor: "{colors.paper}"
    rounded: "{rounded.cap}"
    size: "28px"
---

# Design System: Chest X-ray Triage

## Overview

**Creative North Star: "The Requisition for One Pipeline"**

The page is filled in like a lab order. White form stock carries the content, and requisition-blue ink draws the form itself: the outer rules, the field labels, the section numbers, the focus ring, the threshold line. What is written into the form is near-black ink. Every section, figure and pipeline stage carries a round cap chip in a specimen-tube colour, and each colour stands for one stage of the pipeline, as the legend at the foot of the contents rail states.

Density is that of a form, not a brochure. Facts sit in labelled, ruled cells and tables; numbers sit in a monospace with tabular figures; results that do not exist yet are empty dashed boxes marked Pending. The surface is flat. Hierarchy comes from rule weight, a pale blue wash on header bars and the condensed heading face, never from shadow or gradient.

Motion is small and mechanical. A study ticket takes a rubber stamp, "Cleared" or "Missed", when the threshold passes it, and nothing moves on its own. This system describes `site/index.html`. The FastAPI demo UI at `app/static/index.html` is an older, separate surface and does not follow it. The logo (`site/logo.svg`) is a fixed brand asset with its own colours; it is placed, never restyled.

**Key Characteristics:**
- White form stock, requisition-blue rules and labels, near-black reading ink.
- Six specimen-cap colours used as a fixed categorical code, shown as round chips.
- Three type hands: condensed Archivo for the printed form, Atkinson Hyperlegible Next for reading, Atkinson Hyperlegible Mono for anything counted or copied.
- Facts in ruled fields and tables, never in bullet walls.
- Flat stock: hairline and 1.5px rules, tinted header bars, 2–4px corners.
- Complete light and dark schemes on the same token names.

## Colors

Paper and ink carry the reading, requisition blue draws the form, and six cap colours code the pipeline and nothing else.

### Primary
- **Requisition Blue** (`form`): the form's own ink. The 1.5px outline of the requisition header, the top rule of every field list and the footer, field and table labels, section-number boxes, the τ line and slider thumb, links, the 3px focus outline, text selection, the primary button fill. Plots read it under the alias `--accent`.
- **Header Wash** (`form-soft`): the pale blue band behind figure heads and table header rows, the active contents link, and tickets sent to the detector on narrow screens.

### Secondary
The cap code, taken from the clinical order of draw. Each colour has one meaning.
- **Lavender Cap** (`cap-lav`): the gate. Method section, Fig. 2, the gate stage in Fig. 1 and the stage table.
- **Light Blue Cap** (`cap-blue`): calibration. Fig. 4 and the calibrate stage. Plots also use it, as `--second`, for the Radiologist B series in Fig. 3.
- **Gold Cap** (`cap-gold`): the detector. Fig. 3, the detect stage, the Live demo section. The build also uses gold for the status-line dot and the quick-run banner border, a caution reading that sits beside its detector meaning.
- **Green Cap** (`cap-green`): evaluation. Evaluation protocol, Results, Fig. 5, and the Grad-CAM explanation row.
- **Red Cap** (`cap-red`): risk and abnormality. Problem and Limitations sections, abnormal-study chips, missed tickets and their stamp, the safety notice border, abnormal histogram bars and the Radiologist A box (as `--finding`), error messages (as `--warn`).
- **Grey Cap** (`cap-grey`): neutral. Summary, Design decisions, Interactive figures, Reproduce, References, normal-study chips. It is left out of the rail legend because it codes nothing.

### Tertiary
- **Normal-Study Grey** (`normal`): normal-study histogram bars and the raw (T = 1) calibration curve.
- **Connected Green** (`ok`): success messages in the live demo.

### Neutral
- **Form Stock** (`paper`): the page, figure frames, tickets, inputs, the pending box.
- **Field Tint** (`field`): code blocks, guide boxes, cleared tickets, plot backgrounds. Aliased in CSS as `--surface` and `--code-bg`.
- **Reading Ink** (`ink`): body text, headings, readout values.
- **Carbon Grey** (`muted`): captions, legends, contents links at rest, ticket IDs, the subtitle, the pending label.
- **Hairline** (`rule`): dividers between cells, table row lines, the rail's right edge, the bar inside each ticket.
- **Form Rule** (`rule-strong`): outlines of frames, the triage strip, tickets and tables; input strokes; the slider track; the pending box's dashed edge.

Every token has a `-dark` counterpart. The dark set applies under `prefers-color-scheme: dark` through `:root:not([data-theme="light"])` and is forced by `:root[data-theme="dark"]`. In dark, the paper becomes a deep blue-black, requisition blue lightens to periwinkle, and the caps lift to pastels so chips and bars stay distinct. Canvas and SVG figures read the tokens at draw time and redraw when the scheme changes.

In the light scheme the gold (3.76:1) and light blue (4.26:1) caps are below text contrast on paper. Caps are for chips, outlines and bars; text that carries a cap's meaning is set in ink or Carbon Grey beside a chip. Red is the exception that holds text contrast (6.18:1), so the "Missed" stamp can be red.

### Named Rules
**The Cap Code Rule.** A cap colour names a pipeline stage: lavender gate, light blue calibration, gold detector, green evaluation, red risk, grey neutral. It appears as a round chip beside the section, figure or stage it codes, and the rail legend states the code. A new section takes the cap of the stage it belongs to, or grey.

**The Blue Ink Rule.** Requisition blue draws the form: rules, labels, numbers, focus, the τ line, primary actions. Reading text is ink, and blue reaches running text only as a link.

## Typography

**Display Font:** Archivo, narrowed on its width axis (with Arial Narrow, Roboto Condensed, system-ui)
**Body Font:** Atkinson Hyperlegible Next (with Atkinson Hyperlegible, system-ui, Segoe UI, Roboto)
**Label/Mono Font:** Atkinson Hyperlegible Mono (with ui-monospace, SF Mono, Menlo, Consolas)

**Character:** A condensed grotesk prints the parts of the form, and a face built for low-vision legibility fills them in. Its mono sibling keeps IDs, readouts and τ values aligned and unambiguous.

All three load from Google Fonts in one request: Archivo on width 62–125 and weight 500–800, Atkinson Hyperlegible Next at 400, 600, 700 and 400 italic, Atkinson Hyperlegible Mono at 400, 500 and 700. The build narrows Archivo with `font-stretch` (78–90%); the frontmatter records the same values on the `wdth` axis.

### Hierarchy
- **Display** (800, clamp(2.1rem, 4.4vw, 3.4rem), 1.0, width 78%): the title in the requisition header, and only there.
- **Headline** (800, 1.9rem, 1.6rem under 760px, 1.1, width 80%): section headings, led by a cap chip and a mono section-number box. The triage strip heading is a step down (1.35rem, width 82%).
- **Title** (700, 1.15rem, 1.3, width 90%): sub-headings inside a section.
- **Figure head** (700, 14.5px, width 88%, requisition blue): the "Fig. n · Name" bar on each figure.
- **Label** (700, 12.5–13px, width 85–88%, +0.02em, requisition blue, sentence case): field labels, tally and readout labels, guide titles. Table headers use the same voice at 13.5px; contents-rail headings use it in Carbon Grey.
- **Body** (400, 17px, 16.5px under 760px, 1.62): reading text, at most 70ch. Lead paragraphs run at 1.12rem and 62ch.
- **Body small** (400, 15.5px): field values (68ch), table cells, the safety notice.
- **Caption** (400, 15px, Carbon Grey): figure captions (72ch) and guide boxes; legends drop to 13.5px.
- **Readout** (Mono 700, 1.15rem, tabular figures): live figure values. The triage tally uses 1.3rem.
- **Code** (Mono 400, 14px, 1.6): command blocks; inline code at 0.86em on a Field Tint chip.
- **Tag** (Mono 600, 12px): "Simulated data" and "Illustrative inputs". The Pending box uses 12.5px.

### Named Rules
**The Three Hands Rule.** Archivo condensed prints the form: headings, labels, figure heads, stamps. Atkinson Hyperlegible Next is what you read. Atkinson Hyperlegible Mono is what you count or copy: IDs, τ, readouts, code. A string belongs to one hand only.

**The Sentence Case Rule.** Labels, headings and stamps are set in sentence case with tracking no wider than 0.04em. Nothing on the form is set in all caps.

## Layout

The frame is a contents rail beside a document sheet. On wide screens the rail is 232px, sticky at full viewport height, with a hairline on its right edge; the sheet fills the rest, and the pair centres at a 1320px maximum. The sheet has a 32px top and 48px side inset. The requisition header, safety notice and triage strip stack at the top of the sheet as the first viewport, and numbered sections follow with 56px above each.

Inside the sheet, reading measure stays narrow while the form spans the full width: paragraphs cap at 70ch, field values at 68ch and captions at 72ch, while field lists, tables and figure frames run edge to edge. Header fields split 1.1 : 1.4 : 1.6. Figures put the plot and its controls on the left and the guide and readouts on the right (1.25fr : 1fr, 22px gap). The 40 study tickets sit in a 10-column grid with 6px gaps.

At 1100px and below, the rail turns into a sticky horizontal contents bar along the top that scrolls sideways inside itself, showing cap chips and section names only, and the sheet's side inset narrows to 28px. At 760px and below, the side gutter is 16px, figure grids and field lists go to one column, header fields go two-up with links on their own row, tables restack into labelled rows, and tickets compact to eight across with the ID and "Detector" text hidden, so colour and stamp carry the state. The slider and τ button move above the tickets. The page holds at 360px with no horizontal scroll; wide figures scroll inside their own frame.

### Named Rules
**The Ruled Field Rule.** Facts go in labelled field cells, not bullet lists. A field list opens with a 1.5px requisition-blue rule, separates cells with 1px hairlines, and puts the label above its value. It runs two columns with a hairline between them on wide screens and one column under 760px; the one-column variant sets a 170px label column beside the value.

## Elevation & Depth

The system is flat. No element in the build has a shadow, a gradient fill or a blur. Depth is carried by rule weight and tint alone. Three rule weights do the work: 1.5px requisition blue for the structural edges of the form (the header outline and its divider, the top of every field list, the footer, button outlines), 1px Form Rule for frames, the triage strip, tickets and tables, and 1px Hairline for dividers inside them. The safety notice is the one 1.5px red edge. Tint sets things apart where a rule cannot: Header Wash behind figure heads and table headers, Field Tint for guides and cleared tickets, and a 6–7% red wash into paper behind the safety notice and a missed ticket.

### Named Rules
**The Flat Stock Rule.** Paper does not lift. No box-shadow, gradient fill or blur on any page surface; a part is set apart by its rule weight or a tint. The logo's film gradient belongs to the brand asset and is not a surface treatment.

## Shapes

Corners are small and square-set: 2px for stamps, tags, the pending box and ticket checkboxes; 3px for buttons, inputs, frames, tickets, tables, code and diagram boxes; 4px for the large parts of the sheet (requisition header, safety notice, triage strip, contents links). Round is reserved. Cap chips are true circles from 9px (in tickets and the legend) to 16px (beside section headings), the status dot is a 10px circle, and live-demo steps are counted in 28px requisition-blue circles with paper numerals.

Dashed lines mean a boundary or something not yet filled in: the τ mark on each ticket, the Pending box outline, the fused box in Fig. 3, the Grad-CAM arrow in Fig. 1. Stamps sit at −8°. Diagrams are schematic: 3px-cornered boxes with 2px strokes in the cap colour of their stage (Form Rule for the input and the cleared exit), a decision diamond outlined in requisition blue, and muted connector lines ending in filled triangular heads. Nothing imitates a radiograph.

### Named Rules
**The Only Caps Are Round Rule.** A circle is a cap chip, the status dot or a step counter. Fields, buttons, frames and tickets keep 2–4px corners.

## Components

### Buttons
Plain and printed, like the action boxes on a form.
- **Shape:** squared with a slight ease (3px).
- **Primary:** Requisition Blue fill and 1.5px border, Form Stock text, Atkinson Hyperlegible Next 700 at 14.5px, 8px 13px padding. Used for the live demo's Connect and Analyze.
- **Secondary:** transparent with a 1.5px Requisition Blue border and blue text. The working button of the page: the 95% sensitivity button, figure presets, Show Grad-CAM. The file picker's button takes the same style.
- **Hover / Focus:** secondary buttons take the Header Wash on hover; the primary has no hover change. Focus is the global 3px Requisition Blue outline at 2px offset. Disabled buttons drop to 45% opacity with a not-allowed cursor.
- **Labels:** a verb or the setting it applies ("Connect", "Set τ for 95% sensitivity", "Pull B away", "Hospital GPU"), with no trailing arrow.

### Chips
- **Cap chip:** a solid circle in a cap colour (9–16px), always beside the label it codes; decorative chips are `aria-hidden` and the code is stated in text nearby.
- **Tag:** Mono 600 12px Carbon Grey in a 1px Form Rule box with 2px corners. It marks honesty labels ("Simulated data", "Illustrative inputs") beside the figure heading or caption they qualify.

### Cards / Containers
- **Requisition header:** Form Stock inside a 1.5px Requisition Blue outline (4px corners). A top band holds the 58px logo, the display title and a Carbon Grey subtitle; a 1.5px blue divider separates a row of labelled field cells (Author, Status, Links) split by Form Rule lines.
- **Figure frame:** Form Stock, 1px Form Rule outline, 3px corners, 18px inset. It opens with a full-bleed figure head (Header Wash, cap chip, "Fig. n · Name" in Requisition Blue) and closes with a caption outside the frame that starts with a bold "Fig. n."
- **Guide box:** Field Tint, 1px Hairline, 3px corners, 10px 12px inset, 15px text under a blue label ("Read it like this", "Try").
- **Safety notice:** a 1.5px red outline with 4px corners on a 6% red wash, a red cap chip, and a bold first sentence. It is always present.
- **Shadow strategy:** none (see Elevation & Depth).

### Inputs / Fields
- **Style:** Form Stock fill, 1px Form Rule stroke, 3px corners, ink text in Mono 500 at 15px. Number inputs are 84px wide (full width in the impact calculator) with the spinners removed; the API address field grows beside its Connect button. Labels sit above in 14px Carbon Grey.
- **Range:** a 4px Form Rule track with a square-cornered thumb (3px corners, Form Stock fill, 2px Requisition Blue border). Its value prints beside the label in Mono.
- **Focus:** the global 3px Requisition Blue outline.
- **Input edge:** text, number and URL inputs use a dedicated `--input-line` stroke (#6B7FB3 on paper, 3.95:1; #6A80B8 in dark, 4.76:1) so the field boundary meets the 3:1 non-text floor. The lighter Form Rule stays for rules and frames, never as an input's only boundary.

### Navigation
- **Contents rail:** brand lockup (30px logo, Archivo 700 at 15px), a "Contents" label, then the sections in order, each with a Mono number, a 10px cap chip and its name. Links rest in Carbon Grey, turn ink on a Field Tint wash on hover, and the section in view is marked with `aria-current` on a Header Wash with bold ink. Below the list, a small legend states the cap code (Gate, Calibration, Detector, Evaluation, Risk); the author line sits at the foot.
- **Narrow screens:** at 1100px the rail becomes a sticky top bar of cap chips and names that scrolls sideways; brand, numbers, legend and foot are hidden.

### Study ticket and stamp
The signature component: one simulated study as a specimen label. A 1px Form Rule box (3px corners) holds a Mono ID, a cap chip for ground truth (red abnormal, grey normal), a 4px Hairline bar with an ink tick at the study's gate score and a dashed blue τ line, and a "Detector" checkbox label in Requisition Blue.
- **Sent:** Requisition Blue outline, the box ticked.
- **Cleared:** Field Tint fill, Hairline outline, a muted tick, and a Carbon Grey "Cleared" stamp.
- **Missed:** a 1.5px red outline, a 7% red wash, and a red "Missed" stamp.
- **Stamp:** Archivo 800 at 10px, width 80%, +0.04em, in a 1.5px current-colour box with 2px corners, set at −8°. It springs in from 40% scale over 0.28s on `cubic-bezier(.2, 1.4, .4, 1)`; ticket fills and outlines change over 0.25s. Under reduced motion every transition collapses to 1ms.

### Tally and readouts
Live numbers in labelled cells. The triage tally is a row of three cells in a 1px Hairline box (blue label, Mono 700 count at 1.3rem, "of 40" in small Carbon Grey). Figure readouts are a two-column grid in a Form Rule box with Hairline dividers, blue labels and Mono 700 values at 1.15rem, all with tabular figures.

### Pending result
**The Empty Box Rule.** A metric with no published value is an empty box: Mono 600 at 12.5px, Carbon Grey "Pending", in a 1px dashed Form Rule outline with 2px corners, at least 92px wide, right-aligned in its table row. It is never replaced by a placeholder number.

### Section heading
A cap chip (16px), a Mono section number in a 1.5px Requisition Blue box with 3px corners, then the headline. Summary and References carry a chip but no number.

## Do's and Don'ts

### Do:
- **Do** give every section, figure and pipeline stage one cap chip from the code (lavender gate, light blue calibration, gold detector, green evaluation, red risk, grey neutral), and keep the rail legend in step with it.
- **Do** put facts in labelled, ruled fields or tables: a 1.5px Requisition Blue rule on top, 1px Hairlines between cells, the label in Archivo condensed above the value.
- **Do** set IDs, τ, readouts and code in Atkinson Hyperlegible Mono with tabular figures, and reading text in Atkinson Hyperlegible Next at 17px / 1.62 within 70ch.
- **Do** open each interactive figure with a figure head (Header Wash, cap chip, "Fig. n · Name"), a "Read it like this" guide box and one-click presets, and caption it below with a bold "Fig. n."
- **Do** mark simulated figures and illustrative inputs with the Mono tag next to the figure, and show unpublished metrics as the dashed Pending box.
- **Do** define each colour in both schemes on the same token name, and have canvas and SVG figures read tokens at draw time and redraw when the scheme changes.
- **Do** separate parts with rule weight (1.5px Requisition Blue for the form's structure, 1px Form Rule for frames, 1px Hairline inside) and with Field Tint or Header Wash, not with depth.

### Don't:
- **Don't** add box-shadows, gradient fills or blur to page surfaces; the logo's gradient stays inside the logo.
- **Don't** use a cap colour as decoration or give a new section a colour outside the code; red stays with findings, misses, risk and errors.
- **Don't** set labels or headings in all caps, or end button labels with an arrow.
- **Don't** set body copy in Requisition Blue; blue in running text is a link.
- **Don't** round anything past 4px except cap chips, the status dot and step counters.
- **Don't** draw anything that imitates a radiograph; figures stay schematic boxes, lines, bars and curves.

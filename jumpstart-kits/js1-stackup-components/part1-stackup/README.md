# JS1 Part 1 — Stackup

**Shortcut:** {download}`Download the runbook <JS1_Part1_Stackup-from-Fab-CSV_Runbook.md>`, hand it
to your AI coding agent along with [the supplied fab CSV](JS1_Part1_Fab-Stackup_RevB.csv), and tell
it to follow the file. Two `[HUMAN]` gates stop for you. Assumes [JS0](../../js0-setup/) is done.

Build a 20-layer HDI substrate from the fab's stackup report by driving `jitx-substrate-modeler`.
ACME quote Q26-0417 Rev B · 20 layers · 5-10-5 HDI · 0.80 mm core · four impedance targets. Turn the
fab's CSV into substrate code, then verify every number back against the report.

## The deck

Six slides, written out below so you can see what the part teaches without downloading anything.

- [JS1_Part1_Stackup_Presentation.pdf](JS1_Part1_Stackup_Presentation.pdf) — read-only, opens anywhere
- [JS1_Part1_Stackup_Presentation.pptx](JS1_Part1_Stackup_Presentation.pptx) — editable PowerPoint

**Why this task.** Your fab quotes a stackup as a spreadsheet — materials, thicknesses, vias,
impedance tables — and that file, not a template and not a guess, is the only source of truth.
Estimate nothing: every material, thickness, via and trace width traces to one CSV row, and where
the CSV is silent the agent stops and asks you.

**What you build.** One `Dielectric` or `Conductor` class per CSV material row, with Dk/Df and
roughness exactly as stated. An explicit 41-entry `Stackup`, top mask to bottom mask, every copper
layer function-named — no `Symmetric` shortcut, whose mirrored half is unnamed proxies no CSV row
can be pointed at. All 19
`FabricationConstraints` fields from the FAB_RULES section. The report's full via inventory: ten
single-level laser microvias, the buried L6–L15 sub-composite via, the L1–L20 through-hole. And one
routing structure per impedance target — 40 / 50 / 55 Ω single-ended and 100 Ω differential — each
solved on both layer groups: microstrip on L1/L20, controlled stripline on L3/L5/L16/L18.

**How we know it's right.** The CSV is re-read, not remembered — the tests parse the report and
compare the translated design against it, and the summed stack thickness must equal the report's
finished thickness, which is the classic transcription-slip catch. A `[HUMAN]` gate walks the
conductor-index map (0 = L1, −1 = L20) against the report before any rules land on it. The code
carries no number the report didn't state, so a Rev C flows straight through.

**Close the loop.** *"the fab came back on the through-hole again — 0.400 mm finished hole this
time"* — hand the agent a Rev C and watch the change flow through code, tests, and build.

## The runbook

[JS1_Part1_Stackup-from-Fab-CSV_Runbook.md](JS1_Part1_Stackup-from-Fab-CSV_Runbook.md) opens the
runbook to read. To save the raw markdown instead — the form you hand to an agent —
{download}`download it <JS1_Part1_Stackup-from-Fab-CSV_Runbook.md>`.

## The supplied input

[JS1_Part1_Fab-Stackup_RevB.csv](JS1_Part1_Fab-Stackup_RevB.csv) is the ground truth this part is
built and verified against — hand it to the agent alongside the runbook.

It is a synthetic impedance-controlled stackup report, sectioned so it parses with Python's `csv`
module. ACME Circuit Technology is fictional; the laminates and copper foils are real. You can
substitute your own fab's stackup export.

## The reference solution

Verified code ships importable in the `jitxexamples` package, module
[`jitxexamples.jumpstart_kits.js1_stackup_components.hdi_stackup`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js1_stackup_components/hdi_stackup).

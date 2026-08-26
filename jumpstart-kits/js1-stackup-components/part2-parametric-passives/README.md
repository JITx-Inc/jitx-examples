# JS1 Part 2 — Parametric passives

**Shortcut:** {download}`Download the runbook <JS1_Part2_Parametric-Passives_Runbook.md>`, hand it
to your AI coding agent, and tell it to follow the file. Two `[HUMAN]` gates stop for you. Assumes
[JS0](../../js0-setup/) is done.

Build four component families with no parts database by driving `jitx-component-modeler`. Yageo
RC_L · Panasonic ERJ · Vishay CRCW · Samsung CL, straight from their datasheets — parameterized
families where the class is the data, so you can ask for any part in the catalog and get an
orderable MPN back.

## The deck

Six slides, written out below so you can see what the part teaches without downloading anything.

- [JS1_Part2_Parametric-Passives_Presentation.pdf](JS1_Part2_Parametric-Passives_Presentation.pdf) — read-only, opens anywhere
- [JS1_Part2_Parametric-Passives_Presentation.pptx](JS1_Part2_Parametric-Passives_Presentation.pptx) — editable PowerPoint

**Why this task.** One class stands in for a manufacturer's whole catalog family — sizes,
tolerances, power ratings, packaging — transcribed once from the datasheet. Ask for 49.9 kΩ ±1 % in
0402 and the class derives the dimensions, land pattern, ratings and the exact orderable MPN,
entirely offline with no parts database and no network. An invalid combination raises a `ValueError`
listing what the family actually offers: the datasheet's constraints, enforced at construction.

**The pattern.** A shared core plus a thin layer per vendor. `chip_smt.py` holds `ChipDims`
(Toleranced package dimensions), the chip-size land-pattern generator, the two-pin series insert,
the E-series value check, and carry-correct significant rounding. Each vendor layer adds only its
own encoding — Yageo's RKM code (`100K`), Panasonic's EIA 3-digit (`103`), Vishay's fixed 4-char RKM
(`10K0`) plus a TCR axis, Samsung's 3-char pF code (`104`) plus dielectric and voltage axes. Shared:
geometry, insertion, validation. Never shared: the vendor's value encoding and part-number grammar.

**What you build.** Family 1 (Yageo) self-contained — eleven chip sizes, tolerance and packaging
axes — with no helpers yet, because nothing has repeated. Family 2 (Panasonic) proves what's shared,
so `chip_smt.py` is born and Family 1 is refactored onto it. Family 3 (Vishay) adds the TCR axis and
takes the generator's standard EIA dimensions for Vishay's standard case codes — asserted per size
against the datasheet's own table, because a default nobody checked is how a bad land pattern ships. Family 4
(Samsung) generalizes the pattern across component type, adding a capacitor symbol on the same core.
Proof is by part number: `RC0402JR-07100KL`, `ERJ3GEYJ102V`, `CRCW0603562RFKEA`, `CL10B104KB8NNNC`.

**How we know it's right.** Dimensions, ratings and codes are hand-read from the four datasheets and
asserted in tests, per family, before it counts as done. Generated part numbers match the vendors'
catalog listings character for character. Requested values validate against the tolerance's E-series
grid, with carry-correct rounding before encoding. And all four families instantiate together in one
design that builds successfully — the showcase the closing prompt answers from.

**Close the loop.** *"give me a 49.9 kΩ 0402 1 % Yageo and a 100 nF X7R 0603 50 V Samsung CL"* —
two real, orderable parts, MPNs included, answered from code.

## The runbook

[JS1_Part2_Parametric-Passives_Runbook.md](JS1_Part2_Parametric-Passives_Runbook.md) opens the
runbook to read. To save the raw markdown instead — the form you hand to an agent —
{download}`download it <JS1_Part2_Parametric-Passives_Runbook.md>`.

## The supplied inputs

None to download: the runbook hands the agent the four manufacturer datasheet URLs, which it fetches
during the run. Those datasheets are the ground truth this part is verified against.

## The reference solution

Verified code ships importable in the `jitxexamples` package, module
[`jitxexamples.jumpstart_kits.js1_stackup_components.parametric_passives`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js1_stackup_components/parametric_passives).

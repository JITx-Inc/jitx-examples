<!-- Versal FPGA from the Vendor Pin File — Reference Companion (JS1 · Part 3) · rev 1.1 · 2026-08-27 -->

# Versal FPGA from the Vendor Pin File — Reference Companion (JS1 · Part 3)

Human-facing companion to the **Versal-FPGA-from-Pin-File Runbook**. Read it to understand what
the task builds and why, to review the reference solution, or to run the pieces by hand. The
runbook itself is agent-executable; this page is for you.

---

## What this task is

Model the **AMD Versal Premium VP1002** in the **NFVI1369** package — 1369 balls on a full 37×37
grid at 0.92 mm pitch — and wrap it in the circuit boundary a board design consumes. At this pin
count the component-handling lesson changes: Part 2 taught *datasheet tables become code*; Part 3
teaches **the vendor's machine-readable pin file becomes code** — you parse and generate, then
spend your effort verifying the generation instead of typing 1369 rows.

Ground truth is two AMD documents, both fetched during the run and never committed:

- the **package pinout file** `xcvp1002nfvi1369pkg.txt` (names, balls, banks — the only pin truth),
- **AM013**, the Versal packaging manual — the figure captioned *Package Dimensions for NFVI1369*
  (mechanical), the table captioned *BGA Package Design Rules* (PCB land rules), and the figure
  captioned *VP1002 Banks in NFVI1369 Package* (the bank diagram, which carries the transceiver
  supply-group tag per quad). Cited by caption because AM013 renumbers between editions — the
  mechanical drawing was Figure 246 in v1.9 and Figure 273 in v1.10.

## What you end up with

| Artifact | What it is |
|---|---|
| `tools/generate_pinout.py` | Committed, stdlib-only generator: parse → reconcile → emit. `--report` prints the inventory; `--check` proves the committed module regenerates byte-identically. |
| `xcvp1002.py` (generated) | The `jitx.Component`: one `Port` per ball — 432 unique pins by their exact AMD names, 30 repeated rails as indexed lists — plus the ball map as zero-indexed coordinates, GTM quad groupings, and symbol partitions. |
| `landpattern.py` | The 37×37 BGA land pattern from AM013 values, with a public `get_pad(row, column)` adapter. |
| `symbols.py` | Partition policy: ~43 schematic boxes, one per bank / GT quad, rails chunked at ≤ 64 pins. |
| `bundles.py` + `circuit.py` | `GTMQuad` (4 lanes + 2 refclks) and `XCVP1002Circuit`: 31 supply rails as `Power` ports, three ground domains, six GTM quads wired as bundles. |
| Tests + two buildable designs | Offline invariants (counts, spot-checked balls, symbol coverage, mapping bijectivity, circuit roster) and non-test `jitx build` smoke targets for the component and the wrapped circuit. |

Reference solution: the `jitxexamples` package, module
[`jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js1_stackup_components/versal_fpga).

## The pin inventory (from the pinout file — the numbers the run must reconcile)

| Group | Balls |
|---|---|
| GND (+ RSVDGND, GND_SMON, GND_SENSE) | 689 (+2, +1, +1) |
| Power rails (VCCINT 84, VCC_SOC 18, VCCO_\*, GT analog rails, …) | 193 |
| XPIO user IO — banks 700/701/702 | 163 |
| GTM transceivers — six quads, banks 202–207 (+ bias pins) | 122 |
| PS MIO / config / sysmon — banks 500–503 + VP/VN/VREF | 97 |
| GTY transceivers — banks 103/105 (+ bank 109 bias pair) | 41 |
| NC | 60 |
| **Total** | **1369** |

Six GTM quads, each 4 × (RXP/RXN/TXP/TXN) lanes + 2 × REFCLK pairs; the quad-column bias pins
(`GTM_RREF_*`, `GTM_AVTTRCAL_*`, and the GTY equivalents) are single balls that take one external
precision resistor each — the circuit wrapper exposes them as pass-through ports.

## Two traps the runbook makes you catch

1. **`ball_diameter` sets the PCB land diameter.** The mechanical drawing gives the physical
   solder ball as Ø 0.50/0.64/0.70 mm — but the JITX BGA generator's `ball_diameter` argument
   sets the **PCB land diameter**. The right number is the design-rule table's **0.51 mm** (max
   NSMD land for 0.92 mm pitch). The runbook makes the agent open the generator source and prove
   which one the parameter drives before writing it down.
2. **A `Port` has exactly one home.** Storing a second collection of the component's ports
   (a symbol-group list, a rail roster attribute) fails translation with *"Child object
   encountered multiple times."* Groupings are exposed as **methods returning fresh records**
   (`gtm_quad_pins()`, `symbol_partitions()`, `rail_ties()`). Related: name boundary rail ports
   differently from the net names (`pwr_vccint`, not `VCCINT`) — a collision fails only in the
   full runtime build, not in `--dry`.

## How the reference solution was verified

- Generator reconciliation: parsed rows = file footer = **1369**, unique balls, full grid; the
  committed module regenerates **byte-identically** (`--check`).
- 17 tests + 74 subtests pass offline on the jitx 4.4 line, including ~10 hand-read
  ball spot-checks spanning the grid corners and every bank type, symbol coverage (every port in
  exactly one box), and mapping bijectivity. Both non-test designs `jitx build` with `status: ok`.
- Every one of the 1369 balls was **independently re-checked against the AMD file** by a
  13-agent review fan-out (grid slices plus rails / GTM / symbols / conventions audits) — zero
  mismatches.
- A **fresh agent replayed the runbook from its own text** in an empty project: all four
  `[HUMAN]` gates exercised, its build successful, and its generated ball map converged to the
  reference **identically — 1369/1369 matching (name, row, col) triples**.
- Corner-to-corner geometry: A1 ↔ AU37 pad centers measure 36 × 0.92 = **33.12 mm** on both
  axes, matching AM013's D1/E1 exactly.

## Running the pieces by hand (no agent)

There is no by-hand transcription path at this pin count — the generator *is* the manual path:

```bash
# from a checkout of jitx-examples, with the AMD pinout file downloaded to .context/
python -m jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga.tools.generate_pinout \
    .context/xcvp1002nfvi1369pkg.txt --report      # inventory + reconciliation
python -m jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga.tools.generate_pinout \
    .context/xcvp1002nfvi1369pkg.txt --check       # committed module is regeneration-exact
jitx build jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga.main.VersalFPGADesign
jitx build jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga.main.VersalFPGACircuitDesign
```

Expect roughly **2–3 hours** end to end for the full runbook with an agent (most of it
agent-autonomous); the build-and-verify commands above take a few minutes on a checkout.

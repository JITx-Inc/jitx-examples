# JS1 Part 3 — FPGA

**Shortcut:** {download}`Download the runbook <JS1_Part3_Versal-FPGA-from-Pin-File_Runbook.md>`,
hand it to your AI coding agent, and tell it to follow the file. Four `[HUMAN]` gates stop for you,
and expect roughly 2–3 hours, most of it agent-autonomous. Assumes [JS0](../../js0-setup/) is done.

Build a Versal FPGA from vendor data by driving `jitx-component-modeler` and `jitx-circuit-builder`.
AMD Versal Premium VP1002 · NFVI1369 · 1,369 balls. Parse the machine-readable pin file, generate
the component, verify the generation, then wrap it in the circuit a board design consumes.

## The deck

Six slides, written out below so you can see what the part teaches without downloading anything.

- [JS1_Part3_Versal-FPGA_Presentation.pdf](JS1_Part3_Versal-FPGA_Presentation.pdf) — read-only, opens anywhere
- [JS1_Part3_Versal-FPGA_Presentation.pptx](JS1_Part3_Versal-FPGA_Presentation.pptx) — editable PowerPoint

**Why this task.** AMD publishes the ball map as a machine-readable ASCII file — names, balls, banks
— and that file is the only pin ground truth. Parse it, don't transcribe it: a committed,
stdlib-only generator reconciles the file to exactly 1,369 balls before any component code exists.
Effort moves from typing to checking, and then the flat pin map is lifted into a circuit boundary —
power rails, ground domains and GTM quads as JITX-native ports, which is what a board designer
actually consumes.

**The part.** Six GTM quads on the east column (banks 202–207), XPIO south (700–702), PS/config
north (500–503), rendered from the AMD pinout file rev 1.1.

**What you build.** `tools/generate_pinout.py`, a committed stdlib-only generator that parses,
reconciles (1,369 = file footer = full 37×37) and emits; `--report` prints the inventory and
`--check` proves the committed module regenerates byte-identically. `xcvp1002.py` (generated) gives
one `Port` per ball: 432 unique pins under their exact AMD names, 30 repeated rails as indexed lists
(GND ×689, VCCINT ×84, NC ×60), the ball map as zero-indexed coordinates, GTM quad groupings and
symbol partitions. `landpattern.py` is the 37×37 BGA from AM013 — body 35×35 mm, land Ø 0.51 mm,
with a public `get_pad(row, column)` adapter. `symbols.py` builds ~43 schematic boxes, one per bank
or GT quad, rails chunked at ≤ 64 pins, every port in exactly one box. `bundles.py` and `circuit.py`
add `GTMQuad` (4 lanes + 2 refclks) and `XCVP1002Circuit`: 31 `Power` rails, three ground domains
(GND / GND_SMON / GND_SENSE), and six GTM quad bundles wired through the generated pin groupings.

**How we know it's right.** Reconciliation runs before any code: parsed rows = file footer = 1,369,
unique balls, full 37×37 grid. Then 17 tests and 74 subtests on public jitx 4.2.2 — hand-read ball
spot-checks across grid corners and every bank type, symbol coverage, mapping bijectivity, circuit
rail roster. Both designs, the component viewer and the wrapped circuit, build `status: ok` against
the runtime. An independent 13-agent review re-checked all 1,369 balls against the AMD file with
zero mismatches. A fresh agent replayed the runbook in an empty project and landed a ball map
identical to the reference, 1,369/1,369 on name, row and column. And the geometry checks out: A1 ↔
AU37 pad centers = 36 × 0.92 = 33.12 mm on both axes, exactly AM013's D1/E1.

**Close the loop.** *"give me GTM quad 205 as a 4-lane bundle and tell me which power rails and bias
pins it needs"* — answered live from the built circuit.

## The runbook

[JS1_Part3_Versal-FPGA-from-Pin-File_Runbook.md](JS1_Part3_Versal-FPGA-from-Pin-File_Runbook.md)
opens the runbook to read. To save the raw markdown instead — the form you hand to an agent —
{download}`download it <JS1_Part3_Versal-FPGA-from-Pin-File_Runbook.md>`.

## The supplied inputs

None to download: the agent fetches AMD's package pinout file `xcvp1002nfvi1369pkg.txt` and AM013,
the Versal packaging manual, from AMD's site during the run. Those two documents are the ground
truth this part is verified against.

## The reference companion

[JS1_Part3_Reference_Companion.md](JS1_Part3_Reference_Companion.md) is the human-facing summary of
this task: the artifact table, the pin inventory, the two traps the runbook makes you catch, how the
reference solution was verified, and the commands to run the pieces by hand.

## The reference solution

Verified code ships importable in the `jitxexamples` package, module
[`jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js1_stackup_components/versal_fpga).

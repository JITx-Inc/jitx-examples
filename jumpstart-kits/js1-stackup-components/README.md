# JS1 — Stackup and Component Handling

**Shortcut:** Download the runbook for the part you want, hand it to your AI coding agent, and tell
it to follow the file:

- {download}`Part 1 · Stackup <part1-stackup/JS1_Part1_Stackup-from-Fab-CSV_Runbook.md>` — hand it
  [the supplied fab CSV](part1-stackup/JS1_Part1_Fab-Stackup.csv) as well
- {download}`Part 2 · Versal FPGA <part2-versal-fpga/JS1_Part2_Versal-FPGA-from-Pin-File_Runbook.md>`

**Start a new agent session before you begin any part.** Every step of a JS1 runbook drives a JITX
skill, and a skills install only takes effect in a session started after it.

Each part is self-contained and stops at the `[HUMAN]` steps that need you, but all of them assume
[JS0](../js0-setup/) is done. Everything below is the context around each part.

JS1 has two parts, building a stackup (Part 1) and component creation (Part 2). They are
**independent**, so either can be tackled first.

In every part the user uses agents to drive a JITX skill rather than hand-writing the code, and
nothing counts as done until it clears its ground-truth check (the fab spec or the
vendor pin file) **and** `jitx design build <non-test design target>` completes successfully.

## Start here — the JS1 walkthrough

Each part has its own page carrying everything that part needs: the
runbook you hand to an agent, any supplied input, and the reference solution.

### Part 1 — Stackup

Turn a fab-house stackup report into a verified 20-layer HDI substrate by driving
`jitx-substrate-modeler`, with tests that re-read the report and a summed stack thickness that has
to equal the report's finished thickness. Two `[HUMAN]` gates stop for you.

Runbook, the supplied fab CSV, and the reference solution are on the
[Part 1 page](part1-stackup/).

### Part 2 — FPGA

Generate a 1,369-ball FPGA (Versal) component from the vendor's machine-readable pin file, then wrap
it in the circuit so a board design can instantiate the FPGA by driving `jitx-component-modeler` and
`jitx-circuit-builder`.

The part is an AMD Versal Premium VP1002 in the NFVI1369 package, and AMD publishes its ball map as
a machine-readable file — so you parse it rather than transcribe it. A committed, stdlib-only
generator reconciles the file to exactly 1,369 balls before any component code exists, and the
circuit wrapper lifts the flat pin map into what a board designer actually consumes: 31 `Power`
rails, three ground domains, and six GTM transceiver quads as bundles. Verification is layered —
reconciliation (parsed rows = file footer = full 37×37 grid), an offline test suite including
hand-read ball spot-checks, and both designs building `status: ok`. Expect roughly 2–3 hours across
four `[HUMAN]` gates, most of it agent-autonomous.

Runbook, the reference companion, and the reference solution are on the
[Part 2 page](part2-versal-fpga/).

## Reference solutions

Verified code for both parts ships as importable code in the `jitxexamples` package, under
[`jitxexamples.jumpstart_kits.js1_stackup_components`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js1_stackup_components) —
one module per part, named on that part's page.

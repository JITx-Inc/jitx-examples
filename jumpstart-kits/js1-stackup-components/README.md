# JS1 — Stackup and Component Handling

**Shortcut:** Download the runbook for the part you want, hand it to your AI coding agent, and tell
it to follow the file:

- {download}`Part 1 · Stackup <part1-stackup/JS1_Part1_Stackup-from-Fab-CSV_Runbook.md>` — hand it
  [the supplied fab CSV](part1-stackup/JS1_Part1_Fab-Stackup.csv) as well
- {download}`Part 2 · Parametric passives <part2-parametric-passives/JS1_Part2_Parametric-Passives_Runbook.md>`
- {download}`Part 3 · Versal FPGA <part3-versal-fpga/JS1_Part3_Versal-FPGA-from-Pin-File_Runbook.md>`

**Start a new agent session before you begin any part.** JS0 installs the JITX skills, and a skills
install only takes effect in a session started after it — so the session that finished JS0 cannot run
a JS1 runbook, whose every step drives a skill. Nothing on disk changes; the session boundary is the
whole of it.

Each part is self-contained and stops at the `[HUMAN]` steps that need you, but all of them assume
[JS0](../js0-setup/) is done. Everything below is the context around each part.

JS1 consists of three parts: building a stackup (Part 1) and component creation (Parts 2 and 3) are
**independent** — so any part can be tackled first.

In every part the user uses agents to drive a JITX skill rather than hand-writing the code, and
nothing counts as done until it clears its ground-truth check — the fab spec, the datasheet, or the
vendor pin file — **and** `jitx build <non-test design target>` completes successfully.

## Start here — the JS1 walkthrough

Each part has its own page carrying everything that part needs: the deck as PDF and PPTX, the
runbook you hand to an agent, any supplied input, and the reference solution.

### Part 1 — Stackup

Ingest a fab-house stackup report into a custom 20-layer HDI substrate by driving
`jitx-substrate-modeler`.

The supplied report is ACME quote Q26-0417 Rev B — 20 layers, 5-10-5 HDI, 0.80 mm core, four
impedance targets — and it, not a template, is the only source of truth. You end up with one
material class per CSV row, an explicit 41-entry `Stackup` with every copper layer function-named,
all 19 `FabricationConstraints` fields, the report's full via inventory, and one routing structure
per impedance target on both layer groups. Twenty-five tests re-read the CSV rather than trusting
memory, and the summed stack thickness has to equal the report's finished thickness — the classic
transcription-slip catch. Two `[HUMAN]` gates stop for you.

Deck, runbook, the supplied fab CSV, and the reference solution are on the
[Part 1 page](part1-stackup/).

### Part 2 — Parametric passives

Build parameterized, datasheet-driven component families by driving `jitx-component-modeler`.

Four families — Yageo RC_L, Panasonic ERJ, Vishay CRCW, Samsung CL — transcribed once from their
datasheets so that one class stands in for a manufacturer's whole catalog family. Ask for 49.9 kΩ
±1 % in 0402 and the class derives the dimensions, land pattern, ratings and the exact orderable
MPN, entirely offline with no parts database; an invalid combination raises a `ValueError` listing
what the family actually offers. Proof is by part number — `RC0402JR-07100KL`, `ERJ3GEYJ102V`,
`CRCW0603562RFKEA`, `CL10B104KB8NNNC` — each matching the vendor's catalog listing character for
character, with all four families instantiating together in one design that builds. Two `[HUMAN]`
gates stop for you.

Deck, runbook, and the reference solution are on the
[Part 2 page](part2-parametric-passives/).

### Part 3 — FPGA

Generate a 1,369-ball FPGA (Versal) component from the vendor's machine-readable pin file, then wrap
it in the circuit so a board design can instantiate the FPGA by driving `jitx-component-modeler` and
`jitx-circuit-builder`.

The part is an AMD Versal Premium VP1002 in the NFVI1369 package, and AMD publishes its ball map as
a machine-readable file — so you parse it rather than transcribe it. A committed, stdlib-only
generator reconciles the file to exactly 1,369 balls before any component code exists, and the
circuit wrapper lifts the flat pin map into what a board designer actually consumes: 31 `Power`
rails, three ground domains, and six GTM transceiver quads as bundles. Verification is layered —
reconciliation (parsed rows = file footer = full 37×37 grid), 17 tests and 74 subtests including
hand-read ball spot-checks, and both designs building `status: ok`. Expect roughly 2–3 hours across
four `[HUMAN]` gates, most of it agent-autonomous.

Deck, runbook, the reference companion, and the reference solution are on the
[Part 3 page](part3-versal-fpga/).

## Reference solutions

Verified code for all three parts ships as importable code in the `jitxexamples` package, under
[`jitxexamples.jumpstart_kits.js1_stackup_components`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js1_stackup_components) —
one module per part, named on that part's page.

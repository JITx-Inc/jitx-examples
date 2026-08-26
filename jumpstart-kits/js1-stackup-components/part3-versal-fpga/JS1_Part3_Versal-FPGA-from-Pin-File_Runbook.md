<!--
JITX Versal FPGA from the Vendor Pin File Runbook (JS1 · Part 3)
Paste this file into your AI coding agent (Claude Code, Codex / GPT, or Devin), or upload it,
and tell the agent to follow it. Complete the JS0 Setup Runbook first — this runbook assumes
an authenticated jitx CLI and the JITX skills are already enabled.
-->

# JITX Versal FPGA from the Vendor Pin File Runbook (JS1 · Part 3)

**Goal (for the agent):** In a fresh JITX Python project, model the **AMD Versal Premium VP1002**
FPGA in the **NFVI1369** package — a 1369-ball, full 37×37-grid BGA — and wrap it in a circuit
that exposes its power rails, ground domains, and six GTM transceiver quads as JITX-native
boundary ports. At this pin count you do not transcribe a ball map: you **parse AMD's
machine-readable package pinout file and generate the component**, then verify the generation.
The pinout file is the **only** ground truth for pin names, balls, and banks; AM013 (AMD's Versal
packaging manual) is the only ground truth for package geometry. Estimate nothing; if the data doesn't say it, ask me. Follow
the steps **in order**; nothing is done until it passes its checks and `jitx build <non-test design target>`. Where a step
is marked **[HUMAN]**, stop and wait for me — do not proceed until I confirm.

> **For humans:** prerequisites are a completed **JS0** (authenticated `jitx` CLI on 4.2.2+,
> `jitx-skills` enabled in your agent) and network access to amd.com. Reference solution: the
> `jitxexamples` package, module `jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga`.
> Expect roughly 2–3 hours end to end, most of it agent-autonomous.

**Assumptions / prerequisites**

- JS0 is complete: `jitx --version` is 4.2.2 or newer (pre-releases count) and `jitx auth show`
  confirms authentication. The `jitx` library your project resolves should sit on the same release
  line as the CLI — if pip lands a different line, say so rather than silently proceeding.
- Python 3.12+ and `git` are available; the agent can run shell commands and fetch files from AMD.
- `pip install pymupdf` available for extracting AM013 pages (the component-modeler skill uses it).

---

## Starting instructions — the pattern you are building

These are the instructions this task executes. Read them before step 0. The generic pattern lives in
the component-modeler skill and the steps below delegate to it by section name — read those sections
when a step names one, rather than working from the summary here.

### The recipe

1. Download the **package pinout file** and the **AM013** packaging manual — the two ground truths.
2. Write a **stdlib-only generator** that parses, reconciles, and **emits the component as
   declarative Python**. The generator is committed; the AMD file is not.
3. Build the **land pattern** from AM013 with the stock JITX BGA generator.
4. Partition the **schematic symbols by bank**.
5. Wrap the component in a **circuit** that exposes rails, ground domains and GTM quads as
   JITX-native boundary ports.
6. Verify at every stage: `pyright` → `pytest` → `jitx build <non-test design target>` → the `jitx-code-review` skill.

### What this task supplies

The component-modeler skill carries the pattern — **Generating a component from a machine-readable
vendor pin file**, plus `references/pin-file-generation.md` for the generator shape, and the
**BGA-Specific Notes** in `references/package-examples.md` for the land pattern. Drive it; don't
re-derive it. What is specific to *this* task:

- **The part:** AMD Versal Premium **VP1002** in **NFVI1369** — 1369 balls on a full **37×37** grid,
  0.92 mm pitch. Six GTM transceiver quads (banks 202–207), GTY quads on banks 103/105, XPIO south
  (700–702), PS/config north (500–503).

- **Two ground truths, and neither substitutes for the other.** The pinout file is the only
  authority for pin names, balls and banks. AM013 is the only authority for package geometry and
  for which transceiver group each quad belongs to. **Estimate nothing; if the data doesn't say
  it, ask me.**

- **The row alphabet:** radix-20 over `ABCDEFGHJKLMNPRTUVWY` (I/O/Q/S/X/Z skipped) — A=0, Y=19,
  AA=20, AU=36. The corners are `A1` and `AU37`, both GND.

- **Three ground domains that never merge:** main `GND`, `GND_SMON` (sysmon analog return), and
  `GND_SENSE` (VCCINT Kelvin return). Each takes only its own dedicated ball plus its rails' `Vn`.

- **The bundle shape:** `GTMQuad` = 4 × `LanePair` + 2 × REFCLK `DiffPair`, in the `jitx.common`
  style. The GT bias pins stay *outside* it — see step 11.

- **The symbol-box ceiling for this part is 64 pins**, which puts GND in 11 chunks.

- **Vendor files: link the URL, never commit the file.** The AMD pinout file lives in the
  gitignored `.context/`; the generated module records its sha256 and the AMD URLs.

### Verify (before anything counts as done)

```bash
pyright                 # expect zero errors and zero suppressions
pytest                  # the skill's test shape, plus this task's additions
jitx build <non-test design target>  # both designs: component viewer + circuit wrapper
```

A `pyright: ignore` you feel you need is a finding to report, not a way to reach zero. Run the
`jitx-code-review` skill before the final commit — on this pattern it catches string-keyed models
and port-storage mistakes that happy-path tests miss.

---

## Steps

**0 · Preflight.**
Run `jitx --version` (expect **4.2.2+**) and `jitx auth show` (expect **`Authorized: yes`**). Confirm the JITX skills are invocable — **invoke the base
`jitx` skill first**, since it owns environment and runtime setup, then the two this task drives: the
**component modeler**, and for step 11 the **circuit builder**:

- **Claude Code** — the `jitx-skills` plugin is installed; invoke with `/jitx-skills:jitx`, then
  `/jitx-skills:jitx-component-modeler`.
- **Codex / GPT** — invoke with `$jitx <request>`, then `$jitx-component-modeler <request>`. Name the
  sub-skill rather than relying on `$jitx` to route to it.
- **Devin** — invoke with `@jitx <request>`, then `@jitx-component-modeler <request>`.

**`Authorized: yes` is the field that decides it.** If you also see an `Expires` timestamp in the
past, that is normal and not a failure: the access token is regenerated from the on-disk refresh
token when it is used, headlessly and by design. Don't stop on it, and don't report it as a problem.
Only `Authorized: no` is a stop — and the fix for that is `jitx auth refresh`, per the base skill.

If any check fails, **stop** and tell me to re-run the JS0 Setup Runbook first — do not continue.
`--dry` is not a substitute for the build gates in steps 9 and 12.

**1 · Scaffold a fresh project.**
Create a new project directory and run `jitx project layout init`, then set up the project
environment inside it:

```bash
# macOS / Linux
python3 -m venv .venv && source .venv/bin/activate

# Windows (PowerShell)
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
```

```bash
pip install jitx
jitx project dependencies upgrade
jitx runtime start --background
jitx find
```

Build the seeded non-test target from `jitx find` — ignore any target whose module path comes from
`test`, `tests`, or a test file. **Take the target verbatim from `jitx find`** — the scaffold names
the seeded design class after the project directory, lowercased with hyphens and spaces turned into
underscores, so a directory called `js1-versal-fpga` builds as
`jitx build js1_versal_fpga.main.js1_versal_fpga`. This smoke test must succeed before you write any
code of your own. If it fails, stop and tell me. Then prepare the project: create `tests/`; add
`pytest` and `pyright` as dev dependencies if the scaffold didn't seed them; ensure `.context/` and
`designs/` are gitignored; `git init` + initial commit.

**Run `pyright` inside this venv, every time.** The "pyright clean" gate in steps 9 and 12 means
clean *here*. Run it against any other interpreter and it reports every JITX import as unresolved —
that is pyright telling you it is looking at the wrong Python, not that the imports are wrong, and a
run that stops at import errors has type-checked almost nothing.

**2 · Fetch the ground truth.**
Download into `.context/` (gitignored — **link URLs in docstrings, never commit vendor files**):

- The **xcvp1002 NFVI1369 package pinout file**, `xcvp1002nfvi1369pkg.txt`. The landing page is
  [Versal Adaptive SoC Package Device Pinout Files](https://www.amd.com/en/developer/resources/adaptive-socs-and-fpgas/package-pinout-files/versal-package-device-pinout-files.html),
  but it is a JS-driven page containing **zero `.txt` links** — `curl` + grep finds nothing, which
  looks like a login wall and isn't. The download table is populated from a JSON index:
  `https://download.amd.com/json/adaptive-socs-and-fpgas/developer/resources/package-pinout-files/versal-package-device-pinout-files.json`.
  Resolve the current file path from there. Historical links under `vppackages/` are dead — that
  directory is now `versal/`.

- **AM013**, the Versal Packaging and Pinouts manual
  (https://docs.amd.com/r/en-US/am013-versal-pkg-pinout). You need three things, and per the skill's
  **"Cite by caption first, figure number second"**, find each by **grepping for its caption** — this
  is a living document and the numbers move between editions:
  - the figure captioned **"Package Dimensions for NFVI1369"** (mechanical drawing);
  - the table captioned **"BGA Package Design Rules"** (PCB land rules);
  - the figure captioned **"VP1002 Banks in NFVI1369 Package"** — the bank diagram. It carries the
    `[L]` / `[RS]` transceiver **power-supply-group** tag per quad, and the `(RCAL)` marker on the
    quad that owns each calibration pair. Nothing else states which supply group serves a given
    quad, and this is what makes step 13's question answerable.

  Record the caption, edition and page for each in the code that uses it. This document really does
  renumber: the mechanical figure was Figure 246 in one edition, and in a later one Figure 246 is a
  *different package's* diagram.

If a URL is dead, find the current equivalent on amd.com and tell me what you used — and say whether
you hit a moved document or an egress problem.

**3 · [HUMAN] Confirm device, package, and MPN.**
Tell me the device/package the pinout file's header identifies and its total pin count, and
confirm: **VP1002, NFVI1369, 1369 balls**. AM013 documents other VP1002 packages (SBRJ1369,
SBVJ1369, VFVF1760) and AMD's download index offers a different set again — "packages AM013
documents" and "packages AMD publishes a pinout file for" are not the same list. We are building
**only NFVI1369**; `SBVJ1369` is the confusable name, same ball count.

Also tell me **what you intend to use as the `mpn`**, per the skill's **"When no document states an
MPN"**. Neither ground-truth document contains one: the pinout header gives a device string
(`xcvp1002nfvi1369`), and a real orderable AMD part number additionally encodes speed grade and
temperature range, which are procurement decisions. Say what your proposed value does and does not
identify. **Wait for my approval.**

**4 · Parse and inventory — no component code yet.**
Write the generator's parsing stage (stdlib only), following the skill's
**`references/pin-file-generation.md`**: whitespace-split the 7-column rows, decode every ball
reference to zero-indexed `(row, col)` with a round-trip self-check, and **reconcile: row count ==
the file's "Total Number of Pins" footer == 1369, unique balls, full 37×37 grid**. Classify names:
repeated → rail lists; unique → scalar ports.

Print an inventory table (group → ball count → kind) whose groups **partition** the balls — every
ball in exactly one group — summing to 1369, plus the GTM quad roster. The overlap to resolve here
is `VCCO_<bank>`, which is both a rail and a member of its bank: count it once. Exclude each bank's
own VCCO rail from the bank row (so bank 500 shows 26 of its 28) and say that's what you did.

If it doesn't reconcile, show me the gap — don't guess your way to 1369.

**5 · [HUMAN] Approve the inventory.**
Show me the partitioned inventory table and the reconciliation line. I'm checking: total is 1369;
GND is 689; NC is 60; **31 supply rails**; six GTM quads (banks 202–207); banks {103, 105, 109,
500–503, 700–702}. **Wait for my approval** before any code is emitted.

**6 · Emit the component.**
Extend the generator to emit `xcvp1002.py`, per the skill's **"What the emitted module holds"**:
scalar `Port()` per unique pin (grouped by bank with section comments), indexed lists per rail,
`ball_assignments()` yielding every (port, coordinate) pair with the ball reference as a trailing
comment, coordinate tables under `# fmt: off`, the structural `gtm_quad_pins()` dict,
`symbol_partitions()`, and a header recording the source file name, its sha256, and the AMD URLs.
**Mark the 60 NC balls `no_connect()`** — they are open per AMD, and an ordinary `Port()` makes that
indistinguishable from a board designer forgetting to wire them. Output must be deterministic and
`ruff format`-stable per the skill's rule for emitted collections, with a `--check` mode that
regenerates and diffs. Run the generator; commit the generated module.

**7 · Build the land pattern — read the drawing, then the fine print.**
From the figure captioned **"Package Dimensions for NFVI1369"** take body 35×35 mm, height
3.43/3.63/3.83, pitch 0.92, matrix 37. Now the trap: that same figure gives the **physical ball**
Øb = 0.50/0.64/0.70 mm, but the JITX BGA generator's `ball_diameter` argument sets the **copper land
diameter** of the PCB pad. Open the jitxlib BGA generator source and confirm what the parameter
drives, then take the land from the table captioned **"BGA Package Design Rules"** (0.92 mm pitch →
**0.51 mm** max PCB solder land, NSMD). State in a comment where each number came from, caption
first. Build `landpattern.py` with a `VersalBGA(BGA)` subclass adding the public `get_pad(row,
column)` adapter per the skill's BGA notes — both arguments zero-indexed, matching the coordinates
the generated module carries, so ball A1 is `get_pad(0, 0)` and the framework's 1-based column
offset lives inside the adapter rather than at every call site.

**8 · Partition the symbols.**
1369 pins is ~34× past the ~40-pin single-box threshold, so follow the skill's **Multi-Unit
Symbols** guidance for parts at this scale. This part's partition: one box per IO bank (signals
split left/right, `VCCO_<bank>` down), one per GT quad (RX left, TX + REFCLK right, bias pins down),
one for the dedicated/analog singletons, rails chunked at the **64-pin ceiling** (GND → 11 chunks).
`build_symbols` turns partitions into `BoxSymbol`s; the design puts each on its own schematic page
via `SchematicGroup`.

**9 · Verify the component.**
Write the tests per the skill's **"Testing a generated component"**, with this task's literals: 1369
ports == assignments == pads, the per-rail counts from your step-4 inventory, ~10 hand-read spot
checks spanning `A1`, `AU37`, a double-letter row and one pin per bank type. Then: `pyright` →
`pytest` → `jitx build <non-test symbol-viewer design target>` (expect `status: ok`) → run the
`jitx-code-review` skill and fix findings. Commit when green.

**10 · [HUMAN] Spot-check the balls.**
Show me, side by side with the pinout file: the corners **A1** and **AU37** (both GND); one ball
per bank type (a GTM lane, a GTY refclk, a PMC_MIO, an LPD_MIO, an XPIO pin); both sysmon pairs
(VP/VN_500, VREFP/VREFN_500); and two GNDs from opposite corners — each as
ball → `(row, col)` → port → pad. Also show the geometry cross-check: the A1↔AU37 pad centers
must be 36 × 0.92 = **33.12 mm** apart on both axes (the drawing's D1/E1). **Wait for my approval.**

**11 · Wrap the circuit.**
Drive the circuit-builder skill. Create `bundles.py` (`GTMQuad`: 4 × `LanePair` + 2 × REFCLK
`DiffPair`) and `circuit.py` (`XCVP1002Circuit`): one `Power()` port per supply rail from your
step-4 inventory — **no rail invented, none dropped**; a `rail_ties()` roster method; three ground
domains (main GND takes all 689 GND + 2 RSVDGND + every main rail's `Vn`; `GND_SMON` and
`GND_SENSE` take only their dedicated ball + their rail's `Vn`); sysmon inputs and the six GT
bias pins as pass-through boundary ports; `self.gtm: dict[int, GTMQuad]` wired lane-for-lane
with `>>` against the generated `gtm_quad_pins()`.

Walk the base skill's **MCU / FPGA Components** power-domain checklist here — it owns the general
rules. Where this part instantiates them:

- **31 rails, not 27.** `VCCINT_SENSE`, `VCCAUX_SMON`, `VCC_BATT` and `VCC_FUSE` get one ball each,
  so they land as scalar ports rather than rail lists. Two of the four carry the returns that
  *define* `GND_SMON` and `GND_SENSE`, so a roster built by walking the rail lists both undercounts
  and silently collapses the three-ground requirement.
- **The six GT bias pins live in banks 109, 203 and 105** — 109 carries its pair and **no lanes at
  all**. They serve whole supply groups, so keep them out of `GTMQuad`: model them per-quad and four
  of the six quads have none.
- **The `_L` / `_RS` group tags come from the bank diagram**, not the pin file — including which
  groups have no bonded quad in this package.

And name the boundary rail ports distinctly from the net names (`pwr_vccint`, not `VCCINT`) — a
named net colliding with a public port name fails only in the full runtime build ("Public name
already in use"); `jitx build --dry` cannot see it.

**12 · Verify the circuit.**
Extend the tests (rail roster + sizes, ground-domain separation, 6 quads × 20 topology links,
circuit design translates), then `pyright` → `pytest` → `jitx build <non-test circuit design target>` →
`jitx-code-review`. Commit when green.

**13 · [HUMAN] Close the loop.**
The wrapper is what a board design consumes; show me. **Invite me to ask for something** —
suggest I say: *"give me GTM quad 205 as a 4-lane bundle and tell me which power rails and bias
pins it needs."* **Wait for me to ask.** Answer from the built circuit (bundle port, rail ties,
bias pass-throughs), then open the schematic viewer (`jitx ui open --schematic`) on the bank-205
page so I can see the quad.

**This answer goes through a gate like every other step.** State which document each claim comes
from; anything not derivable from the built design or the step-2 documents, say so rather than
asserting it. The bundle half of that question is answerable from the design; the **rails half is
not** — it needs the bank diagram's supply-group tag, which is why step 2 fetches it. An answer
assembled from ball proximity or from a matching name suffix can be right here and wrong on the next
package, and it reaches me looking exactly like a verified one.

---

## Done when

- A fresh project builds, with `.context/` gitignored and no AMD files committed; the generated
  module records the pinout file's sha256 and URLs.
- The generator reconciles 1369/1369 with a printed inventory whose groups **partition** the balls,
  emits deterministically, and its `--check` mode passes against the committed module.
- Every ball has exactly one `Port` (scalar or indexed rail list), the 60 NC balls are
  `no_connect()`, and the land pattern uses the *Package Dimensions for NFVI1369* body dimensions
  with the **BGA Package Design Rules land diameter** (not the physical ball) — each cited by
  caption, edition and page.
- Symbols cover all 1369 pins, one partition each, none over 64; each bank/quad has its own box.
- `XCVP1002Circuit` exposes **all 31** supply rails as `Power` ports — including the four
  single-ball ones — with three distinct ground domains, and all six GTM quads as bundles wired
  through the structural pin groupings; zero `getattr` anywhere.
- `pyright` clean with no suppressions, `pytest` green — with the regeneration-idempotency test
  confirmed to have *run*, not skipped — both non-test designs `jitx build` with `status: ok`, and a
  `jitx-code-review` pass has run with findings fixed.
- The component carries the skill's filled **Component completeness check** block, written next to
  the code, with the agreed `mpn` and what it identifies recorded in its `Identity` row.
- A live prompted request (e.g. GTM quad 205's bundle + rails) is answered from the built design,
  with a source named for every claim not in it.

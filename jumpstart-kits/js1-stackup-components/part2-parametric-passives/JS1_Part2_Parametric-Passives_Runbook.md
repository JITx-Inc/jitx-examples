<!--
JITX Parametric Component Families Runbook (JS1 · Part 2)
Paste this file into your AI coding agent (Claude Code, Codex / GPT, or Devin), or upload it,
and tell the agent to follow it. Complete the JS0 Setup Runbook first — this runbook assumes
an authenticated jitx CLI and the JITX skills are already enabled.
-->

# JITX Parametric Component Families Runbook (JS1 · Part 2)

**Goal (for the agent):** In a fresh JITX Python project, build four **parameterized, datasheet-driven component families** — three SMD chip-resistor families (**Yageo RC_L**, **Panasonic ERJ**, **Vishay CRCW**) and one MLCC capacitor family (**Samsung Electro-Mechanics CL**). Each family is a single `jitx.Component` class that stands in for the manufacturer's whole catalog family, with **no parts database or online query** — the class *is* the data. Follow the steps **in order**; a family is not done until it passes its tests and `jitx build <non-test design target>`. Where a step is marked **[HUMAN]**, stop and wait for me — do not proceed until I confirm.

> **For humans:** prerequisites are a completed **JS0** (authenticated `jitx` CLI on 4.2.2+, `jitx-skills` enabled in your agent) and network access to the manufacturer datasheet URLs in step 2.

**Assumptions / prerequisites**

- JS0 is complete: `jitx --version` is 4.2.2 or newer and `jitx auth show` confirms authentication.
- Python 3.12+ and `git` are available; the agent can run shell commands and fetch PDFs.
- `pip install pymupdf` is available for datasheet page extraction (the component-modeler skill uses it).

---

## Starting instructions — the pattern you are building

These are the instructions this task executes. Read them before step 0; every family in steps 3–7 is verified against them. The generic pattern lives in the component-modeler skill and the steps below delegate to it by section name — read those sections when a step names one, rather than working from the summary here.

### The recipe

1. Build several scalable, **parameterized** SMD resistor models that let a user bypass online parts databases for common chip resistors, and demonstrate Python component generalizability.
2. Use the JITX component-modeling skill with the manufacturer **PDF datasheets**; start with the most flexible family (Yageo RC_L).
3. Add the next family (Panasonic ERJ) — download its datasheet.
4. Add another family (Vishay CRCW).
5. Extend the pattern across component types with an MLCC capacitor family (Samsung CL).
6. Run the **`jitx-code-review`** self-critique skill on the code, and commit locally after each family lands verified.
7. Confirm any sizes flagged "unavailable" against JITX's full standard chip-size table — don't trust a label mismatch. If the geometry is confirmed *absent*, export the size and the reason rather than dropping it silently.
8. **Enable the full size range** once the geometry is confirmed present.

### What this task supplies

The component-modeler skill carries the pattern — **Parameterized Component Families** and
**Two-Terminal Chip Components**, plus `references/parameterized-families.md` for the class shape.
Drive it; don't re-derive it. What is specific to *this* task:

- **Four families, in this order:** Yageo RC_L, Panasonic ERJ, Vishay CRCW, Samsung CL (MLCC).
  Three resistor vendors, three encoders — which is the point of doing three:

  | Vendor | Value encoding | Example |
  | --- | --- | --- |
  | Yageo | RKM (resistor letter-code notation, letter marks the decimal) | `100K` |
  | Panasonic | 3-digit EIA (two significant digits + decade multiplier) | `103` |
  | Vishay | RKM, fixed 4-character | `10K0` |
  | Samsung | 3-digit pF code | `104` = 100 nF |

- **The MPN each family cross-checks against**, per the skill's test shape:
  `RC0402JR-07100KL`, `ERJ3GEYJ102V`, `CRCW0603562RFKEA`, `CL10B104KB8NNNC`.

- **Where the shared helpers land:** extracted at family 2 into `chip_resistor.py`, renamed
  `chip_smt.py` at family 4 when the capacitor proves they were never resistor-specific. The skill
  says extract at the second consumer and name the module for what it is; the step numbers are this
  task's schedule for it.

- **The seating-plane band, per vendor**, since the skill tells you to find it but not where it is
  in these four documents: Yageo `I2`, Panasonic `b`, Vishay `T1`. Cross-check numerically — the
  right choice agrees across all three (0402: 0.25 mm; 0201: 0.15 mm).

- **E-series grades reachable here:** E24 at ±5 %, E96 for anything tighter, and nothing else. None
  of these four datasheets offers ±2 %, so no E48 caller exists; the tightest grade in the set is
  Yageo's ±0.1 %, which Yageo's own datasheet puts on E24/E96, so no E192 caller either.

- **Datasheets: link the URL, don't commit the PDF** — PDFs live in the gitignored `.context/`.

### Verify (every family, before it counts as done)

```bash
pyright                 # expect zero errors and zero suppressions
pytest                  # the family's tests (plus all earlier families' tests)
jitx build <non-test design target>  # build the intended design, never a target from tests/
```

A `pyright: ignore` you feel you need is a finding to report, not a way to reach zero. Run the
`jitx-code-review` self-critique skill before the final commit — on this pattern it has caught
value-encoder carry bugs that happy-path tests missed.

---

## Steps

**0 · Preflight.**
Run `jitx --version` (expect **4.2.2+**) and `jitx auth show` (expect authenticated). Confirm the JITX skills are invocable in this session — the one this task drives is the **component modeler**:

- **Claude Code** — the `jitx-skills` plugin is installed; invoke with `/jitx-skills:jitx-component-modeler`.
- **Codex / GPT** — invoke with `$jitx-component-modeler <request>`. Name the sub-skill rather than relying on `$jitx` to route to it.
- **Devin** — invoke with `@jitx-component-modeler <request>`.

If any check fails, **stop** and tell me to re-run the JS0 Setup Runbook first — do not continue.

**1 · Scaffold a fresh project.**
Create a new project directory and run `jitx project layout init` (seeds a two-resistor `SampleDesign`), then set up the project environment inside it:

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

Build the seeded non-test target from `jitx find` — ignore any target whose module path comes from `test`, `tests`, or a test file. **Take the target verbatim from `jitx find`** — the scaffold names the seeded design class after the project directory, lowercased with hyphens and spaces turned into underscores, so a directory called `js1-passives` builds as `jitx build js1_passives.main.js1_passives`. This smoke test must succeed before you write any component code. If it fails, stop and tell me. Then prepare the project for this task: create a `tests/` directory; add `pytest` and `pyright` as dev dependencies if the scaffold didn't seed them; ensure `.context/` is gitignored; `git init` + initial commit if the scaffold didn't.

**2 · Fetch the datasheets.**
Download all four manufacturer datasheets into `.context/` (gitignored — **link the URL in each family's docstring, never commit the PDF**):

- **Yageo RC_L** — https://yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L (the RC_L series datasheet, all sizes 0075–2512).
- **Panasonic ERJ** — https://industrial.panasonic.com/cdbs/www-data/pdf/RDA0000/AOA0000C301.pdf
- **Vishay CRCW** — https://www.vishay.com/docs/20035/dcrcwe3.pdf
- **Samsung CL (MLCC)** — the Samsung Electro-Mechanics MLCC catalog PDF: https://product.samsungsem.com/resources/file/product-catalog/MLCC_2512.pdf (the filename is dated per revision — if it has moved, get the newest MLCC catalog from https://product.samsungsem.com/product-catalog.do). It contains the part-numbering scheme, case-size dimension tables, and the dielectric/voltage lineup.

Per the skill's **"Verify the download is a datasheet"**: these four URLs are canonical, so if one doesn't answer, say whether you hit an egress problem or a moved document, and tell me which URL you ended up using.

**3 · Family 1 — Yageo RC_L.**
Drive the component-modeler skill with the Yageo datasheet to build `yageo_rc.py`, following its **Parameterized Component Families** and **Two-Terminal Chip Components** sections. Values encode in Yageo's RKM style (`100K`). Keep this family **self-contained in one file — no shared helpers yet**. Write `tests/test_yageo_rc.py` per the skill's **"Verifying a component with tests"**, cross-checking the datasheet's own ordering example **`RC0402JR-07100KL`**. Verify: `pyright` → `pytest` → `jitx build <non-test design target>`. Commit when green.

**4 · [HUMAN] Verify Family 1 together.**
Stop and walk me through the family against the datasheet before replicating the pattern. Show me: (a) two or three transcribed dimensions side-by-side with the datasheet table, **including which of the two printed termination bands you used and why**; (b) the encoder reproducing the ordering-example MPN and a decade-carry case (`9999 → "10K"`); (c) a fail-fast rejection listing the valid options — run this demo **inside the instantiation context**, since a plain script raises nothing; (d) how each vendor size label maps to the generator's size key by body L×W — including the label mismatch (Yageo `0075` → `009005`); (e) the skill's filled **Component completeness check** block. **Wait for my approval** before continuing.

**5 · Family 2 — Panasonic ERJ.**
Build `panasonic_erj.py` from the Panasonic datasheet: 3-digit EIA value code (`103`), its own tables and MPN f-string. This is the second consumer, so per the skill's **"Shared helpers — extract at the second family"**, extract them now into `chip_resistor.py` and refactor Family 1 onto them — Family 1's unchanged tests passing proves the refactor safe. Write `tests/test_panasonic_erj.py`, cross-checking **`ERJ3GEYJ102V`**. Verify: `pyright` → `pytest` (all families) → `jitx build <non-test design target>`. Commit when green.

**6 · Family 3 — Vishay CRCW.**
Build `vishay_crcw.py` on the shared helpers: fixed 4-character RKM value code (`10K0`). This datasheet specifies its cases by standard EIA/IEC size code (`RR1608M` = 1.6 × 0.8 mm for 0603), so prefer the generator's standard chip dimensions — and doc 20035 **p. 11** (`DIMENSIONS AND MASS`) tabulates them too, so the skill's **"Taking the standard table's dimensions is a verification obligation"** applies in full: read p. 11 and assert the table against it per size. Write `tests/test_vishay_crcw.py`, cross-checking **`CRCW0603562RFKEA`**. Verify: `pyright` → `pytest` → `jitx build <non-test design target>`. Commit when green.

**7 · Family 4 — Samsung CL (MLCC).**
Build `samsung_cl.py` — the same pattern with two new axes, **dielectric** (C0G/NP0, X7R, X5R as offered per size/voltage) and **rated voltage**, a 3-digit pF value code, `CapacitorSymbol`, and `reference_designator_prefix = "C"`. Cross-check against the real catalog part **`CL10B104KB8NNNC`**. The linked catalog is the overview edition and may publish no per-size capacitance lineup — the skill's **"When the catalog does not publish what you need, say so"** covers that case; don't invent ranges. The shared file now serves a non-resistor part, so rename `chip_resistor.py` → `chip_smt.py`, update all imports, and re-run the **full** suite. Write `tests/test_samsung_cl.py`. Verify: `pyright` → `pytest` → `jitx build <non-test design target>`. Commit when green.

**8 · Full verification pass.**
Create a small combined `SampleDesign` that instantiates one part from **each of the four families** and confirm `jitx build <non-test design target>` passes on it. Run `pyright` and the full `pytest` suite, plus the project's lint/format check if the scaffold seeded one. Then run the **`jitx-code-review`** self-critique skill over the four family files and the shared helpers, fix what it finds, re-run the tests, and commit. Report the results of all checks to me.

A good result is: `pyright` reports zero errors and no suppressions, the full `pytest` suite is green including every family's datasheet cross-check, `jitx build <non-test design target>` completes on the combined design, `jitx-code-review` returns no unresolved findings, and each family has its **Component completeness check** block filled in, written next to the code.

**9 · [HUMAN] Close the loop — request a part.**
The library is done; now show me what it's for. **Invite me to ask for an arbitrary part** — suggest I say: *"give me a 49.9 kΩ 0402 1% Yageo and a 100 nF X7R 0603 50 V Samsung CL."* **Wait for me to ask.** When I do, instantiate the requested parts from the family classes in the combined design, rebuild, and show me the schematic/board plus the **generated MPNs**, so I can spot-check them against the datasheets' part-numbering schemes.

This step writes code, so it goes through step 8's gate like every other step — finish with the full verification block (`pyright` → `pytest` → `jitx build <non-test design target>` → `jitx-code-review`). Don't let the last code written be the only code that skipped the review. Print the BOM as well as the MPNs: value labels are the one thing none of those four commands checks.

---

## Done when

- A fresh project scaffolded with `jitx project layout init` builds, with `.context/` gitignored and no datasheet PDFs committed.
- Four family classes exist — `yageo_rc.py`, `panasonic_erj.py`, `vishay_crcw.py`, `samsung_cl.py` — each with a passing `jitx.test.TestCase` file covering: build in a `SampleDesign`, metadata + pad count, the datasheet ordering-example MPN cross-check, the human-readable value label, value-encoder units (incl. decade carry), and fail-fast validation.
- Wherever a family took the generator's standard chip dimensions, a test asserts that table against the datasheet's own, per size, with any disagreement overridden and commented.
- Shared helpers were extracted **at Family 2** (not before) and renamed component-agnostic **at Family 4**, with the full suite green after each refactor.
- `pyright` is clean with no suppressions, the full `pytest` suite passes, and the combined four-family design passes `jitx build <non-test design target>`.
- Each family carries the skill's filled **Component completeness check** block, written next to the code.
- A `jitx-code-review` pass has run and its findings are fixed.
- A live prompted part request (e.g. 49.9 kΩ 0402 1% Yageo + 100 nF X7R 0603 50 V Samsung CL) instantiates, builds, and its generated MPNs check out against the datasheets.

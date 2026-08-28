<!--
JITX Stackup-from-Fab-CSV Runbook (JS1 · Part 1) · rev 1.1 · 2026-08-27
Paste this file into your AI coding agent (Claude Code, Codex / GPT, or Devin), or upload it,
together with your stackup CSV, and tell the agent to follow it. Complete the JS0 Setup Runbook
first — this runbook assumes an authenticated jitx CLI and the JITX skills are already enabled.
START A NEW AGENT SESSION before you begin. A skills install only takes effect in a session
started after it, so the session that finished JS0 cannot run this runbook.
-->

# JITX Stackup-from-Fab-CSV Runbook (JS1 · Part 1)

**Goal (for the agent):** Turn a fabrication house's stackup report into a verified JITX substrate in a file called `board.py` — a 20-layer HDI stack, five microvia levels per side, impedance-controlled routing structures. The user-provided documentation (e.g. CSV) is the **only** ground truth: every material, thickness, via and trace width must trace to one of its rows. Estimate nothing: if the CSV doesn't state it and the substrate-modeler skill doesn't supply a labeled default for it, ask me. Follow the steps **in order**. Where a step is marked **[HUMAN]**, stop and wait for me — do not proceed until I confirm.

> **For humans:** you need a completed **JS0** (authenticated `jitx` CLI on 4.4.0+, `jitx-skills` enabled) and a stackup CSV — `part1-stackup/JS1_Part1_Fab-Stackup.csv` from this kit, or your own fab's export. Reference solution: `pip install jitxexamples`, then [`jitxexamples.jumpstart_kits.js1_stackup_components.hdi_stackup`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js1_stackup_components/hdi_stackup) — a bare `import jitxexamples` succeeds without it, so check the full path.

**Assumptions / prerequisites**

- JS0 is complete: `jitx --version` is 4.4.0 or newer and `jitx auth show` confirms authentication.
- Python 3.12+ and `git` are available; the agent can run shell commands.
- The stackup CSV is in the project directory, or pasted into this session.

---

## Steps

**0 · Preflight.**
Read this runbook's revision out of the HTML comment at the top of the file and tell me what it is, so the run is pinned to a known version of the kit. Then run `jitx --version` (expect **4.4.0+**) and `jitx auth show` (expect authenticated). Confirm the JITX skills are invocable — the one this task drives is the **substrate modeler**:

- **Claude Code** — the `jitx-skills` plugin is installed; invoke with `/jitx-skills:jitx-substrate-modeler`.
- **Codex / GPT** — invoke with `$jitx-substrate-modeler <request>`. Name the sub-skill rather than relying on `$jitx` to route to it.
- **Devin** — invoke with `@jitx-substrate-modeler <request>`.

If any check fails, **stop** and tell me to re-run the JS0 Setup Runbook first.

**1 · Scaffold a project.**
Run `jitx project layout init`, then set up the project environment inside it:

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

Build the seeded non-test target from `jitx find` — ignore any target whose module path comes from `test`, `tests`, or a test file. **Take the target verbatim from `jitx find`.** The scaffold names the seeded design class after the project directory, lowercased with hyphens and spaces turned into underscores, so a directory called `js1-hdi-stackup` builds as `jitx build js1_hdi_stackup.main.js1_hdi_stackup`. This smoke test must succeed before you write any code of your own. If it fails, stop and tell me; do not start on the stackup. Then create `tests/`, add `pytest` and `pyright`, and `git init` if you want version control. Leave the seeded `.gitignore` as it is.

**2 · Read the report before writing any code.**
Parse the CSV and **restate it back to me** per the skill's Source Documents rules; flag whatever is ambiguous.

**3 · Materials and stackup.**
Drive the substrate modeling skill to transcribe the MATERIALS and STACKUP sections, following its **fab-CSV schema** and **"Choosing Symmetric vs explicit Stackup"** — the stackup is explicit, every copper layer named for its CSV layer id and function. A stated value with no JITX field goes in a docstring, and if you can't say where a column landed, tell me rather than dropping it.

**4 · [HUMAN] Verify the stackup against the report.**
Write the materials and the stackup, and **stop there** — vias and routing structures wait for my approval, because rejecting the stackup at this gate would make you redo everything built on top of it. Show me: (a) three layer rows side by side with the CSV; (b) your thickness total, summed from the code, against the report's finished **and** overall thickness; (c) the conversion arithmetic for one copper row, oz and Rz included; (d) the **conductor-index map** for vias and routing structures; (e) the **depth basis** the report's NOTES give for each drill type, and which one you will apply to each via in step 5. **Wait for my approval.**

**5 · Fabrication rules and vias.**
Drive the skill over FAB_RULES per its fab-CSV schema — 19 mapped rows here, two of them (the panel limits) quoted in mm only — and hand-check the five capability rows against the via table per its derived-checks formulas. Two of those rows are the cases the skill warns about: every microvia lands **exactly** on the 0.80:1 ratio, and the report states two drill minimums where `min_drill_diameter` holds one. Tell me how you read each. Then the via inventory: exactly the twelve structures the report offers.

**6 · Routing structures.**
Drive the skill's **"From a fab impedance table"** pattern over the IMPEDANCE section. Eleven rows here resolve to **four** structures — the skill's schema says how the target-vs-modelled columns and the `*-UNC` row resolve; tell me the count you got and why, before you write them. Carry each row's `Ref_layers` planes with the skill's labeled reference-plane default — the report never states plane widths, and an unlabeled number sitting where it looks authoritative is the one failure this task is built to prevent. The **STANDARD** row (`Controlled = No`) is the fab's default line and space: per the skill, record it as a substrate docstring, not a structure.

**7 · Verify.**
Run `pyright` — expect **zero errors and zero suppressions**; a `pyright: ignore` you feel you need is a finding to report, not a way to reach zero. Write CSV-sourced tests per the skill's **"Verifying a Substrate Against Its Source"**.

Then `pytest`. Before you build, **wire the substrate into a design** per the skill's **"Smoke-Test Wiring (Board and Design)"** — step 1's seeded target is not acceptance here, and the skill says why. Then `jitx build <non-test design target>`, one design at a time. Read all of `jitx find`'s output, not just its design list — treat any `import failed:` line as a failure (make `tests/` a package with an `__init__.py` if your tests import shared helpers), and do not build designs discovered under `tests/`; those are pytest fixtures, not smoke-test targets. Finally run **`jitx-code-review`**, fix what it finds, re-run, and report every result to me — including the skill's filled **Substrate completeness check** block.

A good result is: `pyright` reports zero errors, `pytest` is green with every assertion sourced from the CSV, `jitx build` of the design that **binds the substrate** completes and writes its design directory, and `jitx-code-review` returns no unresolved findings. Anything short of that is a failure. Report it to me and stop; do not work around it.

**8 · [HUMAN] Close the loop — re-issue the report.**
Now show me the substrate regenerates from the report. **Invite me to change the CSV** — suggest I say: *"the fab came back on the through-hole again — 0.400 mm finished hole this time; re-issue the report and tell me what moved."* **Wait for me to ask.**

Edit the CSV only with values I give you — both unit columns for the hole, the derived columns on the same row, a Rev C history line, and the `DOCUMENT` fields the skill's re-issue rule names. Per that rule, re-derive the arithmetic over the changed row and re-run the step-5 hand checks. `Depth_mm` does **not** move — it is set by the layer span, not the hole — so the new ratio is the same depth over the new hole. Then update `board.py`, rebuild, and report before → after — including what did **not** move: no dielectric changed, so no impedance row is touched and every trace width still points at its CSV row.

**If I ask for a dielectric change instead, stop.** A dielectric change re-solves the controlled-impedance line widths, and that solve belongs to the fab — the CSV carries its result, not the model that produced it. Report the affected trace widths as blocked pending re-solved impedance rows; do not estimate them, and do not carry the old widths forward as if they still held. If I supply re-solved rows, carry them through and report before → after for every changed width.

Then close this step the way step 7 closes: `pyright`, `pytest`, a `jitx build` of the design that binds the substrate, and **`jitx-code-review`**. The code and tests you wrote here have not been through that gate — step 7's review went stale the moment you edited anything.

---

## Done when

- `board.py` holds one material class per CSV material row, an explicit `Stackup` with function-named copper layers, all 19 fabrication constraints, the report's full via inventory, and one routing structure per controlled impedance target covering both layer groups, each carrying its `Ref_layers` planes — four structures, not five.
- Summed thickness matches the report's finished and overall thickness to the last printed digit; every annular ring and aspect ratio is within its capability limit, derived on the depth basis the NOTES state for that drill type.
- No `Symmetric`, no invented SI models, and no **unlabeled** number that can't be pointed at a CSV row — reference-plane widths carry the skill's labeled default — and the STANDARD line/space recorded as prose, not as a structure.
- The step-4 gate stopped after the stackup, with vias and routing structures written only after approval.
- `pyright` clean with zero suppressions, `pytest` green from CSV-sourced tests, `jitx find` free of import errors, a design that **binds the substrate** builds, `jitx-code-review` findings fixed — run after step 8 as well as step 7 — and the skill's **Substrate completeness check** block filled in the completion report.
- A prompted CSV re-issue (the through-hole change) flows through to rebuilt code, with the aspect ratio and annular ring re-derived, re-checked against capability, and reported before → after — and the untouched impedance rows called out. A dielectric change without re-solved rows is reported as blocking the affected widths; no estimated width appears anywhere.

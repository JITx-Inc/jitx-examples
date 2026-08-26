# JITX Setup — Reference Companion (JS0)

Human-facing companion to the **JITX Setup Runbook**. Use it if you **have no AI agent** (follow the *Manual CLI* path), or you're preparing a **locked-down / enterprise machine** (see *Environment & IT readiness*).

Same commands as the runbook, resequenced for working by hand — the JITX *skills* need an agent, so you enable them last.

---

## Manual CLI path (no AI agent)

Run these in a terminal — you'll get a working, authenticated install, proven by a real build.

1. **Check prerequisites.** `python3 --version` (need 3.12+) and `git --version`; `uv --version` is optional. If Python is older than 3.12, install 3.12+ first.
2. **Install the JITX CLI.** `pip install jitx`. If you hit the PEP 668 "externally-managed-environment" error — the Python packaging rule that stops `pip` writing into a system-managed interpreter — install `uv` (https://astral.sh/uv) and run `uv tool install jitx` instead. Verify: `jitx --version` (4.2.2 or newer) — note it, the Full build below runs only on 4.2.x.
3. **Install the runtime.** `jitx runtime install` — do this **before** signing in. **On Windows**, this launches an MSI installer in a separate popup window (possibly behind others) — complete it to finish.
4. **Sign in.** `jitx auth login` opens a browser. **Sign in with Google** is simplest; if you're **not** using a Google-enabled account, enter your registered email and JITX password. Confirm with `jitx auth show`.
5. **Validate with up to two builds.** The global CLI (step 2) has no `pip`, so run this inside each project once it exists. Create and activate a virtual environment — `python3 -m venv .venv && source .venv/bin/activate` on macOS or Linux, or `py -3.12 -m venv .venv` then `.\.venv\Scripts\Activate.ps1` in Windows PowerShell — then `pip install jitx`, `jitx project dependencies upgrade`, `jitx runtime start --background`, and `jitx find`.
   - **Simplest.** Create a new project with `jitx project layout init` (this seeds a two-resistor sample design). Build the seeded non-test target from `jitx find` — ignore any target whose module path comes from `test`, `tests`, or a test file. **Take the target verbatim from `jitx find`** — the scaffold names the seeded design class after the project directory, lowercased with hyphens and spaces turned into underscores, so a directory called `my-first-board` builds as `jitx build my_first_board.main.my_first_board`. Then open the views with `jitx ui open --schematic` and `jitx ui open --board`.
   - **Full (JITX 4.2.x only).** If your `jitx --version` is 4.3+, skip this — `si_bga_optimization` still targets the 4.2 API and won't build until `jitx-examples` is updated. Otherwise clone `https://github.com/JITx-Inc/jitx-examples` and build the [`si_bga_optimization`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/demos/si_bga_optimization) design — build target `jitxexamples.demos.si_bga_optimization.bga_escape.bga_optimization_design`; open the board view to confirm.
   - **Be patient on the first view.** The very first board or schematic window can take **3–4 minutes** to appear — wait it out rather than re-running. If nothing shows after **5 minutes**, something is wrong. Later views come up much faster.
   - **`jitx ui open` holds the terminal** while its window is open — use a second terminal, or background it, for the next command. Later calls return straight away and add their windows to the JITX app already running; there's no limit on how many views can be open at once, so leave the Simplest build's windows up.
6. **(Optional) Install the editor JITX extension.** Search your editor's (or VSCode's) marketplace for the JITX extension and install it, then confirm you're authenticated in its sidebar.
7. **(Once you have an AI agent) Enable the JITX skills.** Follow the per-runtime steps in the runbook to enable them for your agent (Claude Code, Codex / GPT, or Devin). In the **Claude Code VSCode / Cursor extension** the `/plugin` command isn't available — use the `claude plugin marketplace add …` / `claude plugin install …` CLI form the runbook gives.
8. **Close the loop — change a design parameter.** With an agent, ask it to *"change the differential-pair trace width to 0.0762 mm and the pair spacing to 0.1568 mm"* on the `si_bga_optimization` design; it edits the diff-pair constants (`DIFFPAIR_TRACE_WIDTH` / `DIFFPAIR_PAIR_SPACING` in the design's `substrate.py`), rebuilds, and the board view redraws. Those two numbers are arbitrary demo values rather than an impedance target — you're watching a source edit reach the board view. No agent? Edit the constants yourself and rebuild. **Skipped the Full build?** Do it on the template instead — change a resistor's `resistance` in `main.py` (say `r2` to `10 * kohm`), rebuild, and the schematic redraws with the new value. Either way you've seen the design-as-code loop (intent → code → build → view), and you're ready for JS1.

---

## Environment & IT readiness

For machine sizing, network egress, deployment architecture, licensing models, and data handling — especially on **managed or locked-down machines** — see the [JITX Architecture and Systems Requirements](../shared/JITX_Architecture_and_Systems_Requirements_v2_0.md).

For what sits on top of that on a single engineer's machine — package and extension trust, installing the AI skills per runtime, and a consolidated **[IT/Admin]** vs **[Engineer]** readiness checklist — see [JS0 — Environment Setup](JS0_Environment_Setup.md).

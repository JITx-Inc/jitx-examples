<!--
JITX Stackup-from-Fab-CSV Runbook (JS1 · Part 1) · rev 1.9 · 2026-10-28
Give this file and your stackup CSV to your AI coding agent (Claude Code, Codex / GPT, or Devin)
and tell it to follow the file. Complete JS0 first, then START A NEW AGENT SESSION: a skills
install only takes effect in a session started after it.
-->

# JITX Stackup-from-Fab-CSV Runbook (JS1 · Part 1)

**Goal (for the agent):** turn the fab's stackup report, a CSV, into a verified JITX substrate in `board.py` by driving the `jitx-substrate-modeler` skill. The CSV is the only ground truth: where neither it nor one of the skill's labeled defaults gives a value, ask me. Don't open this kit's reference module (`jitxexamples.jumpstart_kits.js1_stackup_components.hdi_stackup`) or anything in it, even where a skill offers it as an example: it is a finished answer to this report. Follow the steps in order. At a **[HUMAN]** step, stop and wait for me.

**Prerequisites:** JS0 is done; Python 3.12+ and `git` are available; you have the CSV as a file.

## Steps

**0 · Preflight.**
Tell me this runbook's revision, from the comment at the top of the file, and confirm the `jitx-substrate-modeler` skill is invocable.

**1 · Scaffold.**
Make a new, empty directory, run `jitx project layout init` in it, copy the CSV in, and set up its environment:

```bash
# macOS / Linux
python3 -m venv .venv && source .venv/bin/activate

# Windows (PowerShell)
$env:PYTHONUTF8 = "1"; py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
```

```bash
pip install jitx pytest pyright ruff
jitx project dependencies upgrade
jitx runtime start --background
jitx design find
```

Check that `jitx --version` in the venv and the version `jitx runtime introspect` reports are on the same release line (4.6 and 4.6, say); if not, stop and tell me, because fixing it changes the runtime for the whole machine. Then build the seeded design with `jitx design build <target>`, taking the non-test target verbatim from `jitx design find`. If the build fails, stop and tell me.

**2 · Materials and stackup.**
Drive the skill over the report's MATERIALS and STACKUP sections, starting with its restatement of the report to me. Write the materials and the stackup, nothing else yet.

**3 · [HUMAN] Check the stackup against the report.**
Stop and show me: three layer rows beside their CSV rows; the thickness summed from the code against the report's finished and overall thickness; one copper row's conversion arithmetic; the conductor-index map (0 = L1, -1 = L20); and the depth basis the NOTES give for each drill type. Wait for my approval, because vias and routing structures build on this.

**4 · Fab rules, vias and routing structures.**
Drive the skill over FAB_RULES, VIAS and IMPEDANCE. Before you write the code, work out each count and why, and check it against what this report gives; if a count still differs after you go back to the data, stop and tell me. This report gives 19 mapped fab rules and 12 vias. Its 11 impedance rows give four controlled targets (SE-DEFAULT, SE-40, SE-50, DIFF-100) plus their neck structures: the three single-ended targets quote identical neck geometry, so share one neck structure among them and give DIFF-100 its own: six structures in all. Define every structure and apply none: Part 1 has no nets, so the skill's completeness check will list applying them as an open item, and that is expected.

**5 · Verify.**
Run the skill's verification: its checks, tests that read the CSV, and a build of a design that binds your substrate. Add that design as a new class beside the seeded one. Treat any `import failed:` line from `jitx design find` as a failure, and build only non-test targets. Then run `jitx-code-review`, fix every CRITICAL finding and each WARNING you can, and report every result to me, with the reason for each WARNING you keep and the skill's completeness check filled in. If any **Done when** line that applies so far fails, report it and stop.

**6 · [HUMAN] Re-issue the report.**
Invite me to change the CSV, and suggest I say: *"the fab came back on the through-hole again: 0.400 mm finished hole this time. Re-issue the report and tell me what moved."* Wait for me to ask.

Edit the CSV only with values I give you, plus what a revision moves with them: the changed row's other unit column and derived columns, a Rev C line in REVISION_HISTORY, and the DOCUMENT `Revision` row (with its note naming the revision it supersedes) and `Issue date`, both dated the day you issue it. Keep the filename and each column's printed precision. `Depth_mm` does not move, because the layer span sets it, not the hole. Then update `board.py`, run step 5 again in full, and report before and after, including what did not move.

If I ask for a dielectric change instead, stop. New dielectrics need line widths the fab re-solves; report the affected widths as blocked until I supply re-solved impedance rows, and never estimate them.

If a build stops on a question from the runtime (*"Significant changes detected… Do you want to continue?"*), ends in `status: error` with `EOF when reading a line`, or runs far longer than your earlier builds with no output, stop and tell me exactly what it printed. Only I can answer the question, in the JITX UI or in my own terminal: never answer it from your shell or set anything to skip it. Stop your build before I rebuild in my terminal, and when I say it is answered, rebuild and carry on from where the build stopped.

## Done when

- `board.py` holds one material class per CSV material row, an explicit `Stackup` with each copper layer named for its CSV layer and function, all 19 `FabricationConstraints` fields, the report's 12 vias, and the four target routing structures with their neck structures and DIFF-100-UNC as DIFF-100's uncoupled region, each layer entry carrying its `Ref_layers` planes.
- The summed thickness matches the report's finished and overall thickness to the last printed digit, and every annular ring and aspect ratio is within its limit on the depth basis the NOTES state.
- Every value traces to a CSV row or to one of the skill's labeled defaults.
- Step 3 stopped before vias and routing structures were written.
- The skill's checks pass, `pyright` among them with zero suppressions; `pytest` is green with tests that read the CSV from its file; `jitx design find` shows no import failures, a design binding the substrate builds, and `jitx-code-review` leaves no CRITICAL finding (every result reported, with the reason for each WARNING kept), after step 5 and again after step 6.
- The through-hole re-issue flows through to rebuilt code, with aspect ratio and annular ring re-derived and reported before and after.

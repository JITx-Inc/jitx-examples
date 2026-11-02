# JS1 Part 1 — Stackup

**Shortcut:** {download}`Download the runbook <JS1_Part1_Stackup-from-Fab-CSV_Runbook.md>`, give it
and [the supplied fab CSV](JS1_Part1_Fab-Stackup.csv) to your AI coding agent, and tell it to follow
the file.

Turn a fab's stackup report into a verified 20-layer HDI substrate by driving
`jitx-substrate-modeler`. The supplied report is ACME quote Q26-0417 Rev B: 20 layers, 5-10-5 HDI,
a 0.80 mm core and four impedance targets. Every number in the substrate traces to a row of that
report or to one of the skill's labeled defaults, and tests re-read the report to check the
substrate against it. What you learn is how to model a fab's stackup report as code, so the
stackup, vias, routing structures and fab rules your designs use come from one source, and a
re-issued report becomes a change the tests check.

## Before you start

- Finish [JS0](../../js0-setup/).
- Start a new agent session for this part. A skills install only takes effect in a session started
  after it.
- Download the runbook and the CSV, both linked below.
- Allow about 20 minutes.
- To compare this run with your current flow afterward, note now roughly how long turning a fab's
  stackup report into your design's stackup and rules takes your team, what tends to go wrong, and
  how long a re-issued report takes to carry into your stackup and rules, before any design picks it
  up. During the run, time it, time gate 2 from your request to the agent's report, and note
  anything the checks caught.

## What the agent asks of you

Two `[HUMAN]` gates stop for you:

1. **Check the stackup.** The agent shows you layer rows beside the CSV, its summed thickness
   against the report's, how it numbers the copper layers, and which depth each drill's aspect ratio
   is measured on. Approve, or say what is wrong, before it builds vias and routing structures on
   top.
2. **Re-issue the report.** Ask for a change to the CSV (the runbook suggests a larger
   through-hole) and the agent carries it through the code, the tests and the build, then tells
   you what moved and what did not. A dielectric change stops instead, until the fab re-solves the
   line widths.

## After the run

You can now model a substrate from a fab's stackup report and carry a re-issued report through the
code, the tests and the build. Gate 2's change stops at the substrate, which no design has parts or
nets on yet, so set its time against carrying a re-issued report into your stackup and rules before
any design picks it up; that comparison counts for more than the whole run's time against your note,
since a first run includes learning. Set anything the checks caught beside what tends to go wrong in
your flow. Then model your own fab's stackup report the same way and time it against the same note:
that second run is the fairer measure.

## Files

- [The runbook](JS1_Part1_Stackup-from-Fab-CSV_Runbook.md), to read here;
  {download}`download it <JS1_Part1_Stackup-from-Fab-CSV_Runbook.md>` to give to your agent.
- [JS1_Part1_Fab-Stackup.csv](JS1_Part1_Fab-Stackup.csv), the report the substrate is built and
  verified against. ACME Circuit Technology is fictional; the laminates and copper foils are real.
- The reference solution, module
  [`jitxexamples.jumpstart_kits.js1_stackup_components.hdi_stackup`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js1_stackup_components/hdi_stackup)
  in the `jitxexamples` package (`pip install jitxexamples`).

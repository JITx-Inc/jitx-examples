# JS4 Part 1 — Fanout and Escape

**Shortcut:** {download}`Download the runbook <JS4_Part1_Fanout-Escape_Runbook.md>`, give it to
your AI coding agent, and tell it to follow the file.

Lay out the start of a board in code by prompting an agent that drives `jitx-circuit-builder`,
`jitx-code-layout` and `jitx-layout-constraints`. Starting from a supplied design where the JS1
VP1002 FPGA and a Micron MT53E1G32D2FW LPDDR4 memory are connected and only the FPGA is placed, you
give the agent your placement, via and routing strategy and it places the memory below the FPGA,
puts a via in the pad of every FPGA ball but its NC balls, and every memory ball but NC and DNU (the
board leaves NC balls unconnected, so no later part needs them) and a ground pour on every ground
layer, and escapes channel B's two strobe pairs, the ones Part 4 will route, out of both parts' ball
fields at the positions a reference layout of those lanes gives. Each part's vias and escapes sit in
the part's circuit, so moving that circuit moves them with it; moving the part alone after its vias
are placed leaves them behind. The decoupling capacitors and the ZQ, IO_VR and RREF resistors stay
unplaced in this part, and the FPGA's decoupling leaves out the 27 capacitors that would connect to
nothing on this board: on the rails Part 2 does not pour, each one of 10 uF and up and each smaller
one with no free ball pair in the field, since Part 2 joins capacitors of those kinds to a pour and
these rails get none. 59 capacitors remain. The counts in the runbook and JITX's issues report check
the result. The board uses an 18-layer reference stackup that ships in `jitxexamples`, built from
the fabrication drawing of a production FPGA evaluation board.

What you learn is how to state a layout strategy as precise rules that code applies to every ball
they name, so the fanout is correct and consistent across both parts: the strategy is written once,
applied to all 1,492 fanout vias, and changed in one place. The Essentials page [Kinematic
Tree](https://docs.jitx.com/en/latest/essentials/physical_design/kinematic-tree.html) covers
placement in code.

## Before you start

- Finish [JS0](../../js0-setup/) and [JS1 Part 2](../../js1-stackup-components/part2-versal-fpga/),
  where the VP1002 comes from.
- Start a new agent session. A skills install only takes effect in a session started after it.
- Allow about two hours of agent time, an estimate since this part has not been timed, plus the
  time you spend at the checks below. Your agent needs network access to github.com.
- If you want to compare this run with how your team does the same work today, time it.

## What the agent asks of you

Two `[HUMAN]` gates stop for you:

1. **Check the fanout.** The agent shows you the fanout vias by part and the pours by layer, as
   its capture of the built design counts them, against the runbook's counts. Then it opens the
   board view and tells you where to look to see a through via, a pour layer and the two escapes
   leaving each part's ball field. You confirm before it runs its checks.
2. **Change the strategy.** The agent invites you to change one part of the via and routing strategy
   and suggests using the 10 mil through via for the FPGA's GND balls. It changes only what you
   name, rebuilds, and reports the fanout vias by type and part.

## After the run

You can now give an agent a fanout strategy for a dense board and get it applied, in code, to
every ball it names. Part 4's reference routes continue in code from the `PairPoint`s placed here;
whether interactive routing in the board editor continues from one is unverified. Then give the same
kind of strategy for a BGA on one of your own boards.

## Files

- [The runbook](JS4_Part1_Fanout-Escape_Runbook.md), to read here;
  {download}`download it <JS4_Part1_Fanout-Escape_Runbook.md>` to give to your agent.
- The design this part starts from, module
  [`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.base`](https://github.com/JITx-Inc/jitx-examples/blob/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4/base.py)
  in the `jitxexamples` package.
- The escape positions, from a reference layout of channel B's two byte lanes, module
  [`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.reference_escapes`](https://github.com/JITx-Inc/jitx-examples/blob/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4/reference_escapes.py)
  in the `jitxexamples` package.
- The reference solution, module
  [`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part1_fanout_escape`](https://github.com/JITx-Inc/jitx-examples/blob/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4/part1_fanout_escape.py)
  in the `jitxexamples` package. A project that builds it sets up a parts chain as the repository
  README's [Parts configuration](https://github.com/JITx-Inc/jitx-examples#parts-configuration)
  section says.

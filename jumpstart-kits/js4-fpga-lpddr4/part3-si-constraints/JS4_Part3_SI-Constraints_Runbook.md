<!--
JITX SI Constraints Runbook (JS4 · Part 3) · rev 2.4 · 2026-11-12
Give this file to your AI coding agent (Claude Code, Codex / GPT, or Devin) and tell it to follow
the file. Complete JS0 and JS1 Part 2 first, then START A NEW AGENT SESSION: a skills install only
takes effect in a session started after it.
-->

# JITX SI Constraints Runbook (JS4 · Part 3)

Each step below is a request, written the way you would ask an agent for the work. Follow them in
order; at a **[HUMAN]** step, stop and wait for me. Drive `jitx-interconnect-constraints` for the
constraints, `jitx-layout-constraints` for the spacing rules and the base `jitx` skill for the
project. The ground truth is AMD UG863, *Versal
Adaptive SoC PCB Design User Guide*, its LPDDR4/4x rules:
<https://docs.amd.com/r/en-US/ug863-versal-pcb-design>. Cite its revision. If you can't read it,
tell me what you tried. Where it leaves a choice, make it and tell me what you chose. Don't open
`jitxexamples.jumpstart_kits.js4_fpga_lpddr4` other than its `base` and `ball_field` modules,
even where a skill offers it as an example: it holds a finished answer to this task. Build on
`part2_power`'s `JS4PowerCircuit` and `JS4PowerDesign` without reading that module.

**Prerequisites:** JS0 and JS1 Part 2 are done; Python 3.12+; you can fetch from amd.com and
github.com.

Every part, and the board, comes from the `jitxexamples` package. Model none, and leave the FPGA's
pin offer, the substrate, Part 1's placement, vias, ground pours and escape routes, and Part 2's
resistors, capacitors, pours and power rules as they are:

- `substrates.reference_18layer`: `Reference18Substrate` and `Reference18Board`, an 18-layer
  stackup with its routing structures (ball-field ones among them), vias and backdrills.
- `jumpstart_kits.vp1002_lpddr4`: `circuit.VP1002LPDDR4`, the VP1002 offering one x32 LPDDR4
  interface with the pin swaps AMD allows, as `bundles.VersalLPDDR4`.
- `components.memories.MT53E1G32D2FW_046_WT_B.MT53E1G32D2FW_046_WT_B`, the Micron memory.
- `protocols.memory.lpddr4`: `LPDDR4Constraint`, whose defaults come from a different guide, UG583.
- `jumpstart_kits.vp1002_lpddr4.package_delays.SYNTHETIC_CSV`: the FPGA's package delays, in
  Vivado's I/O ports export format. The values are synthetic, not AMD data: say so wherever you
  report a delay that includes them. Map `Pin Number` to an FPGA port with `ball_to_rc` from
  `jumpstart_kits.js1_stackup_components.versal_fpga.tools.generate_pinout` and the FPGA's
  `ball_assignments()`, and check that ball AT20 maps to
  `IO_L8P_N2P4_M0P70_701`.

## Steps

**0 · Preflight.**
Tell me this runbook's revision, from the comment at the top, and confirm
`jitx-interconnect-constraints` is invocable.

**1 · Project.**
Set up a new JITX project in an empty directory, with `jitxexamples` as a dependency and a parts
chain as the jitx-examples README's
[Parts configuration](https://github.com/JITx-Inc/jitx-examples#parts-configuration) section says,
and build the seeded design.

**2 · Start from Part 2.**
Build your design on Part 2's reference, `JS4PowerCircuit` and `JS4PowerDesign` from
`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part2_power`. It places the memory below the FPGA, fans
out every FPGA ball but its NC balls, and every memory ball but NC and DNU, through a via in its
pad, pours GND on every ground layer, escapes channel B's two DQS pairs out of both parts' ball
fields on segments tagged `ball_field.BallFieldPairTag`, whose rule gives them the ball-field pair
structure, places the resistors and the decoupling capacitors on BOTTOM, and pours five rails on L9,
L10 and L12. `JS4PowerCircuit` extends Part 1's circuit, which extends `base.JS4BaseCircuit`, which
declares the nets and reads the LPDDR4 interface through `lpddr4_bus()`, so look there for them.
Build it.

**3 · [HUMAN] Constraint plan.**
Tell me in a few sentences what a JITX timing constraint measures along a path. Then table every
UG863 LPDDR4/4x timing and physical rule: its value, and how you'll express it in JITX or why you
won't; express the trace length rule as a delay limit through the substrate's velocity. Pick
routing structures against UG863's impedance targets, and say how package and via delay count
toward that limit, quoting UG863 on package delay.
Our SI team allows at most 1.0 dB insertion loss on every LPDDR4 signal: add it to the table as
our number, not UG863's. Add our layout targets, 20% of UG863's limit: DQ and DM to DQS_T
+/-20 ps, each DQS and CK pair +/-0.4 ps, and CKE and CS to CK_T +/-4 ps. They leave margin for
simulation and the synthetic package delays. TI SPRAD66B recommends matching in the layout tool
to a target less than 20% of the limits in its own tables before simulation; ours are at that
bound, not below it. Keep UG863's limit for CA to CK_T and DQS to CK_T. Flag where the FPGA's
offer differs from the table. Wait for my approval.

**4 · Constraints.**
Write the approved rules as one reusable constraint on `LPDDR4Constraint`, taking the routing
structures and limits as arguments, the loss limit among them, and apply it. Give each FPGA pin in
the delay file a `TerminatingPinModel` at the midpoint of its delays, and the memory's pins none.
Write UG863's spacing as design rules, with the under-device values on segments carrying a
`BallFieldTag` from `jitxexamples.jumpstart_kits.js4_fpga_lpddr4.ball_field`; Part 1's escapes
carry its subclass, `BallFieldPairTag`.
Build and check the issues: expect 182 `NOT MET` groups, holding the 66 skews, 56 delay limits and
68 loss limits (each CKE ball's three share one). If yours differ after you recheck your nets and
rules, stop and tell me.

**5 · Verify.**
Run the skills' checks, a build of your design and `jitx-code-review`; fix what they find apart from
unrouted paths, and report each result.

## Done when

- The design builds on Part 2's reference unchanged: it binds the reference substrate and board,
  uses `VP1002LPDDR4`'s pin offer, keeps Part 1's placement, vias, ground pours and escape routes,
  and keeps Part 2's resistors, capacitors, pours and power rules.
- The step 3 table covers every UG863 LPDDR4/4x timing and physical rule with its revision, each
  applied or left out with a reason, gives the loss limit as the SI team's and the four 20% targets
  as ours beside UG863's limits; no width is invented. Step 3 stopped before any constraint was
  written.
- The constraint is one reusable class or function taking the structures and limits as arguments,
  and the design reports 182 `NOT MET` groups, holding the 66 skews, 56 delay limits and 68 loss
  limits (each CKE ball's three share one).
- UG863's spacing is written as design rules, with the under-device values on segments carrying a
  `BallFieldTag`.
- Each FPGA pin in the delay file has a `TerminatingPinModel` at its midpoint, read by column name;
  the memory's pins have none. Every reported delay that includes them says they are synthetic.
- `pyright` passes with zero suppressions; `pytest` passes for any tests you wrote; `jitx design
  find` shows no import failures; the design builds; and `jitx-code-review` leaves no CRITICAL
  finding (every result reported, with the reason for each WARNING kept).

Part 4 routes channel B's two byte lanes interactively, and JITX measures their DQ, DMI and DQS
constraints on the routed copper.

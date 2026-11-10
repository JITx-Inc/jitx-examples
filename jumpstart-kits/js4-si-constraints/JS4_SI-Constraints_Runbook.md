<!--
JITX SI Constraints Runbook (JS4) · rev 3.0 · 2026-11-03
Give this file to your AI coding agent (Claude Code, Codex / GPT, or Devin) and tell it to follow
the file. Complete JS0 and JS1 Part 1 first, then START A NEW AGENT SESSION: a skills install only
takes effect in a session started after it.
-->

# JITX SI Constraints Runbook (JS4)

Each step below is a request, written the way you would ask an agent for the work. Follow them in
order; at a **[HUMAN]** step, stop and wait for me. Drive `jitx-interconnect-constraints` for the
constraints and the base `jitx` skill for the project. The ground truth is AMD UG863, *Versal
Adaptive SoC PCB Design User Guide*, its LPDDR4/4x timing constraint rules and physical design
rules: <https://docs.amd.com/r/en-US/ug863-versal-pcb-design>. Cite its revision wherever you use
it. If you cannot read those tables, tell me what you tried and ask me for them. Where it leaves a
choice, make it and tell me what you chose. Don't open
`jitxexamples.jumpstart_kits.js4_si_constraints`, even where a skill offers it as an example: it is
a finished answer to this task.

**Prerequisites:** JS0 and JS1 Part 1 are done, and you have the `board.py` JS1 Part 1 produced;
Python 3.12+; you can fetch from amd.com.

Every part comes from the `jitxexamples` package; model none, and leave the FPGA's pin offer as it
is:

- `jumpstart_kits.vp1002_lpddr4x`: `circuit.VP1002LPDDR4X`, the JS1 VP1002 offering one x32
  LPDDR4X interface, `bundles.VersalLPDDR4X`, with the pin swaps AMD allows, and
  `pinout.LPDDR4X_X32`, the pins it offers. JITX picks the pins when the board is routed.
- `components.memories.MT53E1G32D2FW_046_WT_B.MT53E1G32D2FW_046_WT_B`, the Micron memory.
- `protocols.memory.lpddr4`: the `LPDDR4` bundles and `LPDDR4Constraint`, a reusable constraint
  whose `LPDDR4ConstraintParams` defaults come from a different guide, UG583.
- `jumpstart_kits.vp1002_lpddr4x.package_delays.SYNTHETIC_CSV`, the path of the FPGA's package delay
  file, with columns named after Vivado's I/O ports export (UG899 Appendix A): one row per pin of
  memory triplet M0, with its minimum and maximum delay in ps, both legs of a P/N pair alike. Its
  values are synthetic estimates, not AMD data; say so wherever you report a delay that includes
  them. Its `Pin Number` is the ball: map it to an FPGA port with `ball_to_rc` from
  `jumpstart_kits.js1_stackup_components.versal_fpga.tools.generate_pinout` and the FPGA's
  `ball_assignments()`, and check one: ball AT20 is `IO_L8P_N2P4_M0P70_701`.

## Steps

**0 · Preflight.**
Tell me this runbook's revision, from the comment at the top, and confirm
`jitx-interconnect-constraints` is invocable.

**1 · Project.**
Set up a new JITX project for this board in an empty directory, with `jitxexamples` as a dependency
and my JS1 Part 1 `board.py` copied in, and build the seeded design.

**2 · Connect.**
Place the VP1002 and the Micron on my JS1 board and substrate, require the FPGA's interface and net
it to the memory with plain nets, each channel's one CKE to both of the memory's CKE balls. Build
it.

**3 · [HUMAN] Constraint plan.**
First tell me, in a few sentences, what a JITX timing constraint measures along a path and where
each part of that measurement comes from. Then show me every UG863 LPDDR4/4x timing and physical
rule in a table: its value, and how you will express it in JITX or why you won't. Turn the 3600 mil
trace length rule into a delay from the substrate's own velocity: about 525 ps on the JS1
striplines. Name the routing structures against UG863's impedance targets, and the closest with the
gap if none is in range. Say how you will count package delay and via delay, quoting what UG863 says
about package delay. A `TerminatingPinModel` adds its pin's package delay to every path on that pin,
delay limits included, so with the pin models step 4 asks for, package delay counts toward the 3600
mil limit: say so, and what that leaves for the trace with the file's delays. Flag where the FPGA's
offer differs from the table. Wait for my approval.

**4 · Constraints.**
Write the approved rules as one reusable constraint for this link that takes the routing structures
and the limits as arguments and builds on `LPDDR4Constraint`, and apply it. Give each FPGA pin in
the package delay file a `TerminatingPinModel` at the midpoint of its minimum and maximum, reading
the file by column name and skipping rows with no delay, as a full export lists every pin; leave
the memory's pins without one.
Build, and check the issues.
Expect 66 skews (per channel the CK pair, two CKE, two CS and six CA; per byte the DQS pair, DQS
to CK, DMI and eight DQ) and 56 delay limits. Unrouted, each sits in its own `Unassigned Pin on
Path` group, except that each CKE ball's skew and delay share one group reporting that ball's path
unrouted (`No path for signal constraint`, or a `Signal path` line ending `is not routed yet`): 118
`NOT MET` groups, then `met Satisfied`, the routing check. Map any other count to these. On jitx
4.6.0 the report may name a path's FPGA end through a net on the required bundle, as in
`RESET_n.ch[0].ca[0]`; the path is still that signal's.

**5 · Verify.**
Give the JS1 microvias you will route through a delay model, on subclasses in this project, not in
`board.py`: the time across the via's dielectric from the middle of its top copper to the middle of
its bottom copper, D·√Dk / c, from the substrate's own thicknesses and Dk, with no loss. Then write
a verification design that code-routes one channel B byte lane, its CK pair, its CKE (FPGA pin to
one CKE ball, on to the other) and one CA bit, on the inner striplines through those microvias in
the pads. Expect 15 Skew and 12 Time lines and no `Using placeholder model` line; report each
against its limit, how much of each Time and each Skew is package delay, and what UG863's layout
rules would flag. Don't match lengths.

Then run the skills' checks and `jitx-code-review`, fix what they find apart from unrouted paths,
and report each result.

**6 · [HUMAN] Change a requirement.**
Invite me to change a requirement, suggesting: *"Our SI team wants DQ and DMI within ±50 ps of DQS.
Change that limit and show me where the routed paths stand."* Change only that limit, in one place,
rebuild the verification design, and show me the new limit as the report prints it and each routed
DQ and DMI skew against it, from the new report: the router may lay the routes differently. Then
run step 5's checks again.

## Done when

- The design binds my JS1 substrate, uses `VP1002LPDDR4X`'s pin offer unchanged, and nets the
  interface to the memory with plain nets, one CKE per channel to both CKE balls.
- The step 3 table covers every UG863 LPDDR4/4x timing and physical rule with its revision, each
  applied or left out with a reason; the 3600 mil rule is a delay derived from the substrate's
  velocity; the impedance gap is reported, with no width invented. Step 3 stopped before any
  constraint was written.
- The constraint is one reusable class or function that takes the structures and limits as
  arguments, and the shipping design reports its 66 skews and 56 delay limits, unmeasured, in 118
  `NOT MET` groups.
- Each FPGA pin in the package delay file carries a `TerminatingPinModel` at the midpoint of its
  minimum and maximum, read from the file by column name; the memory's pins carry none. Every report
  of a delay that includes them says the values are synthetic.
- The microvias the verification design routes through carry a delay model from the substrate's
  thicknesses and Dk, and `board.py` is unchanged.
- The verification design reports 15 Skew lines and 12 Time lines and no placeholder model, each set
  against its limit.
- `pyright` passes with zero suppressions; `pytest` passes for any tests you wrote; `jitx design
  find` shows no import failures; every design builds; and `jitx-code-review` leaves no CRITICAL
  finding (every result reported, with the reason for each WARNING kept), after step 5 and again
  after step 6.
- After step 6 exactly one limit has changed, and the verification design reports each DQ and DMI
  skew against ±50 ps.

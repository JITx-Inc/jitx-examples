# JS4: SI Constraints

**Shortcut:** {download}`Download the runbook <JS4_SI-Constraints_Runbook.md>`, give it to your AI
coding agent, and tell it to follow the file.

Turn a vendor's layout guide into signal-integrity constraints by prompting an agent that drives
`jitx-interconnect-constraints`. The agent reads AMD UG863's LPDDR4/4x rules for the link from the
JS1 VP1002 FPGA to a Micron MT53E1G32D2FW LPDDR4X memory and writes the timing rules and the trace
length rule as one reusable constraint: skew limits, the length rule turned into a delay limit
through the stackup's own velocity, routing structures and reference planes. It gives the FPGA's
pins package delays from a supplied file of synthetic estimates (not AMD data) and the board's
microvias a delay model, then code-routes one byte lane, a clock, the clock enable and an address
bit, and JITX measures each routed path against its limits.

## What you learn

A timing constraint in JITX is a limit on a path, written in code. It names the path from one pin
to another through the nets, and a limit on that path's delay or on the difference between two
paths' delays. JITX adds up everything on the path: the package delay inside each end pin, given as
a pin model; each trace, from its routing structure's velocity on the layer it runs on; each via,
from its delay model; and any part the path passes through, from that part's pin model. The issue
report sets each routed path's sum against its limit.

Because the constraint is code, its limits are arguments. In this kit the agent writes UG863's rules
once, as one constraint for this link. A tighter requirement from your SI team is one changed value
and a rebuild (gate 2 below). A revision of UG863 that changes only limits changes numbers, not
code. The next board with this link, or another stackup, takes the same constraint with its own
routing structures. The package delays come from a file, so a new export changes an input, not the
constraint; the via models are code on the stackup's own materials, so a new stackup needs its own.
The interface is the example; what you learn is how to capture a guide's timing rules once and carry
them from board to board.

## What the kit supplies and leaves out

UG863 says "Include adaptive SoC package delays for all skew calculations", and "Include package
delay in routing constraints when determining signal trace lengths unless otherwise specified". It
takes the delays from Vivado's per-pin export, at the midpoint of each pin's minimum and maximum.
AMD publishes them only through Vivado, and the VP1002's were not available for this kit, so the
kit supplies a package delay file with the export's column names whose values are synthetic
estimates, not AMD data; both legs of each differential pair get the same value. The agent turns it
into the pin models.

A pin model adds its delay to every path on that pin, the delay limit included, so this kit counts
package delay toward the 3600 mil rule, which UG863's table calls a PCB trace length. That is the
conservative reading: it leaves the trace about 2280 to 2940 mil on the length-limited pins with
these estimates. The other reading holds the trace alone to 3600 mil, and needs each path's limit
raised by its own pin's package delay, which is not known until JITX assigns the pins. The agent
shows you the reading it applies, and what it leaves for the trace, at gate 1. On your own board,
export the real delays from Vivado, check their column names, and point the same code at that file.

The via delay model is first order: the time to cross the dielectric from the middle of one copper
layer to the middle of the next, from the stackup's own thicknesses and Dk. It leaves out the pad
and antipad, so it is a floor on each via's delay, not a characterization. The agent puts it on
JS4's own copies of the JS1 microvias; your JS1 `board.py` stays as it is.

Some of UG863 stays outside the constraint. Spacing, via counts and which layer a group runs on are
layout rules for a layout review. JS4 does not match lengths: the verification routes stay as
routed, so some miss their limits, and a skew between two different FPGA pins includes their
package delays' difference, synthetic here. A miss shows the check working, not a fault for the
agent to fix.

The FPGA comes from the `jitxexamples` package with its LPDDR4X pin swaps already offered, so JITX
picks its pins when the board is routed; [JS3](../js3-pin-assignment/) teaches that part. JS4
exports no XDC, and validating the FPGA pins in Vivado stays your step.

## Before you start

- Finish [JS0](../js0-setup/) and [JS1 Part 1](../js1-stackup-components/part1-stackup/). The
  design uses the substrate you built there.
- Start a new agent session. A skills install only takes effect in a session started after it.
- Allow about two hours of agent time, plus the time you spend at the two decisions below.
- Have your JS1 Part 1 `board.py` at hand. Your agent needs network access to amd.com.
- To compare this run with your current flow afterward, note now roughly how long it takes your
  team to get a memory interface's layout-guide rules into the layout tool's constraints, and how
  long a changed limit takes to reach the constraints and the check
  against the routed board. During the run, time it, and time gate 2 from your request to the
  agent's report.

## What the agent asks of you

Two `[HUMAN]` gates stop for you:

1. **Approve the constraint plan.** The agent shows you every UG863 LPDDR4/4x rule beside how it
   will express it in JITX, or why it won't, with the routing structures it will use, the gap to
   UG863's impedance targets, how it will model package and via delay, and the one clock enable per
   channel the FPGA offers where UG863 lists two for a dual-rank memory. You approve before it
   writes any constraint.
2. **Change a requirement.** Ask for a tighter limit (the runbook suggests DQ and DMI within ±50 ps
   of DQS). The agent changes that one value, rebuilds, and shows you the new limit in the report
   and each routed DQ and DMI path's verdict against it.

## After the run

You can now write a layout guide's timing and length rules as constraints that JITX measures on the
routed board, with the package and via delays on the path. Set gate 2's time against the same change
in your current flow, through to the check against the routed board; that comparison counts for more
than the whole run's time against your note, since a first run includes learning. Length matching,
the step toward meeting these limits, is outside this kit. Then write the constraints for an
interface from one of your own boards, from its vendor's layout guide and your own package delay
export, and time it against the same note: that second run is the fairer measure.

## Files

- [The runbook](JS4_SI-Constraints_Runbook.md), to read here;
  {download}`download it <JS4_SI-Constraints_Runbook.md>` to give to your agent. It names the AMD
  guide the agent fetches.
- The synthetic package delay file, `package_delays_synthetic.csv`, ships inside the `jitxexamples`
  package next to
  [`jumpstart_kits.vp1002_lpddr4x.package_delays`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/vp1002_lpddr4x),
  which generates it and says how.
- The reference solution, module
  [`jitxexamples.jumpstart_kits.js4_si_constraints`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js4_si_constraints)
  in the `jitxexamples` package (`pip install jitxexamples`).

# JS4 Part 3 — SI Constraints

**Shortcut:** {download}`Download the runbook <JS4_Part3_SI-Constraints_Runbook.md>`, give it to
your AI coding agent, and tell it to follow the file.

Turn a vendor's layout guide into constraints that enforce signal integrity by prompting an agent
that drives `jitx-interconnect-constraints` and `jitx-layout-constraints`. Starting from Part 2's
reference, where every FPGA ball but its NC balls, and every memory ball but NC and DNU, is fanned
out, the memory is placed below the FPGA, and the decoupling and power pours are in, the agent reads
AMD UG863's LPDDR4/4x rules for the link from the JS1 VP1002 FPGA to a Micron MT53E1G32D2FW LPDDR4
memory and writes them as one reusable constraint: skew and delay limits, routing structures, and an
insertion loss limit standing in for your SI team's budget, not a UG863 value, with UG863's spacing
as design rules beside it. It gives the FPGA's pins package delays from a supplied file and ends at
the issues report of the design before routing, where every constrained path reports `NOT MET` until
it is routed. The board uses an 18-layer reference stackup that ships in `jitxexamples`, built from
the fabrication drawing of a production FPGA evaluation board.

What you learn is how to write constraints that enforce signal integrity, whose skew limits JITX's
router matches lengths against when it routes a complex interface like LPDDR4. You capture a guide's
rules once, as code that JITX measures on the routed board, and carry them from board to board:
[Part 4](../part4-routing/) routes channel B's two byte lanes against them, with the router matching
their lengths to Part 3's skew limits, and the next board with this link takes the same constraint
with its own routing structures. The Essentials page [Signal Integrity
Constraints](https://docs.jitx.com/en/latest/essentials/SI/constraints.html) covers the concepts.

## Before you start

- Finish [JS0](../../js0-setup/) and [JS1 Part 2](../../js1-stackup-components/part2-versal-fpga/),
  where the VP1002 comes from. You do not need Parts 1 or 2 of JS4: this part builds on the
  reference solution of [Part 2](../part2-power/), which ships in `jitxexamples`.
- Start a new agent session. A skills install only takes effect in a session started after it.
- Allow about an hour of agent time, an estimate since this part has not been timed on its own,
  plus the time you spend at the decision below. Your agent needs network access to amd.com and
  github.com.
- If you want to compare this run with how your team does the same work today, time it.

## What the agent asks of you

One `[HUMAN]` gate stops for you:

1. **Approve the constraint plan.** The agent shows you every UG863 LPDDR4/4x rule beside how it
   will express it in JITX, or why it won't; the routing structures against UG863's impedance
   targets; and how it will count package and via delay toward the trace length limit. The table
   also carries the runbook's 1.0 dB insertion loss limit, the kit's stand-in for your SI team's
   budget, not a UG863 value; on your own board, give your team's number. It also sets the kit's
   layout targets at 20% of UG863's limit on four rules: DQ and DM to DQS_T +/-20 ps, each DQS and
   CK pair +/-0.4 ps, and CKE and CS to CK_T +/-4 ps. CA to CK_T and DQS to CK_T keep UG863's
   limits. A target below the limit leaves margin for simulation and the synthetic package delays.
   TI SPRAD66B recommends matching in the layout tool to a target less than 20% of the limits in its
   own tables before simulation; the kit's 20% is at that bound, not below it. It flags the one
   clock enable per channel the FPGA offers where UG863 lists two for a dual-rank memory. You
   approve before it writes any constraint.

## After the run

You can now write a layout guide's timing rules, and your own loss budget, as constraints that JITX
measures, with package and via delays on the path. Routing channel B's two byte lanes against them
is Part 4's, and validating the FPGA pins in Vivado is outside this kit. Then write the constraints
for an interface from one of your own boards, from its vendor's layout guide and your own Vivado
package delay export.

## Files

- [The runbook](JS4_Part3_SI-Constraints_Runbook.md), to read here;
  {download}`download it <JS4_Part3_SI-Constraints_Runbook.md>` to give to your agent.
- `package_delays_synthetic.csv`, the FPGA's package delays in Vivado's export format, ships in
  [`jumpstart_kits.vp1002_lpddr4`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/vp1002_lpddr4).
  AMD publishes package delays through Vivado's export, and the VP1002's were not available, so
  its values are synthetic estimates, not AMD data; the module that generates it says how. On your
  own board, point the same code at your export.
- The reference solution, module
  [`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part3_si_constraints`](https://github.com/JITx-Inc/jitx-examples/blob/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4/part3_si_constraints.py)
  in the `jitxexamples` package, built on Part 2's reference, module
  [`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part2_power`](https://github.com/JITx-Inc/jitx-examples/blob/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4/part2_power.py).
  A project that builds it sets up a parts chain as the repository README's
  [Parts configuration](https://github.com/JITx-Inc/jitx-examples#parts-configuration) section
  says.

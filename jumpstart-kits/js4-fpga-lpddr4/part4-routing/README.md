# JS4 Part 4 — Routing

**Shortcut:** {download}`Download the runbook <JS4_Part4_Routing_Runbook.md>`, give it to your AI
coding agent, and tell it to follow the file.

Route two LPDDR4 byte lanes against their timing constraints by prompting an agent that drives
`jitx-interactive-layout`. Starting from Part 3's reference, where every FPGA ball but its NC balls
and every memory ball but NC and DNU has a via in its pad, channel B's two strobe pairs are escaped
out of both ball fields, the decoupling and power pours are in, and UG863's LPDDR4/4x rules are
constraints, the agent routes every DQ, DMI and DQS of channel B's byte lanes 0 and 1 on L3_SIG1
from the JS1 VP1002 FPGA to the Micron MT53E1G32D2FW LPDDR4 memory. It matches length with
serpentines inside length-matching sections, and JITX measures each route against Part 3's limits:
DQ and DMI to DQS skew, each DQS pair's skew, and every byte-lane signal's delay and loss. The
issues report of the routed design proves it. The board uses an 18-layer reference stackup
that ships in `jitxexamples`, built from the fabrication drawing of a production FPGA evaluation
board.

What you learn is how to route an interface against constraints that JITX measures on the routed
copper, with each skew's margin in the issues report of every build. Part 3's constraints drive the
router's length matching: in the reference build, it lengthened the length-matching sections until
all 20 byte-lane skews were met. The Essentials page [Topological
Autorouter](https://docs.jitx.com/en/latest/essentials/physical_design/autorouter.html) covers how
the router behaves.

## Before you start

- Finish [JS0](../../js0-setup/) and [JS1 Part 2](../../js1-stackup-components/part2-versal-fpga/),
  where the VP1002 comes from. You do not need Parts 1 to 3 of JS4: this part builds on the
  reference solution of [Part 3](../part3-si-constraints/), which ships in `jitxexamples`.
- Start a new agent session. A skills install only takes effect in a session started after it.
- This part has not been timed yet. Your agent needs network access to github.com.
- If you want to compare this run with how your team does the same work today, time it.

## What the agent asks of you

One `[HUMAN]` gate stops for you:

1. **Approve the routing plan.** The agent shows you how it will route each byte lane to its FPGA
   byte slot, where each length-matching section goes, and the limits each route will be measured
   against. You approve before it routes.

After routing, the agent builds, checks each line and pair it routed for copper and for a serpentine
grown into a neighbour's room, repairs and re-tunes what broke, and runs its checks to the end. The
data lines carry no tag: their 46 ohm structure fits between the balls, and only Part 1's strobe
escapes take the ball-field structure. The agent places a control point only at the ends of a
length-matching section.

## After the run

You can now have an agent route a memory interface against its constraints and report each skew's
margin from the routed copper. This part routes two byte lanes; the other byte lanes and the
command, address and clock nets stay unrouted. Then route a byte lane on one of your own boards
against its constraints.

## Files

- [The runbook](JS4_Part4_Routing_Runbook.md), to read here;
  {download}`download it <JS4_Part4_Routing_Runbook.md>` to give to your agent.
- The reference solution, module
  [`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part4_routing`](https://github.com/JITx-Inc/jitx-examples/blob/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4/part4_routing.py)
  in the `jitxexamples` package, built on Part 3's reference, module
  [`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part3_si_constraints`](https://github.com/JITx-Inc/jitx-examples/blob/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4/part3_si_constraints.py).
  It routes the two byte lanes in code along a reference layout's paths, module
  [`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part4_reference_routes`](https://github.com/JITx-Inc/jitx-examples/blob/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4/part4_reference_routes.py).
  A project that builds it sets up a parts chain as the repository README's
  [Parts configuration](https://github.com/JITx-Inc/jitx-examples#parts-configuration) section
  says.

# JS4 Part 2 — Power

**Shortcut:** {download}`Download the runbook <JS4_Part2_Power_Runbook.md>`, give it to your AI
coding agent, and tell it to follow the file.

Lay out a board's power in code by prompting an agent that drives `jitx-code-layout` and
`jitx-layout-constraints`. Starting from Part 1's reference, where the JS1 VP1002 FPGA and a Micron
MT53E1G32D2FW LPDDR4 memory are placed and fanned out, you give the agent your power strategy and it
sets width and clearance floors for the two 2 oz power layers from a fabricator's published
capability, places the ZQ, IO_VR and RREF resistors and the decoupling capacitors on the bottom
side, and writes a pour for each of five rails on its layer. Each capacitor below 10 uF sits across
two ball vias of its rail and ground, with no route; the larger ones, and any small one with no free
pair, go in a ring outside the part's ball field, each pad on its own via, clear of the corridor
between the parts where Part 4 routes two byte lanes. Part 1's reference already leaves out the
capacitors that would connect to nothing, those a ring would hold on a rail that gets no pour, so
the agent places every capacitor it inherits: 46 in the fields and 13 in the ring. The 1.1 V pour
joins the FPGA's XPIO bank supplies to the memory's field, since the design models no power source.
Each part's resistors, capacitors and their vias sit in the part's circuit, so they move with it;
the pours are drawn on the board from where the parts sit. The counts in the runbook and JITX's
issues report check the result.

What you learn is how to state a power layout as precise constraints that code applies, so the
layout is correct and consistent: the capacitor placement rule, the rail-to-layer map, the gap
between rails and the 2 oz floors are each stated once and applied to all 59 capacitors, 6
resistors and 5 pours, and changing one is one edit and a rebuild.

The heavy copper rules are the general example of a key concept in JITX, layout constraints. The
agent tags the five poured rails' nets and writes rules that each pair a condition on tags or layers
with an effect. The reference's rules are a 6 mil trace width for the tagged nets; on L9 and L10, a
trace width floor, a clearance floor and a trace to pour clearance; and a pour feature size, raised
on L9 and L10 to their width floor. No relief rule matches the pours, so each joins its own net's
vias solid. The agent reports each tag and rule it wrote. Part 1's ball-field pair structure and
Part 3's spacing rules are layout constraints too. The Essentials page [Layout
Constraints](https://docs.jitx.com/en/latest/essentials/physical_design/layout-constraints.html#heavy-copper-on-one-layer)
builds the same kind of heavy copper rules on another board.

## Before you start

- Finish [JS0](../../js0-setup/) and [JS1 Part 2](../../js1-stackup-components/part2-versal-fpga/),
  where the VP1002 comes from. Part 1 of this kit is optional: this part starts from its reference.
- Start a new agent session. A skills install only takes effect in a session started after it.
- Allow about two hours of agent time, plus the time you spend at the checks below. Your agent
  needs network access to github.com and pcbway.com.
- If you want to compare this run with how your team does the same work today, time it.

## What the agent asks of you

Two `[HUMAN]` gates stop for you:

1. **Check the layout.** The agent shows you the tags and rules it wrote, each with what it
   applies to and what it sets, then the resistors, the capacitors by part and by field or
   ring, the pours by layer with each pour's area and the ball and ring vias inside it, and the
   rails that get no pour. Then it opens the board view and tells you where
   to look to see a capacitor across two ball vias, a ring capacitor on its vias and the 1.1 V pour
   joining the two parts. You confirm before it runs its checks.
2. **Change the strategy.** The agent invites you to change one part of the power strategy and
   suggests making the gap between two rails' pours on a layer 15 mil. It changes only what you
   name, rebuilds, and reports each pour's area and the smallest gap on each layer.

## After the run

You can now give an agent a power strategy for a dense board and get it applied, in code, to every
capacitor and rail it names. The design has no power source and no regulator, and the FPGA's
other rails get no pour in this part. Then give the same kind of strategy for a BGA on one of your
own boards.

## Files

- [The runbook](JS4_Part2_Power_Runbook.md), to read here;
  {download}`download it <JS4_Part2_Power_Runbook.md>` to give to your agent.
- The design this part starts from, module
  [`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part1_fanout_escape`](https://github.com/JITx-Inc/jitx-examples/blob/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4/part1_fanout_escape.py)
  in the `jitxexamples` package, Part 1's reference.
- The reference solution, module
  [`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part2_power`](https://github.com/JITx-Inc/jitx-examples/blob/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4/part2_power.py)
  in the `jitxexamples` package. A project that builds it sets up a parts chain as the repository
  README's [Parts configuration](https://github.com/JITx-Inc/jitx-examples#parts-configuration)
  section says.

<!--
JITX Power Runbook (JS4 · Part 2) · rev 1.8 · 2026-11-12
Give this file to your AI coding agent (Claude Code, Codex / GPT, or Devin) and tell it to follow
the file. Complete JS0 and JS1 Part 2 first, then START A NEW AGENT SESSION: a skills install only
takes effect in a session started after it.
-->

# JITX Power Runbook (JS4 · Part 2)

Each step below is a request, written the way you would ask an agent for the work. Follow them in
order; at a **[HUMAN]** step, stop and wait for me. Drive `jitx-code-layout` for the parts'
placement, their vias and the pours, `jitx-layout-constraints` for the rules, and the base `jitx`
skill for the project and the viewer. The power strategy is mine, given in steps 3 to 7; where it
leaves a choice, make it and tell me what you chose. Don't open the `part2_power` or
`part3_si_constraints` modules of `jitxexamples.jumpstart_kits.js4_fpga_lpddr4`, even where a skill
offers them as examples: they hold a finished answer to this task. Build on `part1_fanout_escape`
without reading that module: subclass its `JS4FanoutCircuit` and `JS4FanoutDesign`, and place each
part's resistors and capacitors in a subclass of its `FanoutFpga` or `FanoutMemory`, which your
circuit returns from `new_fpga` and `new_memory`. The package's `base` module, which declares those
two methods, and `jitxexamples.jumpstart_kits.vp1002_lpddr4.decoupling` are yours to read.

**Prerequisites:** JS0 and JS1 Part 2 are done; Python 3.12+; you can fetch from github.com and
pcbway.com.

Every part, and the board, comes from the `jitxexamples` package. Model none, and leave the FPGA's
pin offer, the substrate, the base design's nets and Part 1's placement, vias, ground pours and
escape routes as they are:

- `substrates.reference_18layer`: `Reference18Substrate` and `Reference18Board`, an 18-layer
  stackup whose L9_PWR1_2OZ and L10_PWR2_2OZ are 2 oz copper.
- `jumpstart_kits.js4_fpga_lpddr4.part1_fanout_escape`: `JS4FanoutCircuit` and `JS4FanoutDesign`,
  the FPGA and the memory placed, a 6 mil through via in every connected ball's pad and ground pours
  on the ground layers. The decoupling capacitors and the ZQ, IO_VR and RREF resistors are unplaced.
  Its `FanoutFpga.decoupling_layouts` leaves out the 27 FPGA capacitors that would connect to
  nothing on this board, all on rails step 7 does not pour, so the design holds 59: 44 at the FPGA,
  15 at the memory. The VCCO of XPIO banks 700 to 702 and the memory's VDD2 and VDDQ are one 1.1 V
  net; VDD1, 1.8 V, has its own. No rail has a source.
- `jumpstart_kits.vp1002_lpddr4.decoupling`: each capacitor below 10 uF has a `ShortTrace` naming
  the ball of its rail it decouples; each larger one is netted to that ball with none.

## Steps

**0 · Preflight.**
Tell me this runbook's revision, from the comment at the top, and confirm `jitx-code-layout` is
invocable.

**1 · Project.**
Set up a new JITX project in an empty directory, with `jitxexamples` as a dependency and a parts
chain as the jitx-examples README's
[Parts configuration](https://github.com/JITx-Inc/jitx-examples#parts-configuration) section says,
and build the seeded design.

**2 · Start from Part 1's reference.**
Build your design on `JS4FanoutCircuit` and `JS4FanoutDesign`, and build it.

**3 · Rules.**
The substrate gives no width or gap for its two 2 oz layers. Take them from PCBWay's
[PCB Capabilities](https://www.pcbway.com/capabilities.html) page, Advanced PCB item 14, the 70 um
row: 6 mil width and 7 mil spacing, the medium column, on L9 and L10 only. Tag the nets of the five
rails step 7 pours, and give their traces 6 mil. Pours join their own net's vias solid and drop any
feature under their layer's width floor.

**4 · Resistors.**
Place the resistors on BOTTOM before any capacitor, each in its part's circuit, with no route: each
RREF resistor across its AVTTRCAL ball's via and the RREF ball's via beside it, each ZQ resistor
across its ZQ ball's via and the VDD2 ball's via beside it. IO_VR_700 has no 1.1 V ball beside it:
put one pad on its via and the other on a new 6 mil via of the 1.1 V net between the balls beside
it. Expect six.

**5 · Small capacitors.**
Place every capacitor below 10 uF on BOTTOM in its part's circuit, across two fanout vias one pitch
apart: rail pad on a via of its rail, return pad on a ground via (a GND_SMON one for VCCAUX_SMON),
nearest the ball its `ShortTrace` names, no courtyard overlap, rails with the fewest balls first.
The count that finds a pair depends on the order, so break every tie the way the reference does:
rails with as many balls in the order `fpga_sets` gives at the FPGA, and VDDQ, VDD2, VDD1 at the
memory; a rail's capacitors in set order; for each, its rail's balls nearest first from the ball its
`ShortTrace` names, equal distances in port order; and at each ball the neighbours at +x, -x, +y,
then -y on the board, taking the first ground one where the capacitor fits. Tell me which land
sizes fit at each part's pitch, with the gap to the next via. The FPGA has 37 capacitors below
10 uF and the memory 12: tell me how many found a pair and which did not. Expect 34 at the FPGA
and all 12 at the memory to find one, with or without step 6's layout; those are the counts in a
field step 8 checks.

**6 · The ring.**
Place each capacitor of 10 uF and up, and each small one that found no pair, in a ring just outside
its part's ball field, on the edge nearest its rail's balls, each pad on its own new 6 mil via in
the pad and no trace back to a ball (a small one's `ShortTrace` becomes a plain net). Each one is on
a rail step 7 pours, since Part 1 never created those on other rails, where the rail via would
connect to nothing: place every capacitor Part 1 holds, and add or leave out none. In your
`FanoutFpga` subclass, override `decoupling_layouts`: take Part 1's (`super().decoupling_layouts()`)
and add, keyed by the set names `fpga_sets` gives, a `RailLayout` from
`jitxexamples.jumpstart_kits.vp1002_lpddr4.decoupling` whose `ring` names, by place in the set, the
small ones that take a plain net for the ring. Which small ones find no pair is known only once step
5 has run, so run it once and write them as data, with the reason. Keep the channel between the
parts clear for the LPDDR4 routes: no ring capacitor on the memory's edge facing the FPGA, and on
the FPGA's edge facing the memory only the XPIO banks', each courtyard 7.75 mil clear of the
corridor where Part 4's byte lanes cross the gap between the fields, x -0.360 to 10.910 mm on the
board. A capacitor whose nearest spot falls in the corridor moves along the edge to the nearest free
spot outside it. Expect seven capacitors of 10 uF and up in the ring at the FPGA and three at the
memory. Tell me the small ones that go to the ring; in the reference, three do, so 10 of the FPGA's
44 capacitors are in the ring and the design's 59 are 46 in the fields and 13 in the ring.

**7 · Pours.**
Pour each rail in code on its layer: on L9, VCCINT and the 1.1 V net, the latter one piece from the
XPIO banks' VCCO balls to the whole memory field, since nothing else joins that rail's balls; on
L10, VCC_SOC with VCC_IO, and VCCAUX; on L12_SIG4, VDD1 under the memory. Draw each outline from the
ball grid: a one-pitch cell on each rail ball, boxed per cluster, and the clusters joined. Join
each ring via to its rail's nearest ball with a link that runs midway between ball rows and columns,
never along a row: along a row, the voids around the other nets' vias leave webs under the width
floor and the via ends up on an island. Keep rails on one layer 10 mil apart. Expect five pours,
one piece each.

**8 · Check the power.**
Build and capture the design. From the capture, count against steps 4 to 7: the resistors; the
capacitors by part and by field or ring; each rail pour's pieces, read from its realized copper, not
its drawn outline, and the vias of its net inside that copper; and the non-Empty ground pours by
layer, one on each of eight layers. If any count differs from an "Expect" in those steps, or from
what you told me there, stop and tell me.

**9 · [HUMAN] Check the layout.**
Show me each tag you created and each rule you wrote in step 3: what it applies to, what it sets and
its priority. Then show me step 8's counts, each pour's realized area and the ball and ring vias
inside it, and the rails that get no pour. Then open the board view and
tell me where to look to see a capacitor across two ball vias, a ring capacitor on its vias, and the
1.1 V pour joining the FPGA's VCCO balls to the memory. Wait for me to confirm.

**10 · Verify.**
Run the skills' checks, a build of your design and `jitx-code-review`; fix what they find, and
report each result.

**11 · [HUMAN] Close the loop.**
Invite me to change one part of the strategy, suggesting: *"Make the gap between two rails' pours
on a layer 15 mil."* Change only what that request names, run step 10 again, and report each pour's
area and the smallest gap between pours on each layer.

## Done when

- The design builds on Part 1's reference unchanged: it binds the reference substrate and board,
  uses the FPGA's pin offer, keeps the base design's nets, and keeps Part 1's placement, vias,
  ground pours and escapes.
- L9 and L10 carry 6 mil width and 7 mil clearance floors, and no other layer does. The five poured
  rails' nets are tagged, with 6 mil traces.
- Six resistors sit on BOTTOM, each pad on a via of its net: the RREF and ZQ resistors on their
  parts' fanout vias, the IO_VR resistor on its ball's via and one new 1.1 V via.
- Every capacitor sits on BOTTOM in its part's circuit, with no courtyard overlap. Each one in a
  ball field is below 10 uF, its rail pad on a via of its rail and its return pad on a ground via.
  Each one outside is in the ring on one of the five poured rails, each pad on its own new via, with
  no `ShortTrace`; seven at the FPGA and three at the memory are of 10 uF and up. The design holds
  Part 1's 59 capacitors and no other: 34 at the FPGA and 12 at the memory in the fields, 10 at the
  FPGA and 3 at the memory in the ring.
- Five pours, each one piece in the captured copper: VCCINT and the 1.1 V net on L9, VCC_SOC and
  VCCAUX on L10, VDD1 on L12. Each one's realized copper holds every ball via and every ring via of
  its rail, and rails on one layer keep 10 mil apart before step 11. The issues report shows no
  `NOT MET`.
- Step 9 showed me step 3's tags and rules and stopped for my confirmation.
- After step 10 and after step 11: `pyright` passes with zero suppressions; `pytest` passes for any
  tests you wrote; `jitx design find` shows no import failures; the design builds; and
  `jitx-code-review` leaves no CRITICAL finding (every result reported, with the reason for each
  WARNING kept).
- After step 11, only what my request named has changed: with the suggested request, the pours on
  L9 and L10 keep 15 mil apart and every count and the issues report are as before.

Part 3 adds the SI constraints to this part's reference, and Part 4 routes on Part 3's.

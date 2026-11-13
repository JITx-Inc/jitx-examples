<!--
JITX Fanout and Escape Runbook (JS4 · Part 1) · rev 4.4 · 2026-11-12
Give this file to your AI coding agent (Claude Code, Codex / GPT, or Devin) and tell it to follow
the file. Complete JS0 and JS1 Part 2 first, then START A NEW AGENT SESSION: a skills install only
takes effect in a session started after it.
-->

# JITX Fanout and Escape Runbook (JS4 · Part 1)

Each step below is a request, written the way you would ask an agent for the work. Follow them in
order; at a **[HUMAN]** step, stop and wait for me. Drive `jitx-circuit-builder` for the placement,
`jitx-code-layout` for the vias, pours and escape routes, `jitx-layout-constraints` for the rules
the escapes take, and the base `jitx` skill for the project and the viewer. The via and routing
strategy is mine, given in steps 3 to 7; where it leaves a choice, make it and tell me what you
chose. Don't open the `part1_fanout_escape` or `part3_si_constraints` modules of
`jitxexamples.jumpstart_kits.js4_fpga_lpddr4`, even where a skill offers them as examples: they hold
a finished answer to this task. Its `base`, `ball_field` and `reference_escapes` modules, and
`jitxexamples.jumpstart_kits.vp1002_lpddr4.pinout` and `.decoupling`, are yours to read.

**Prerequisites:** JS0 and JS1 Part 2 are done; Python 3.12+; you can fetch from github.com.

Every part, and the board, comes from the `jitxexamples` package. Model none, and leave the FPGA's
pin offer, the substrate and the base design's nets as they are:

- `substrates.reference_18layer`: `Reference18Substrate` and `Reference18Board`, an 18-layer
  stackup with its vias, its routing structures and their ball-field forms.
- `jumpstart_kits.js4_fpga_lpddr4.base`: `JS4BaseCircuit` and `JS4BaseDesign`, the VP1002 FPGA and
  the Micron LPDDR4 memory connected, with their decoupling, and only the FPGA placed. The VCCO of
  XPIO banks 700 to 702 and the memory's VDD2 and VDDQ are one 1.1 V net; VDD1, 1.8 V, has its own.
- `jumpstart_kits.js4_fpga_lpddr4.ball_field`: `BallFieldPairTag` and `ball_field_rules`, the tag
  and rule that give a pair's route segment inside a ball field the narrower pair structure.
- `jumpstart_kits.js4_fpga_lpddr4.reference_escapes`: `FPGA_ESCAPES` and `MEMORY_ESCAPES`, where a
  reference layout of channel B's two byte lanes puts each strobe escape's insertion and pair
  point, in each part's circuit, keyed by FPGA byte slot and memory byte lane.
- `jumpstart_kits.vp1002_lpddr4.pinout`: `LPDDR4_X32`, the FPGA's LPDDR4 pin layout. Each byte
  slot belongs to one channel.

## Steps

**0 · Preflight.**
Tell me this runbook's revision, from the comment at the top, and confirm `jitx-code-layout` is
invocable.

**1 · Project.**
Set up a new JITX project in an empty directory, with `jitxexamples` as a dependency and a parts
chain as the jitx-examples README's
[Parts configuration](https://github.com/JITx-Inc/jitx-examples#parts-configuration) section says,
and build the seeded design.

**2 · Start from the base design.**
Build your design on `JS4BaseCircuit` and `JS4BaseDesign` from
`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.base`. It declares the nets and reads the LPDDR4
interface through `lpddr4_bus()`. Build it.

**3 · Placement.**
Leave the FPGA where the base design places it. Put the memory at the origin of its circuit turned
180 degrees, and place that circuit at (6.4509, -17.3772) mm on the board at 0 degrees: the memory
sits below the FPGA's LPDDR4 balls, turned to balance length across the data lanes. Leave the
decoupling capacitors and the ZQ, IO_VR and RREF resistors unplaced. Keep each part's copper in its
own circuit, so it moves with it: vias and escapes in the FPGA's or the memory's circuit.
Leave out of the FPGA's decoupling, by overriding its circuit's `decoupling_layouts` with
`RailLayout(omit=...)`, the 27 capacitors that would connect to nothing on this board. Part 2
pours VCCINT, VCC_SOC with VCC_IO, VCCAUX and the VCCO of banks 700 to 702, and puts every
capacitor of 10 uF and up, and every smaller one with no free ball pair in the field, in a ring on
its own via to its rail's pour. So on every other rail, leave out each capacitor of 10 uF and up,
and these smaller ones, by place in the rail's set counted from 0: place 1 (the second) of
VCCO_503, VCC_PMC, VCC_PSLP and VCCAUX_SMON, place 2 (the third) of GTY_AVCC_RS and GTM_AVCC_RN,
and places 1 and 2 (the second and third) of VCCINT_GT_R. Expect 59
capacitors, 44 at the FPGA and 15 at the memory; if yours differ, stop and tell me.

**4 · Fanout.**
Put a via in the pad of every FPGA ball but its NC balls, and every memory ball but NC and DNU.
That includes the FPGA balls no net reaches yet, so a later part can still assign them; the NC balls
get none, since this board leaves them unconnected and no later part needs them. Each of those
net-less FPGA vias, 293 here, logs `No Net linked for via` when a session opens on the design: keep
them. Make every fanout via the substrate's smallest through via, the 6 mil `THVia_6p0`.
Tell me the gap those vias leave between neighbouring pads at each part's ball pitch. Expect 1309
vias at the FPGA and 183 at the memory; if yours differ after you recheck which balls you skipped,
stop and tell me.

**5 · Ground.**
Pour GND over the whole board on every ground layer, L2, L4, L6, L8, L11, L13, L15 and L17. If you
count other than eight pours, stop and tell me.

**6 · Escape.**
Escape only channel B's two DQS pairs, the ones Part 4 will route, from both ball fields on L3.
Channel A takes L5, since B fills L3 under the FPGA and between the parts; CA, CS, CKE and CK take
L7. Route each pair's vias to a `PairInsertion`, then to a `PairPoint` just outside the field, on
`BallFieldPairTag` segments under `ball_field_rules`, placing both at the position and heading
`reference_escapes` gives in that part's circuit. Place no other control point: the insertion is
where the two legs couple and the pair point is where the tag ends. Invert every FPGA insertion and
pair point, and no memory one.

**7 · Check the escapes.**
Build: expect two pairs at each part, three tagged segments each, and no `NOT MET` in the issues
report. A `No Net linked for via` warning comes from one of step 4's vias on a ball no net reaches:
it is not an issue, so leave the via in place. If yours differ, stop and tell me.

**8 · [HUMAN] Check the fanout.**
Show me the fanout vias by part and the pours by layer, as your capture of the built design counts
them, against steps 4 and 5. Count only pours with copper: the reference-plane pours of step 6's
escapes, on L2 and L4, read back empty. Then open the board view and tell me where to look to see
a through via, a pour layer and the two escapes at each part. Wait for me to confirm.

**9 · Verify.**
Run the skills' checks, a build of your design and `jitx-code-review`; fix what they find, and
report each result.

**10 · [HUMAN] Close the loop.**
Invite me to change one part of the strategy, suggesting: *"Use the 10 mil through via for the
FPGA's GND balls instead."* Change only what that request names, run step 9 again, and report the
fanout vias by type and part.

## Done when

- The design builds on the base design unchanged: it binds the reference substrate and board, uses
  the FPGA's pin offer, and keeps the base design's nets.
- Every FPGA ball but the NC balls, and every memory ball but NC and DNU, has one through via in its
  pad, 6 mil before step 10, and no other ball has one: 1309 at the FPGA and 183 at the memory.
- Each of the eight ground layers has a GND pour over the board.
- The FPGA stays where the base design places it, and the memory sits at (6.4509, -17.3772) mm
  turned 180 degrees. Each part's vias and escapes sit in that part's circuit: moving a part's
  circuit moves its copper with it. The decoupling capacitors and the ZQ, IO_VR and RREF resistors
  are unplaced.
- The design holds 59 decoupling capacitors, 44 at the FPGA and 15 at the memory: none of 10 uF and
  up on an FPGA rail Part 2 does not pour, and none of step 3's eight smaller ones.
- Channel B's two DQS pairs, and no other pair, leave each part's ball field on L3 on segments
  tagged `BallFieldPairTag` to a `PairPoint` outside it, at the positions and headings
  `reference_escapes` gives, with no other control point; `ball_field_rules` is applied. Every FPGA
  insertion and pair point is inverted and every memory one is not. The issues report shows no `NOT
  MET`.
- Step 8 stopped for my confirmation.
- After step 9 and after step 10: `pyright` passes with zero suppressions; `pytest` passes for any
  tests you wrote; `jitx design find` shows no import failures; the design builds; and
  `jitx-code-review` leaves no CRITICAL finding (every result reported, with the reason for each
  WARNING kept).
- After step 10, only what my request named has changed: with the suggested request, the FPGA's
  689 GND vias are 10 mil and every count and the issues report are as before.

Part 2 adds the power copper to this board and places the decoupling, Part 3 adds the SI
constraints, and Part 4 routes channel B's two byte lanes from these escapes; each starts from the
reference of the part before it.
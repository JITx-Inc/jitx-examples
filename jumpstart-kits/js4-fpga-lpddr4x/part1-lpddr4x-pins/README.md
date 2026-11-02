# JS4 Part 1: LPDDR4X Pin Assignment

**Shortcut:** {download}`Download the runbook <JS4_Part1_LPDDR4X-Pin-Assignment_Runbook.md>`,
give it to your AI coding agent, and tell it to follow the file.

The VP1002 FPGA from JS1 drives a Micron MT53E1G32D2FW LPDDR4X over one x32 interface on banks 702
and 701. You encode AMD's LPDDR4/4X pin rules as `provide` options on the FPGA: on the single
channel x32 layout, flipped, the FPGA offers every byte swap and bit swap the rules allow, and JITX
picks the assignment when the board is routed. AMD documents that layout to the nibble, and its pin
positions are the ones channel 0 of AMD's VMK180, VCK190 and VPK120 boards uses, CS1 aside on the single rank VCK190 (gate 1). You build it by driving `jitx-pin-assignment` and `jitx-interconnect-constraints`,
with `jitx-component-modeler` for the pin file. AMD's PG313 is the ground truth for the rules, and
four AMD evaluation boards (VMK180, VCK190, VPK120, VEK280) are checked against the rule set as
worked examples. UG863 timing limits cover the link. Verification designs show that the limits bind,
not that a layout meets them: a legal assignment routed in code for one byte lane, the clock, the
clock enable and one address bit reports a measured skew on each routed path, and an illegal
assignment drops its route. What you learn is how to encode a vendor's pin rules and apply SI
constraints on a complex interface, so the constraints bind whichever legal assignment the design
picks.

PG313 says every pin swap must be captured in the design's XDC and validated before you build
hardware. Validating the chosen assignment in Vivado is your step: this kit does not export an XDC
and does not claim Vivado legality.

## Before you start

- Finish [JS0](../../js0-setup/), [JS1 Part 1](../../js1-stackup-components/part1-stackup/) and
  [JS1 Part 2](../../js1-stackup-components/part2-versal-fpga/). The design uses the substrate and
  the FPGA you built there.
- Start a new agent session for this part. A skills install only takes effect in a session started
  after it.
- Have your JS1 Part 1 `board.py` and your JS1 Part 2 VP1002 package at hand. Your agent needs
  network access to amd.com and github.com.
- Allow about 2 hours.
- To compare this run with your current flow afterward, note now roughly how long deriving the
  memory pin rules and setting the timing constraints takes your team, what tends to go wrong, and
  how long checking another pin assignment against the rules takes, before Vivado and routing.
  During the run, time it, time gate 3 from your request to the agent's report, and note anything
  the checks caught.

## What the agent asks of you

Three `[HUMAN]` gates stop for you:

1. **Confirm the rule table.** The agent shows you AMD's pin rules as a table, each row cited to a
   PG313 topic, table or figure, or to AMD's tutorial; the positions it took from the boards
   because the documents give them only to the nibble, with the boards that agree; and which board
   interfaces pass. The offered layout's fixed command, address, clock, reset and system clock
   positions, and each byte slot's DQS_T, DQS_C and DMI positions, match those boards pin for pin;
   you still validate the chosen assignment in Vivado, the flow AMD's Memory_Pinouts tutorial
   describes. The agent also asks you to confirm the clock
   enable topology: one controller CKE per channel driving both of the memory's CKE balls follows
   the boards, while UG863's timing table lists a CKE1 per channel for dual rank. Approve before it
   writes any `provide`.
2. **Confirm the constraint values.** The agent shows you each timing limit beside its UG863 table
   row, the UG863 rules it does not apply, and the routing structures it will use. Approve before
   it applies them.
3. **Another assignment.** Ask for a proof of another legal assignment (the runbook suggests the
   other channel B byte, in the slot the first proof's byte swap left it). The agent adds a
   verification design without touching the offer or the shipping design, and refuses any
   assignment the rules forbid.

The JS1 substrate has no routing structure inside UG863's impedance windows (45 Ω single ended,
82 Ω differential), so the agent uses the closest structures and reports the gap.

## After the run

You can now encode a memory controller's pin rules and apply its timing limits so they bind
whichever legal assignment a design picks. Gate 3 adds a verification design with a few code routes
and leaves the shipping design unrouted, so set its time against checking another assignment against
the rules in your current flow, before Vivado and routing; that comparison counts for more than the
whole run's time against your note, since a first run includes learning. The illegal assignment is a
control the runbook builds to show the check works, not a catch; set anything else the checks caught
beside what tends to go wrong in your flow. Length matching is not part of this run: these
constraints are the setup it needs, and JITX's solver does the matching against them, with
code-created routes, outside this kit. Vivado validation of the chosen pins stays yours. Leave both
out of the comparison. Then use the pattern on a memory interface on one of your own boards, and
time it against the same note: that second run is the fairer measure.

## Files

- [The runbook](JS4_Part1_LPDDR4X-Pin-Assignment_Runbook.md), to read here;
  {download}`download it <JS4_Part1_LPDDR4X-Pin-Assignment_Runbook.md>` to give to your agent. It
  names the AMD documents and board files the agent fetches; there is no supplied input file.
- The reference solution, module
  [`jitxexamples.jumpstart_kits.js4_fpga_lpddr4x`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4x)
  in the `jitxexamples` package (`pip install jitxexamples`).

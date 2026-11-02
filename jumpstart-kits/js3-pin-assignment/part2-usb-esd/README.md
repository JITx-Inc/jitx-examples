# JS3 Part 2: USB through an ESD Array

**Shortcut:** {download}`Download the runbook <JS3_Part2_USB-through-ESD_Runbook.md>`, give it to
your AI coding agent, and tell it to follow the file.

USB 2.0 runs from an RP2040 through a Nexperia PUSB3FR4 ESD array to a USB Type-C receptacle, and
the design leaves the choice of ESD channels open: either documented channel pair, either channel on
D+. You build it by driving `jitx-pin-assignment` and `jitx-interconnect-constraints`. The PUSB3FR4
datasheet is the ground truth for which channels may carry the pair. A USB 2.0 constraint covers
the path from the RP2040's pins to the receptacle's, and verification designs prove it binds:
routed through offered channels it reports a loss on each leg and the skew between them, and
routed through a pairing the datasheet does not document it drops the route. What you learn is how
to leave a part's channel choices open within what its datasheet documents, with an SI constraint
that binds whichever channels the design picks.

## Before you start

- Finish [JS0](../../js0-setup/) and [JS1 Part 1](../../js1-stackup-components/part1-stackup/).
  The designs bind the substrate you built there.
- Start a new agent session for this part. A skills install only takes effect in a session started
  after it.
- Have your JS1 Part 1 `board.py` at hand.
- Allow about 15 minutes.
- To compare this run with your current flow afterward, note now roughly how long choosing
  protection-part channels and checking them against the datasheet takes your team, what tends to go
  wrong, and how long re-checking another channel choice takes, before layout. During the run, time
  it, time gate 2 from your request to the agent's report, and note anything the checks caught.

## What the agent asks of you

Two `[HUMAN]` gates stop for you:

1. **Confirm the channel freedom.** The agent shows you each channel mapping it offers beside the
   datasheet table or figure that supports it, the pairings it does not offer, and how each
   channel's trace continues under the package to the unconnected pin opposite. The right answer
   is one net, joined by board copper under the package: the opposite pins are n.c., so a pin
   model between them would describe a path the part does not have and leave the data line open
   on the board. Approve before it writes the SI constraint.
2. **Another channel choice.** Ask for a proof through another channel choice (the runbook suggests
   D+ on CH2 and D- on CH1). The agent adds a verification design without touching the shipping
   design, and refuses any pairing the datasheet does not document.

The JS1 substrate has a 100 Ω differential structure and no 90 Ω one, so the agent uses 100 Ω and
reports the gap against USB 2.0's 90 Ω.

The constraint's skew and loss numbers are jitxlib's generic USB 2.0 values. They were not checked
against the USB 2.0 specification, and the 3.75 ps skew limit is far tighter than the RP2040's
Full Speed link needs, so the proofs show that the constraint binds, not that the board complies.
Read the proof output that way: the Loss and Skew lines show binding. `NOT MET` is expected for two
reasons, the placeholder model lines for JS1's vias (which have no SI models) in the same group, and a skew
above jitxlib's 3.75 ps.

## After the run

You can now model the channel freedom a protection part documents and constrain the path through it.
Gate 2 adds a verification design and leaves the shipping design unplaced and unrouted, so set its
time against re-checking another channel choice in your current flow before layout; that comparison
counts for more than the whole run's time against your note, since a first run includes learning.
The undocumented pairing is a control the runbook builds to show the check works, not a catch; set
anything else the checks caught beside what tends to go wrong in your flow. Then use the pattern on
a protected interface on one of your own boards, and time it against the same note: that second run
is the fairer measure.

## Files

- [The runbook](JS3_Part2_USB-through-ESD_Runbook.md), to read here;
  {download}`download it <JS3_Part2_USB-through-ESD_Runbook.md>` to give to your agent. It names
  the datasheets the agent fetches; there is no supplied input file.
- The reference solution, module
  [`jitxexamples.jumpstart_kits.js3_pin_assignment.usb_esd`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js3_pin_assignment/usb_esd)
  in the `jitxexamples` package (`pip install jitxexamples`).

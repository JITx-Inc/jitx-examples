# JS4: FPGA to LPDDR4X

**Shortcut:** Download the runbook, hand it to your AI coding agent, and tell it to follow the
file:

- {download}`Part 1 · LPDDR4X pin assignment <part1-lpddr4x-pins/JS4_Part1_LPDDR4X-Pin-Assignment_Runbook.md>`

Start a new agent session before you begin. Every step of a JS4 runbook drives a JITX skill, and a
skills install only takes effect in a session started after it.

JS4 connects the VP1002 FPGA from JS1 to an LPDDR4X memory. On one layout the FPGA offers every
byte swap and bit swap AMD's memory controller rules allow, the design asks for one interface, and
the choice of pins stays open until the board is routed. AMD documents that layout to the nibble,
and its pin positions are the ones AMD's VMK180, VCK190 and VPK120 boards use (VCK190, single
rank, has no CS1). It assumes
[JS0](../js0-setup/) and both parts of [JS1](../js1-stackup-components/) are done, because the
design uses the JS1 substrate and FPGA.

## The parts

### Part 1: LPDDR4X pin assignment

One x32 LPDDR4X interface from the VP1002 to a Micron MT53E1G32D2FW. The agent derives AMD's pin
rules from PG313, checks four AMD evaluation boards against them, offers every byte swap and bit
swap the rules allow on the single channel layout, flipped, on banks 702 and 701 (pin positions
from the boards), and applies UG863 timing limits. A legal code-routed assignment shows that the
limits bind, and an illegal one shows the rules enforced: its route is dropped. Vivado validation
of the chosen pins stays with you. Three `[HUMAN]` gates stop for you. Everything for it is on the
[Part 1 page](part1-lpddr4x-pins/).

## Reference solution

Verified code ships in the `jitxexamples` package, under
[`jitxexamples.jumpstart_kits.js4_fpga_lpddr4x`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js4_fpga_lpddr4x).

# JS3 Part 1: MCU Peripheral Muxing

**Shortcut:** {download}`Download the runbook <JS3_Part1_MCU-Peripheral-Muxing_Runbook.md>`, give it
to your AI coding agent, and tell it to follow the file.

An RP2040 drives a W25Q128JV serial flash over SPI and an LIS3DH accelerometer over I2C, and the
design leaves every bus pin for the RP2040 to choose, by driving `jitx-pin-assignment`. The ground
truth is Table 279 of the RP2040 datasheet: the agent checks the RP2040 model's pin options against
it and counts the legal pin choices, 34,000 for the two buses together. Verification designs then
route one legal pin set, which the tool keeps, and one illegal set, whose routes the tool drops.
What you learn is how to work with the pin options a part model offers: check them against the
datasheet, leave the choice of pins to the design, and confirm that a choice outside them is
dropped, so every legal pin choice stays open until the board is routed.

## Before you start

- Finish [JS0](../../js0-setup/) and [JS1 Part 1](../../js1-stackup-components/part1-stackup/).
  The designs bind the substrate you built there.
- Start a new agent session for this part. A skills install only takes effect in a session started
  after it.
- Have your JS1 Part 1 `board.py` at hand.
- Allow about 20 minutes.
- To compare this run with your current flow afterward, note now roughly how long assigning MCU
  peripheral pins and checking them against the datasheet takes your team, what tends to go wrong,
  and how long moving a bus to other pins takes, before layout. During the run, time it, time gate 2
  from your request to the agent's report, and note anything the checks caught.

## What the agent asks of you

Two `[HUMAN]` gates stop for you:

1. **Check the peripheral set and pins.** The agent shows you the buses the design requires, the
   RP2040 model's GPIO options for each I2C and SPI function beside Table 279, the counts of legal
   pin choices with their arithmetic, and the pins it proposes to route: one legal set and one
   with SDA and SCL swapped. Approve, or say what is wrong, before any pin is fixed.
2. **Move a bus.** Ask for the I2C bus on other pins (the runbook suggests GPIO 26 and 27). The
   agent checks them against Table 279 first, re-routes only the verification design, and shows
   you that the shipping design did not change.

## After the run

You can now check a part model's pin options against its datasheet and let a design keep any legal
choice. Gate 2 re-routes a verification design and leaves the shipping design unplaced and unrouted,
so set its time against moving a bus in your current flow before layout; that comparison counts for
more than the whole run's time against your note, since a first run includes learning. The set with
SDA and SCL swapped is a control the runbook builds to show the check works, not a catch; set
anything else the checks caught beside what tends to go wrong in your flow. Then use the pattern on
a pin plan in progress on one of your own boards, and time it against the same note: that second run
is the fairer measure.

## Files

- [The runbook](JS3_Part1_MCU-Peripheral-Muxing_Runbook.md), to read here;
  {download}`download it <JS3_Part1_MCU-Peripheral-Muxing_Runbook.md>` to give to your agent. It
  names the datasheets the agent fetches; there is no supplied input file.
- The reference solution, module
  [`jitxexamples.jumpstart_kits.js3_pin_assignment.mcu_muxing`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js3_pin_assignment/mcu_muxing)
  in the `jitxexamples` package (`pip install jitxexamples`).

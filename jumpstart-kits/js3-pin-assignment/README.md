# JS3: Pin Assignment

**Shortcut:** Download the runbook for the part you want, hand it to your AI coding agent, and tell
it to follow the file:

- {download}`Part 1 · MCU peripheral muxing <part1-mcu-muxing/JS3_Part1_MCU-Peripheral-Muxing_Runbook.md>`
- {download}`Part 2 · USB through an ESD array <part2-usb-esd/JS3_Part2_USB-through-ESD_Runbook.md>`

Start a new agent session before you begin any part. Every step of a JS3 runbook drives a JITX
skill, and a skills install only takes effect in a session started after it.

JS3 teaches pin assignment: a part offers the pin mappings its datasheet allows, a design asks for
what it needs, and the choice of pins stays open until the board is routed. Both parts drive
`jitx-pin-assignment` on real parts, and both assume [JS0](../js0-setup/) and
[JS1 Part 1](../js1-stackup-components/part1-stackup/) are done, because their designs bind the
JS1 substrate. The parts are independent, so either can be tackled first.

## The parts

### Part 1: MCU peripheral muxing

An RP2040 drives an SPI flash and an I2C accelerometer, and the RP2040 chooses which GPIO carry the
two buses. The agent checks the RP2040 model against the datasheet's GPIO function table before
relying on it, and verification designs show a legal pin set kept and an illegal one dropped. Two
`[HUMAN]` gates stop for you. Everything for it is on the [Part 1 page](part1-mcu-muxing/).

### Part 2: USB through an ESD array

USB 2.0 runs from an RP2040 through a 4-channel ESD array to a Type-C receptacle, with the ESD
channels left free within what the ESD datasheet documents. A USB 2.0 SI constraint covers the pair,
and verification designs prove it binds through the chosen channels by driving
`jitx-interconnect-constraints` as well. Two `[HUMAN]` gates stop for you. Everything for it is on
the [Part 2 page](part2-usb-esd/).

## Reference solutions

Verified code for both parts ships in the `jitxexamples` package, under
[`jitxexamples.jumpstart_kits.js3_pin_assignment`](https://github.com/JITx-Inc/jitx-examples/tree/main/src/jitxexamples/jumpstart_kits/js3_pin_assignment),
one module per part, named on that part's page.

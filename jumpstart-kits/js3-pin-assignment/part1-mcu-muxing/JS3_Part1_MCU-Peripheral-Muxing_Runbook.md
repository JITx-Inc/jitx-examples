<!--
JITX MCU Peripheral Muxing Runbook (JS3 · Part 1) · rev 1.1 · 2026-10-30
Give this file to your AI coding agent (Claude Code, Codex / GPT, or Devin) and tell it to follow
the file. Complete JS0 and JS1 Part 1 first, then START A NEW AGENT SESSION: a skills install only
takes effect in a session started after it.
-->

# JITX MCU Peripheral Muxing Runbook (JS3 · Part 1)

**Goal (for the agent):** a design in which an RP2040 drives a W25Q128JV flash over SPI and an LIS3DH accelerometer over I2C, with every bus pin left to pin assignment, and verification designs that show which pin choices it accepts, by driving the `jitx-pin-assignment` skill. The datasheets below are the only ground truth: Table 279 of the RP2040 datasheet for which GPIO carries which function, the flash and accelerometer datasheets for their wiring. Where they are silent, ask me. Don't open this kit's reference module (`jitxexamples.jumpstart_kits.js3_pin_assignment`) or anything in it, even where a skill offers it as an example: it is a finished answer to this task. Follow the steps in order. At a **[HUMAN]** step, stop and wait for me.

**Prerequisites:** JS0 and JS1 Part 1 are done; Python 3.12+ and `git` are available; you have the `board.py` that JS1 Part 1 produced.

**Datasheets.** Fetch each one. If a fetch fails, ask me for the PDF.

- Raspberry Pi Ltd, "RP2040 Datasheet": https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf. Table 279 is in section 2.19.2.
- Raspberry Pi Ltd, "Hardware design with RP2040": https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf.
- Winbond, "W25Q128JV" datasheet, Revision J: https://datasheet.lcsc.com/datasheet/pdf/d009d960f1daec6149edaa35b7dae856.pdf?productCode=C97521.
- STMicroelectronics, "LIS3DH" datasheet, DocID17530 Rev 2: https://www.st.com/resource/en/datasheet/lis3dh.pdf, or the copy at https://datasheet.lcsc.com/datasheet/pdf/fe5ca48c88184deb9f920ce8b9b86aeb.pdf?productCode=C15134.

**Parts.** Use these models from the `jitxexamples` package; don't write your own: `jitxexamples.components.mcus.raspberry_pi_RP2040.RP2040`, `jitxexamples.components.flash.winbond_W25Q128JVSIQ.W25Q128JVSIQ` and `jitxexamples.components.sensors.stmicroelectronics_LIS3DHTR.LIS3DHTR`.

## Steps

**0 · Preflight.**
Tell me this runbook's revision, from the comment at the top of the file, and confirm the `jitx-pin-assignment` skill is invocable.

**1 · Scaffold.**
Make a new, empty directory, run `jitx project layout init` in it, copy your JS1 Part 1 `board.py` in, and set up its environment:

```bash
# macOS / Linux
python3 -m venv .venv && source .venv/bin/activate

# Windows (PowerShell)
$env:PYTHONUTF8 = "1"; py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
```

```bash
pip install jitx jitxexamples pytest pyright ruff
jitx project dependencies upgrade
jitx runtime start --background
jitx design find
```

Check that `jitx --version` in the venv and the version `jitx runtime introspect` reports are on the same release line (4.6 and 4.6, say); if not, stop and tell me, because fixing it changes the runtime for the whole machine. Then build the seeded design with `jitx design build <target>`, taking the non-test target verbatim from `jitx design find`. If the build fails, stop and tell me.

**2 · Check the RP2040 model.**
Check the RP2040 model's pin options for the 12 single-pin functions (SDA and SCL of I2C0 and I2C1; RX, CSn, SCK and TX of SPI0 and SPI1) against Table 279, with a test that holds the table's lists. Then count the legal pin choices, with a test for each: Table 279 gives 113 for one I2C bus (I2C0 8 × 8 plus I2C1 7 × 7), 400 for one SPI bus with chip select (SPI0 4 × 4 × 4 × 4 plus SPI1 4 × 4 × 3 × 3), and 34,000 for both with no GPIO shared. If the model or a count differs from the table, stop and tell me.

**3 · The design.**
Wire the RP2040 to the flash over SPI with chip select and to the accelerometer over I2C, each part as its datasheet says, with the bus pins left to pin assignment. Add a design that binds your JS1 substrate.

**4 · [HUMAN] Check the pins.**
Stop and show me: the buses the design requires and which part each serves; the model's pin options beside Table 279; the three counts with their arithmetic; one legal pin choice for every bus line; and an illegal variant with the I2C SDA and SCL pins swapped. Give the Table 279 entry for each pin. Wait for my approval, because the verification designs fix those pins.

**5 · Verify.**
Write two verification designs that place the three parts and code-route every bus line: one on the legal pins, one on the illegal variant. Build all three designs and check each one's issues through the runtime, as the skill shows. The legal design reports `met Satisfied` and no dropped route; the illegal one reports `Code route dropped: its ends are on different nets` for its two I2C routes. Then run `jitx-code-review`, fix every CRITICAL finding and each WARNING you can, and report every result to me, with the reason for each WARNING you keep. If any **Done when** line that applies so far fails, report it and stop.

**6 · [HUMAN] Move a bus.**
Invite me to move a bus, and suggest I say: *"Move the I2C bus to GPIO 26 and 27."* Wait for me to ask. Check my pins against Table 279 before you route them; if one is not allowed, tell me which entry rules it out and wait for me to choose again. Change only the legal verification design, then run step 5 again in full and report before and after.

## Done when

- The RP2040 model's SPI and I2C pin options match Table 279, checked by a test that holds the table's lists.
- The counts are 113, 400 and 34,000, each checked by a test that derives it from the model's options.
- The shipping design requires an SPI bus with chip select and an I2C bus from the RP2040, wires the flash and the accelerometer as their datasheets say, binds your JS1 substrate, and has no placement and no routes.
- Step 4 stopped before the verification designs fixed any pins.
- The legal verification design reports no dropped route; the illegal one reports both I2C routes dropped.
- `pyright` passes with zero suppressions; `pytest` is green; `jitx design find` shows no import failures; every design builds; and `jitx-code-review` leaves no CRITICAL finding (every result reported, with the reason for each WARNING kept), after step 5 and again after step 6.
- After step 6 the moved bus routes with no dropped route, and the shipping design is unchanged.

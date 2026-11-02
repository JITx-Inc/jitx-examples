<!--
JITX USB-through-ESD Pin Assignment Runbook (JS3 · Part 2) · rev 1.2 · 2026-10-30
Give this file to your AI coding agent (Claude Code, Codex / GPT, or Devin) and tell it to follow
the file. Complete JS0 and JS1 Part 1 first, then START A NEW AGENT SESSION: a skills install only
takes effect in a session started after it.
-->

# JITX USB-through-ESD Pin Assignment Runbook (JS3 · Part 2)

**Goal (for the agent):** a design that carries USB 2.0 from an RP2040 through a Nexperia PUSB3FR4 ESD array to a USB Type-C receptacle, with the ESD channels left to pin assignment and a USB 2.0 SI constraint on the pair, and verification designs that prove the constraint binds through the channels, by driving the `jitx-pin-assignment` and `jitx-interconnect-constraints` skills. The datasheets below are the ground truth, `jitxlib.protocols.usb` gives the constraint numbers and your JS1 substrate the routing structures; where they are silent, ask me. Don't open this kit's reference module (`jitxexamples.jumpstart_kits.js3_pin_assignment`) or anything in it, even where a skill offers it as an example: it is a finished answer to this task. Follow the steps in order. At a **[HUMAN]** step, stop and wait for me.

**Prerequisites:** JS0 and JS1 Part 1 are done; Python 3.12+ and `git` are available; you have the `board.py` that JS1 Part 1 produced.

**Datasheets.** Fetch each one. If a fetch fails, ask me for the PDF.

- Nexperia, "PUSB3FR4 ESD protection for ultra high-speed interfaces", product data sheet, 12 July 2018: https://assets.nexperia.com/documents/data-sheet/PUSB3FR4.pdf. Nexperia's site may refuse an automated download; the copy at https://datasheet.lcsc.com/datasheet/pdf/973b1dae6d18992ab9432880e89c8003.pdf?productCode=C294620 is the same document.
- Raspberry Pi Ltd, "RP2040 Datasheet": https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf.
- Microchip, "Introduction to USB Type-C", AN1953 (DS00001953A): https://ww1.microchip.com/downloads/en/Appnotes/00001953A.pdf.

**Parts.** Use these models from the `jitxexamples` package; don't write your own: `jitxexamples.components.mcus.raspberry_pi_RP2040.RP2040` (its USB pins and series resistors), `jitxexamples.components.digital_isolators.PUSB3FR4.PUSB3FR4` and `jitxexamples.components.connectors.molex_2012670005.USBTypeCComponent`.

## Steps

**0 · Preflight.**
Tell me this runbook's revision, from the comment at the top of the file, and confirm the `jitx-pin-assignment` and `jitx-interconnect-constraints` skills are invocable.

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

**2 · The channel freedom.**
Check the PUSB3FR4 model's pins against the datasheet's pinning table and its land pattern against the reflow soldering footprint, with a test. Then work out which ESD channels may carry D+ and D-, each with the datasheet table or figure behind it. USB 2.0 polarity is fixed end to end, so only the channel choice is free. The datasheet supports four mappings: CH1 with CH2 or CH3 with CH4, either channel of the pair on D+. If you find a different number, stop and tell me.

**3 · The provider.**
Write a provider around the PUSB3FR4 that offers exactly those mappings, with a test that reads them back from it. Put each channel pin and the n.c. pin opposite it in the datasheet's pass-through layout on one net, with a test. No SI constraint yet.

**4 · [HUMAN] Confirm the channel freedom.**
Stop and show me: each offered mapping beside its datasheet table or figure; the pairings you leave out and why; and how the design joins each channel pin to the n.c. pin opposite it. Wait for my approval, because the SI constraint builds on this.

**5 · The circuit and the constraint.**
Run the RP2040's USB pair through the provider to the receptacle, wired as a USB 2.0 device per AN1953 (both rows' D+ and D- contacts joined, a 5.1 kΩ pull-down on each CC pin). Constrain the pair from the RP2040's USB pins to the receptacle's A6 and A7 contacts with the USB 2.0 skew and loss numbers from `jitxlib.protocols.usb`, on JS1's DIFF-100. USB 2.0 asks for 90 Ω: tell me the gap and never invent a width. jitxlib's 3.75 ps skew limit is far tighter than a Full Speed link needs, so when you report, say the proofs show the constraint binding, not compliance. Add a design that binds your JS1 substrate.

**6 · Verify.**
Write three verification designs that place the parts and code-route the pair: D+ on CH1 and D- on CH2; D+ on CH4 and D- on CH3; and D+ on CH1 and D- on CH3, which the datasheet does not document. Build all four designs and check each one's issues through the runtime, as the skills show. For this task:

- Each offered choice reports a Loss line on each leg and a Skew line.
- The undocumented one reports `Code route dropped: it conflicts with other connections` and no Skew line.
- The shipping design reports `No path for signal constraint` on both legs.
- JS1's vias have no SI models: report the placeholder-model lines; don't model the vias.
- If DIFF-100 doesn't fit at the pads, give the proof routes the substrate's single-ended neck structure and tell me; keep DIFF-100 on the shipping constraint.
- Report each skew against its limit; matching it is not this task.

Then run `jitx-code-review`, fix every CRITICAL finding and each WARNING you can, and report every result to me, with the reason for each WARNING you keep. If any **Done when** line that applies so far fails, report it and stop.

**7 · [HUMAN] Another channel choice.**
Invite me to ask for another routing, and suggest I say: *"Prove D+ on CH2 and D- on CH1 as well."* Wait for me to ask. Add a verification design for it; the provider and the shipping design do not change. If I ask for a pairing the datasheet does not document, such as CH2 with CH3, tell me what the datasheet would have to show and don't offer it. Then run step 6 again in full and report before and after.

## Done when

- The PUSB3FR4 model matches the datasheet's pinning table and reflow soldering footprint, checked by a test.
- The provider offers exactly the four mappings of step 2, each traced to the datasheet, checked by a test that reads them from the provider.
- Each channel pin and the n.c. pin opposite it are on one net, checked by a test. A pin model between them does not count: those pins have no path through the part.
- Step 4 stopped before any SI constraint was written.
- The shipping design carries the constraint with `jitxlib.protocols.usb`'s USB 2.0 numbers on DIFF-100, binds your JS1 substrate, has no placement and no routes, and reports `No path for signal constraint` on both legs. The 90 Ω gap is reported, with no width invented.
- Each offered verification design reports a Loss line on both legs and a Skew line; the undocumented one reports a dropped route and no Skew line.
- `pyright` passes with zero suppressions; `pytest` is green; `jitx design find` shows no import failures; every design builds; and `jitx-code-review` leaves no CRITICAL finding (every result reported, with the reason for each WARNING kept), after step 6 and again after step 7.
- After step 7 the new channel choice reports a Loss line on both legs and a Skew line.

<!--
JITX Circuits-from-Datasheet Runbook (JS2) · rev 2.0 · 2026-10-30
Give this file to your AI coding agent (Claude Code, Codex / GPT, or Devin) and tell it to follow
the file. Complete JS0 first, then START A NEW AGENT SESSION: a skills install only takes effect in
a session started after it.
-->

# JITX Circuits-from-Datasheet Runbook (JS2)

Each step below is a request, written the way you would ask an agent for the work. Follow them in
order; at a **[HUMAN]** step, stop and wait for me. Drive `jitx-circuit-builder` for the circuits
and the base `jitx` skill for the project. The ground truth is the Microchip KSZ9031RNX data sheet,
DS00002117:
<https://ww1.microchip.com/downloads/aemDocuments/documents/UNG/ProductDocuments/DataSheets/KSZ9031RNX-Data-Sheet-DS00002117.pdf>.
Where it leaves a choice, make it and tell me what you chose. Don't open
`jitxexamples.jumpstart_kits.js2_circuits`, even where a skill offers it as an example: it is a
finished answer to this task.

Every part comes from `jitxexamples.components`; model none:

- `ethernet_phys.microchip_KSZ9031RNX.KSZ9031RNX`, the PHY;
- `crystals.seiko_epson_TSX_3225.TSX3225`, a 25 MHz crystal, 9 pF load, +/-10 ppm at 25 C and
  over -20 to 75 C;
- `fets_p_ch.NTF6P02T3G.NTF6P02T3G`, the MOSFET for the PHY's core LDO;
- `power_switchmode.texas_instruments_TPS62933DRLR.TPS62933DRLRCircuit`, the buck;
- `connectors.bel_fuse_0826_1G1T_23_F.Bel_0826_1G1T_23_F`, the RJ45 jack with magnetics.

## Steps

**0 · Preflight.**
Tell me this runbook's revision, from the comment at the top, and confirm `jitx-circuit-builder` is
invocable.

**1 · Project.**
Set up a new JITX project for this board in an empty directory, with `jitxexamples` as a dependency
and its example parts catalogue as the parts source, and build the seeded design.

**2 · Straps.**
Make a typed strap configuration from the strap-in table (Table 2-2) that rejects an address or mode
the table doesn't define.

**3 · [HUMAN] Strap configuration.**
Show me your strap table beside the data sheet's, with the resistor for a 1 and for a 0 on each pin,
and propose PHY address 0, mode 1111, no 125 MHz clock out and single-LED mode. Wait for my choice.

**4 · PHY circuit.**
Build the KSZ9031RNX application circuit, taking the strap configuration as an argument, behind
typed ports, with RESET_N and INT_N as single-pin ports out to a host. Make the 1.2 V core with the on-chip LDO
controller and the NTF6P02T3G, following Figure 8 of Microchip's ANLAN206
(<https://ww1.microchip.com/downloads/en/AppNotes/ANLAN206-UNG.pdf>): 100 kOhm from gate to source,
10 uF on the source, 10, 1 and 0.1 uF on the drain, and a trace from the drain to AVDDL pin 4,
which the controller senses. The catalogue has no ferrite bead, so the core supplies share one net.
Tell me how the MOSFET measures against the data sheet's Section 11.0, and what the data sheets
leave unverified. One decoupling capacitor per supply pin; the assembler's smallest package is
0402. Expect nine strap resistors (five up and four down at the proposed configuration), and,
besides the MOSFET's own, five capacitors plus one bulk on 3.3 V and nine plus three bulk on
1.2 V; if yours differ after you go back to the data, stop and tell me.

**5 · [HUMAN] Input voltage.**
Size a 3.3 V buck for this board's load: propose an input voltage and the smallest output current
the catalogue has an inductor for. Show me the regulator's checks and wait for my choice.

**6 · Board.**
Compose the board from the buck, the PHY circuit and the jack, with the PHY's MAC and host
interfaces as the board's ports: expect three sub-circuits. Fix the jack's position and let the
rest float. Check the data
sheet's power-up order holds, and leave SI constraints and routing for JumpStart 4.

**7 · Verify.**
Run the skills' checks, a build of the board and the parts checks, and `jitx-code-review`; fix what
they find, and report each result.

**8 · [HUMAN] Close the loop.**
Invite me to change the straps, suggesting: *"set the PHY address to 5 and advertise 1000BASE-T
full-duplex only, then tell me which resistors moved."* Change only the configuration the design
passes in, and run step 7 again.

## Done when

- Nine strap resistors, one on each Table 2-2 pin, each pulled the way the chosen configuration
  needs: five up and four down at the step 3 proposal.
- In the PHY circuit, besides the MOSFET's own, five capacitors plus one bulk on 3.3 V and nine
  plus three bulk on 1.2 V, each on a `ShortTrace` to its pin; two crystal load capacitors.
- LDO_O drives the NTF6P02T3G's gate, with Figure 8's gate resistor and capacitors and the sense
  trace to AVDDL pin 4, and the code says how the MOSFET measures against Section 11.0 and what is
  unverified.
- The board holds three sub-circuits. Its ports are the input as `Power`, `RGMII` and `MIIM`, with
  RESET_N and INT_N as single-pin ports, and each member reaches the pin the data sheet names.
- The checks, tests and build pass, the parts check passes with no `IDEAL-` part, and
  `jitx-code-review` leaves no CRITICAL finding, after step 7 and after step 8.
- Steps 3 and 5 stopped. From the step 3 proposal, the step 8 change moves four strap resistors
  (PHYAD2, PHYAD0, MODE1 and MODE0) and nothing else; otherwise, exactly the resistors on pins
  whose Table 2-2 bit differs between the two configurations.

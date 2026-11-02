<!--
JITX Versal LPDDR4X Pin Assignment Runbook (JS4 · Part 1) · rev 1.3 · 2026-10-30
Give this file to your AI coding agent (Claude Code, Codex / GPT, or Devin) and tell it to follow
the file. Complete JS0 and both parts of JS1 first, then START A NEW AGENT SESSION: a skills
install only takes effect in a session started after it.
-->

# JITX Versal LPDDR4X Pin Assignment Runbook (JS4 · Part 1)

**Goal (for the agent):** a design that connects one x32 LPDDR4X interface of the VP1002 you built in JS1 Part 2 to a Micron MT53E1G32D2FW, with AMD's pin rules encoded as `provide` options so that JITX picks the pin assignment, UG863 timing constraints on the link, and verification designs that show a legal assignment measured and an illegal one rejected. Drive the `jitx-pin-assignment` and `jitx-interconnect-constraints` skills, and `jitx-component-modeler` for the pin file. AMD's documents below are the ground truth, with four AMD evaluation boards as worked examples of the rules. Where the documents place a pin only to the nibble, you may encode the position every board using that layout agrees on, marked as inferred, with the boards named. Where no board uses a layout you encode but boards use its flipped twin, you may encode the mirror of their position, marked as inferred by mirroring. Where the documents are silent and the boards disagree, stop and tell me. Validating the pinout in Vivado is my step: export no XDC and claim no Vivado legality. Don't open this kit's reference module (`jitxexamples.jumpstart_kits.js4_fpga_lpddr4x`) or anything in it, even where a skill offers it as an example: it is a finished answer to this task. Follow the steps in order. At a **[HUMAN]** step, stop and wait for me.

**Prerequisites:** JS0, JS1 Part 1 and JS1 Part 2 are done; you have the `board.py` that JS1 Part 1 produced and the VP1002 package that JS1 Part 2 produced (generator, generated module, circuit); Python 3.12+ and `git` are available; you can fetch files from amd.com and github.com.

**Documents.** Fetch each one. If a fetch fails, tell me what you tried and ask me for the file. Record each document's revision and date where you cite it, and keep vendor files in the gitignored `.context/`.

- AMD PG313, *Versal Adaptive SoC Programmable Network on Chip and Integrated Memory Controller LogiCORE IP Product Guide*, its LPDDR4/4X pin rule and interface topics: https://docs.amd.com/r/en-US/pg313-network-on-chip.
- AMD Vivado-Design-Tutorials, tag 2025.2, `Versal/PCB_Design/Memory_Pinouts/README.md`, Appendix B: https://github.com/Xilinx/Vivado-Design-Tutorials/tree/2025.2/Versal/PCB_Design/Memory_Pinouts.
- AMD AM013, *Versal Adaptive SoC Packaging and Pinouts Architecture Manual*, "About ASCII Package Files": https://docs.amd.com/r/en-US/am013-versal-pkg-pinout.
- The board pinouts. VMK180, VPK120 and VEK280: `part0_pins.xml` and `board.xml` under `boards/Xilinx/vmk180/production/3.3`, `boards/Xilinx/vpk120/production/1.2` and `boards/Xilinx/vek280/production/1.2` of https://github.com/Xilinx/XilinxBoardStore at tag 2025.2. VCK190: `Versal/Memory_and_NoC/NoC_DDRMC/Performance_Tuning/finished_design/design/lpddr4_mc3_vck190.xdc` in Vivado-Design-Tutorials tag 2025.2. Each board's package pin file (`xcvm1802vsva2197pkg.txt`, `xcvc1902vsva2197pkg.txt`, `xcvp1202vsva2785pkg.txt`, `xcve2802vsvh1760pkg.txt`) comes from AMD's Versal package pinout downloads, as the VP1002's did in JS1 Part 2.
- AMD UG863, *Versal Adaptive SoC PCB Design User Guide*, its LPDDR4/4x timing and physical design rules: https://docs.amd.com/r/en-US/ug863-versal-pcb-design.

**Parts and protocol.** Use these from the `jitxexamples` package; don't write your own: the memory `jitxexamples.components.memories.MT53E1G32D2FW_046_WT_B.MT53E1G32D2FW_046_WT_B`, and `LPDDR4`, `LPDDR4Constraint` and `LPDDR4ConstraintParams` from `jitxexamples.protocols.memory.lpddr4`. If the controller drives one CKE per channel, base the FPGA's interface bundle on `LPDDR4SharedCKE` from the same module.

## Steps

**0 · Preflight.**
Tell me this runbook's revision, from the comment at the top of the file, and confirm the `jitx-pin-assignment`, `jitx-interconnect-constraints` and `jitx-component-modeler` skills are invocable.

**1 · Scaffold.**
Make a new, empty directory, run `jitx project layout init` in it, copy in your JS1 Part 1 `board.py` and your JS1 Part 2 VP1002 package, and set up its environment:

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

Check that `jitx --version` in the venv and the version `jitx runtime introspect` reports are on the same release line (4.6 and 4.6, say); if not, stop and tell me, because fixing it changes the runtime for the whole machine. Then build the seeded design with `jitx design build <target>`, taking the non-test target verbatim from `jitx design find`, and run your JS1 Part 2 tests. If either fails, stop and tell me.

**2 · The memory controller pins.**
Extend your JS1 Part 2 generator so the generated module also carries each DDRMC triplet pin's "DDRMC Only" value and triplet position (the `MxP` number in its name). Change no existing port, pad mapping or count, and keep the generator's `--check` and your JS1 Part 2 tests passing. The VP1002 has one triplet, M0, on banks 700 to 702: 162 positions, 116 `YES`, 22 `YES_PLUS_GC` and 24 `NO`. If your counts differ, stop and tell me.

**3 · The rule set.**
Write AMD's LPDDR4/4X pin rules as data in triplet positions (bank, nibble, pin), with a rule table in the module docstring that cites document, revision and topic for each row. Cover every documented base layout (single channel, dual channel, pin efficient), flipped and non-flipped. Every board's standard layout is flipped, so encode the non-flipped positions as mirrors (bank b to 2 - b, nibble n to 7 - n, N8 and the pin within its nibble kept), citing PG313's flipped and non-flipped nibble figures and VEK280's M0 and M2 interfaces for the mirror. Test that every board interface is in the rule set: VMK180 has 4, VCK190 4, VPK120 6 and VEK280 6. If you find a different number, stop and tell me.

**4 · [HUMAN] Confirm the rule table.**
Stop and show me: the rule table; each inferred position with the boards behind it; the board test results; and the layout you will offer on banks 702 and 701, with what you leave out and why. For this input that is the single channel x32 layout, flipped, the one channel 0 of VMK180, VCK190 and VPK120 uses: show that each fixed position and each byte slot's DQS_T, DQS_C and DMI match those boards pin for pin, and name any position no board carries (VCK190 has no CS1). Then, as its own item, show how many CKE pins the controller drives per channel and ask me to confirm it: the boards map one per channel, while UG863 Table 1 lists CKE0 and CKE1 per channel (CKE1 dual rank only). Wait for my approval, because the `provide` options encode this table.

**5 · The offer.**
Offer that layout on a circuit around your VP1002, with every swap the rules allow: 25 fixed pins (per channel six CA, the CK pair, CKE, CS0 and CS1, plus RESET_N and the system clock pair, with one CKE per channel if that is what I confirmed) and four byte slots of 11 pins (DQS pair, DMI, eight DQ). A byte may take either slot of its channel and any order of its eight DQ: 2 × 2 × (8!)^4 = 10,571,633,173,463,040,000 assignments. Test that count from your rule data. Don't enumerate assignments as options; if the skill offers no way to express the bit swap without one option per order, stop and tell me.

**6 · [HUMAN] Confirm the constraint values.**
Stop and show me: each timing limit you will apply, as `LPDDR4ConstraintParams` fields beside the UG863 row and text it comes from; each UG863 rule you will not apply, and why; and the routing structures you will use against UG863's impedance targets. `LPDDR4ConstraintParams` defaults come from UG583: set every field UG863 governs and turn off any rule UG863 does not have. If JS1's substrate has none in range, name the closest and the gap, and never invent a width. Wait for my approval, because the constraints build on these values.

**7 · The design.**
Write the shipping design: your JS1 substrate, the step 5 circuit and the Micron memory, the interface required from the FPGA and netted to the memory with plain nets, and the approved limits from the FPGA's pins to the memory's balls. Build it and check its issues through the runtime, as the skills show. With no routes nothing measures yet. For this input there are 66 constraints (per channel the CK pair, two CKE, two CS and six CA, and per byte the DQS pair, CK minus DQS, DMI and eight DQ). Each reads `NOT MET` with `Unassigned Pin on Path`, except the four CKE paths, which read `No path for signal constraint`. One `met Satisfied` group makes 67 in all. If you structure the constraints differently, tell me how your count maps to these.

**8 · Verify.**
Write two verification designs that place the parts and code-route one channel B byte lane, its channel's CK pair, the CKE (from the FPGA pin to one CKE ball and on to the other) and one CA bit. The legal one routes the byte into the slot the other channel B byte takes by default, with its DQ reordered. The illegal one sends one DQ to a channel A slot. Build them and check their issues. For this input:

- The legal design reports 15 Skew lines: the CK pair, each CKE ball to CK, CA to CK, the DQS pair, CK minus DQS, DMI to DQS and each of the eight DQ to DQS.
- The illegal design reports `Code route dropped: its ends are on different nets`, and the misrouted DQ has no Skew line.
- The Micron's balls are too close for the surface layer: route on the inner stripline layers through microvias in the pads. If a route reports `Unable to find path for requested route`, move it to another stripline layer and tell me.
- Report what UG863's physical rules would flag (vias per signal, a lane split across layers), the `Using placeholder model` lines from JS1's unmodeled vias (don't model the vias), and each skew against its limit. Matching the skews is not this task.

Then run `jitx-code-review`, fix every CRITICAL finding and each WARNING you can, and report every result to me, with the reason for each WARNING you keep. If any **Done when** line that applies so far fails, report it and stop.

**9 · [HUMAN] Another assignment.**
Invite me to ask for another proof, and suggest I say: *"Prove the other channel B byte in its own verification design: route it into the slot the byte swap left it, with its DQ in order."* Wait for me to ask. Add a standalone verification design for it; the offer and the shipping design do not change. If I ask for an assignment the rules forbid, such as a channel A byte in a channel B slot, tell me which rule forbids it and don't offer it. Then run step 8 again in full and report before and after.

## Done when

- The generated VP1002 module carries the DDRMC column and triplet position of all 162 M0 pins (116 `YES`, 22 `YES_PLUS_GC`, 24 `NO`), its existing ports, pads and counts are unchanged, and the generator's `--check` and your JS1 Part 2 tests pass.
- The rule table cites document, revision and topic for every row and covers every documented base layout, flipped and non-flipped; every inferred position names its boards.
- A test shows all 20 board interfaces (VMK180 4, VCK190 4, VPK120 6, VEK280 6) are in the rule set.
- Step 4 stopped before any `provide` was written, with the CKE count confirmed as its own item, and step 6 stopped before any constraint.
- The offer covers the 10,571,633,173,463,040,000 assignments of step 5, and no others, without enumerating them, and a test computes that count.
- The shipping design binds your JS1 substrate, has no routes, and reports no measurement: each of the 66 constraints of step 7 reads `Unassigned Pin on Path` and the unrouted CKE paths `No path for signal constraint`. Every limit traces to its UG863 row; the impedance gap is reported, with no width invented.
- The legal verification design reports its 15 Skew lines; the illegal one reports the dropped route and no Skew line for the misrouted DQ.
- `pyright` passes with zero suppressions; `pytest` is green; `jitx design find` shows no import failures; every design builds; and `jitx-code-review` leaves no CRITICAL finding (every result reported, with the reason for each WARNING kept), after step 8 and again after step 9.
- After step 9 the new verification design reports a Skew line on each path it routes, with no dropped route.

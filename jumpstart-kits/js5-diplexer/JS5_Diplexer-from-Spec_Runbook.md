<!--
JITX Diplexer-from-Spec Runbook (JS5) · rev 0.10 · 2026-11-11
Before you start: `jitxlib-ansys`, the JITX library that drives HFSS, and the JITX HFSS
optimization plugin are not public. Contact JITX for access.
Give this file and the vendor files it lists to your AI coding agent (Claude Code) and tell it to
follow the file. Complete JS0 first, install the JITX HFSS optimization plugin 0.3.3 or later
beside the JITX skills, then START A NEW AGENT SESSION: a skills install only takes effect in a
session started after it.
-->

# JITX Diplexer-from-Spec Runbook (JS5)

Before you start: `jitxlib-ansys`, the JITX library that drives HFSS, and the JITX HFSS
optimization plugin are not public. Contact JITX for access.

Each step below is a request, written the way you would ask an agent for the work. Follow them in
order; at a **[HUMAN]** step, stop and wait for me. Drive `jitx-hfss-optimization` for the
campaign and the jitx-skills it names for the design. The point is the HFSS campaign: get to its
first solve quickly, let its loop do the tuning, and use its tools rather than building your own.
Where the requirements leave a choice, make it and tell me what you chose. Work from the vendor
files saved beside this runbook, and fetch nothing from the web.

**Prerequisites:** JS0 is done; `jitxlib-ansys` and the JITX HFSS optimization plugin 0.3.3 or later
are installed; Claude, JITX 4.6 and Ansys Electronics Desktop 2026 R1 with an HFSS licence run on
this Linux machine, with `ANSYSEM_ROOT` (the AEDT install root) and `ANSYSEM_ROOT261` set in the
agent's shell. These vendor files, downloaded in a browser, are saved beside this runbook:

- Würth Elektronik's HFSS model of the SMA jack,
  [`ANSYS_60312202114514 (rev25a).a3dcomp`](https://www.we-online.com/components/products/download/ANSYS_60312202114514%20%28rev25a%29.a3dcomp),
  and the jack's [data sheet](https://www.we-online.com/components/products/datasheet/60312202114514.pdf).
- Kyocera AVX's [Accu-P 0402 S-parameter archive](https://www.kyocera-avx.com/download/rfs-design-tools/AccuP-0402_S2P.zip)
  and [Accu-P data sheet](https://datasheets.kyocera-avx.com/accu-p.pdf).
- Murata's [LQW15AN_80 reference specification](https://pim.murata.com/asset/pim4/inductor/JELF243A-0100_PDF_INDUCTOR).

## Requirements

Design a 50 Ω diplexer that beats the Mini-Circuits ZDPLX-592-S+: common port in, low port
2.4 to 2.5 GHz, high port 5.1 to 5.9 GHz. Meet the nominal column at nominal part values and the
worst-corner column at the worst tolerance corner. Measure at the SMA jacks, launches included.

| Metric | Band (GHz) | Nominal | Worst corner |
|---|---|---|---|
| Insertion loss, low port | 2.4 to 2.5 | ≤ 0.8 dB | ≤ 0.6 dB |
| Insertion loss, high port | 5.1 to 5.9 | ≤ 0.9 dB | ≤ 0.4 dB |
| Return loss, low port | 2.4 to 2.5 | ≥ 20 dB | ≥ 10 dB |
| Return loss, high port | 5.1 to 5.9 | ≥ 20 dB | ≥ 8 dB |
| Return loss, common port | 2.4 to 2.5 | ≥ 20 dB | ≥ 10 dB |
| Return loss, common port | 5.1 to 5.9 | ≥ 20 dB | ≥ 8 dB |
| Stop-band isolation, low port | 5.1 to 5.9 | ≥ 45 dB | ≥ 38 dB |
| Stop-band isolation, high port | 2.4 to 2.5 | ≥ 40 dB | ≥ 35 dB |

Architecture: an LC low-pass section to the low port and an LC high-pass section to the high port,
joined at the common port. Each section is high impedance at the junction in the other's band: the
low-pass starts with a series inductor at the junction, the high-pass with a series capacitor that
a shunt inductor resonates in the low band. Each section gets its isolation from transmission
zeros, made by series-LC branches to ground, at or near the other port's band. Printed shorted
stubs are welcome as the shunt inductors, with a capacitor at a stub's tip to make a zero. Use the
catalogue's tightest-tolerance parts. The order of each section and where its zeros sit are yours
to find.

It handles 1 W RF input and operates from −40 to 85 °C. Build it on the JLCPCB 2-layer 0.76 mm
RO4350B board from `jitxlib.jlcpcb`, with 0402 passives from the `jitxexamples` parts catalogue,
printed stubs, and a Würth 60312202114514 edge-launch SMA jack from `jitxexamples` on the board
edge at each port. The jack is specified for a 1.6 mm board: use it on the 0.76 mm board, its
bottom tabs hanging below. Its pads run to the board edge as its data sheet draws them, the one
exception to the edge-clearance floor. The board's ground vias go in the jack's ground pads,
plated and left open, with that in the fab notes. Open the top mask over the RF copper. The board
takes the ZDPLX's standard case outline: 31.75 mm square; common port at the left edge and high
port at the right, both 16.00 mm from the top edge; low port at the bottom edge, 16.00 mm from the
left; two 3.18 mm through holes at the top-left and bottom-right corners, 25.40 mm apart each way.

## Steps

**0 · Preflight.**
Tell me this runbook's revision, from the comment at the top, confirm `jitx-hfss-optimization`,
`jitx-project-builder`, `jitx-code-review` and `jitx-jlcpcb` are invocable, and tell me the installed `jitx`,
`jitxlib-ansys` and HFSS optimization plugin versions.

**1 · Spec.**
Start a campaign in an empty directory from the requirements above, with no AEDT file. Expect
eight scored metrics, each with a nominal and a worst-corner floor.

**2 · [HUMAN] Targets.**
Show me the scored targets as you will score them, and everything the requirements and step 7 leave
open as one list with a default for each. Wait for my answers.

**3 · Architecture.**
Pick each section's order, zeros and starting values from closed-form filter design, and check
them once at circuit level, junction included, with the catalogue parts' models and tolerances.
Write the rough path with each floor's worst-corner penalty, keeping about 0.15 dB of each
insertion-loss floor for layout and launches. Compare no other topology and search no values with
your own optimizer: the HFSS campaign does the tuning. If the design cannot fit 0.6 / 0.4 dB at
the worst corner, tell me by how much and propose the ZDPLX typical (0.8 / 0.9 dB) instead.

**4 · [HUMAN] Rough path.**
Show me `rough-path.md` and wait for my approval or my changes.

**5 · [HUMAN] Plan.**
Plan the build of the signed path with `jitx-project-builder`, on the outline in the requirements.
Show me the plan and wait for my approval.

**6 · Build.**
Build the approved plan. Expect three edge-launch ports, two holes, two copper layers and no copper
between any 0402 part's two lands.

**7 · Simulation setup.**
Set up two experiments with the skill: a launch-thru fixture (two jacks back to back on a short 50 Ω
line, from the board's launch code) and the whole board. Jack ports through Würth's model; every
0402 part a lumped port closed with its vendor S-parameters where the files beside this runbook give
them, else its data-sheet RLC, at every tier (`jitxlib-ansys` does not yet close a part as a port:
write that closure); an interpolating sweep, 0.5 to 6.4 GHz; no field export. Score step 2's nominal
floors, each tightened by its step 3 penalty. Run the skill's checks and a no-solve export of each;
fix what they find in the design.

**8 · [HUMAN] Ready to simulate.**
Show me the acceptance block with what built each piece, each export's geometry summary, and the
board. Wait for my go.

**9 · [HUMAN] Principles and budget.**
Write the operating principles for each section and run their checks. Show me the targets and what
may change and what is pinned, and propose a budget in campaign rounds and launch calibration
solves. Wait: I write the budget file.

**10 · Launch.**
Tune one launch on the fixture before the board's first solve. First state its return-loss and
insertion-loss targets, derived from the diplexer's floors. Report each calibration solve against
them, then put the tuned launch at all three ports.

**11 · Optimize.**
Run the campaign within my budget. After each solve, re-pick the part values from the solved board
before you change copper. After each round, give me one line per scored metric against its floor.

**12 · Verify.**
When the targets hold or the budget runs out, solve the final design at the confirm tier and score
every floor from that solve at nominal and at the worst corner. Check the 1 W rating and the
operating temperature range against the parts' data sheets. Run the skills' checks, a build and
`jitx-code-review`; fix what they find, and report each result.

**13 · Fabrication packet.**
Export the final design's JLCPCB fabrication packet with `jitx-jlcpcb`, with the fab notes beside
its order sheet. Show me the packet's files and its order settings, and tell me what I still set by
hand on the order form.

## Done when

- `rough-path.md` carries my approval, and every later change to a section's topology, a part
  family, the substrate or the reference planes carries an approved addendum.
- The board is the outline in the requirements, on two copper layers of a JLCPCB RO4350B substrate
  from `jitxlib.jlcpcb`, with no copper between any 0402 part's two lands, and every passive
  resolves from the catalogue to an orderable part number, none `IDEAL-`.
- A Würth 60312202114514 jack sits at each of the three port positions in the requirements, each
  with the launch tuned at step 10. The tuning's last calibration solve is reported against the
  targets stated there, beside the jack's 1.6 mm specified board thickness and the board's own.
- The top mask is open over the RF copper, the open in-pad via note is in the fab notes and not on
  the legend, and only the jack pads are exempt from the edge-clearance floor.
- The final design's JLCPCB packet is exported, with the fab notes beside its order sheet.
- A confirm-tier solve of the final design, with every 0402 part as a port, scores all sixteen
  floors from step 2, each met or reported with its shortfall, and states the worst-corner
  insertion loss on each port against 0.6 / 0.4 dB (or the fallback I approved) and against the
  ZDPLX typical.
- The 1 W and temperature checks are reported per part, with the part data sheet each rating came
  from.
- The skill's checks, the tests and a build pass, and `jitx-code-review` leaves no CRITICAL
  finding, after step 12.
- Steps 2, 4, 5, 8 and 9 stopped, and the agent never wrote the budget file.

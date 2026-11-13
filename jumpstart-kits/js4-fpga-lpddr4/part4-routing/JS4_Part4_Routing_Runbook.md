<!--
JITX Routing Runbook (JS4 · Part 4) · rev 1.7 · 2026-11-12
Give this file to your AI coding agent (Claude Code, Codex / GPT, or Devin) and tell it to follow
the file. Complete JS0 and JS1 Part 2 first, then START A NEW AGENT SESSION: a skills install only
takes effect in a session started after it.
-->

# JITX Routing Runbook (JS4 · Part 4)

Each step below is a request, written the way you would ask an agent for the work. Follow them in
order; at a **[HUMAN]** step, stop and wait for me. Drive `jitx-interactive-layout` for the routes,
`jitx-layout-constraints` for the one design rule this part adds and the base `jitx` skill for the
project. The ground truth is Part 3's constraints, which JITX measures on the routed copper. Where
the skills leave a choice, make it and tell me what you chose. Don't open
`jitxexamples.jumpstart_kits.js4_fpga_lpddr4` other than its `base`, `ball_field` and `rules`
modules, even where a skill offers it as an example: it holds a finished answer to this task. Build
on `part3_si_constraints`'s `JS4SIConstraintsCircuit` without reading that module.

**Prerequisites:** JS0 and JS1 Part 2 are done; Python 3.12+; you can fetch from github.com.

Every part, the board and the constraints come from the `jitxexamples` package. Leave the FPGA's
pin offer, the substrate, Part 1's placement, vias, ground pours and escape routes, Part 2's
resistors, capacitors, pours and power rules, and Part 3's constraints and rules as they are.

## Steps

**0 · Preflight.**
Tell me this runbook's revision, from the comment at the top, and confirm `jitx-interactive-layout`
is invocable.

**1 · Project.**
Set up a new JITX project in an empty directory, with `jitxexamples` as a dependency and a parts
chain as the jitx-examples README's
[Parts configuration](https://github.com/JITx-Inc/jitx-examples#parts-configuration) section says,
and build the seeded design.

**2 · Start from Part 3.**
Build your design on Part 3's reference: a circuit that subclasses `JS4SIConstraintsCircuit` from
`jitxexamples.jumpstart_kits.js4_fpga_lpddr4.part3_si_constraints`, in a design that binds
`Reference18Board` and `Reference18Substrate` from `jitxexamples.substrates.reference_18layer`. It
has a through via in the pad of every FPGA ball but its NC balls and every memory ball but NC and
DNU, channel B's two strobe pairs escaped out of both ball fields on L3_SIG1 to a `PairPoint` at
each end, the resistors and the decoupling capacitors on BOTTOM, five power pours on L9, L10 and
L12, and the LPDDR4 constraints and spacing rules. Build it and check the issues: expect 182 `NOT
MET` groups, every constrained path unrouted. Each FPGA via on a ball no net reaches logs `No Net
linked for via` when a session opens on the design: it is not an issue, so leave the via in place.

**3 · Pair serpentine pitch.**
Give the pairs tagged `rules.LPDDR4PairTag` a minimum serpentine pitch of one coupled segment of the
85 ohm structure on L3 (two 3.55 mil traces 6.45 mil apart) plus the substrate's 2.8 mil minimum
copper to copper space, so a strobe pair takes more length in the room it has. Build.

**4 · [HUMAN] Routing plan.**
Plan the routes of channel B's byte lanes `ch[1].d[0]` and `ch[1].d[1]` on L3_SIG1: each DQ and DMI
via to via, each DQS between Part 1's pair points, nothing else. Byte lane 0 goes to byte slot 3's
balls and byte lane 1 to slot 2's, where Part 1's strobe escapes leave; the bit order is yours, and
the routes fix the assignment. If the session labels a slot with another byte, go by the slot. Show
me the plan, its length-matching sections and each route's limits. Wait for my approval.

**5 · Route.**
Route the two byte lanes as approved, matching length with serpentines inside the length-matching
sections. Place a control point only where a length-matching section ends: a route point at each end
of a DQ or DMI section and a pair point at each end of a DQS section. A line with no section is one
route from via to via: steer it with the route's turns, which pick the side of each via, line or
pair it passes, and let the router pull it tight between them. No DQ or DMI route takes a tag: its
own structure fits between the balls, as `ball_field` describes. Then build and report the issues.
In the reference solution's build every route routes and 60 groups turn met: the 20 skews (each DQ
and DMI to its DQS_T within +/-20 ps, each DQS pair within +/-0.4 ps), the 18 DQ and DMI delay
limits and the 22 loss limits, leaving 122 `NOT MET` groups, all outside the two byte lanes, none of
them `Unrealizable`, `Overlap` or `Unable to find path`. After every build or re-tune, check each
line and pair you had routed, since one can break while it still reads routed or met: every route
has copper and no serpentine has grown into a neighbour's room (an `Unrealizable route: insufficient
space` group names it). If one broke, or a line is pulled across a neighbour, repair it without a
control point: re-route it with turns that put it on the planned side of what it passes, re-route
the line it crowds, or move the nearest section's ends or narrow its envelope; then re-tune and
build again. If a byte lane's spread does not fit its sections, repair it the same way. If your
counts still differ after you recheck your routes and sections against the plan, stop and tell me.

**6 · Verify.**
Run the skills' checks, a build of your design and `jitx-code-review`; fix what they find apart
from paths outside the two byte lanes, and report each result, with the margin of each of the 20
skews. If a fix moves a route, check and repair the lines and pairs as step 5 says before you report.

## Done when

- The design builds on Part 3's reference, unchanged apart from the pair serpentine pitch rule: it
  binds the reference substrate and board, uses `VP1002LPDDR4`'s pin offer, keeps Part 1's
  placement, vias, ground pours and escape routes, keeps Part 2's resistors, capacitors, pours and
  power rules, and keeps Part 3's constraints and rules.
- Every DQ, DMI and DQS of `ch[1].d[0]` and `ch[1].d[1]` is routed on L3_SIG1, each DQ and DMI from
  its FPGA via to its memory via and each DQS between Part 1's pair points, and nothing else is
  routed. Every route has copper. No DQ or DMI route carries a tag, and the only control points
  you added sit at the ends of length-matching sections. Step 4 stopped before any route.
- The two byte lanes' 20 skews, 18 delay limits and 22 loss limits report met, each skew with its
  margin, and the `NOT MET` groups left are all outside the two byte lanes (122 in the reference
  solution's build), with no `Unrealizable`, `Overlap` or `Unable to find path` group.
- `pyright` passes with zero suppressions; `jitx design find` shows no import failures; the design
  builds; and `jitx-code-review` leaves no CRITICAL finding (every result reported, with the reason
  for each WARNING kept).

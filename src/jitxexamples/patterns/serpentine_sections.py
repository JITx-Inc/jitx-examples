"""Length-matched sections on four differential pairs, under four serpentine
settings.

Length matching is a constraint the router meets, not a length drawn in code.
Each of the four pairs runs between two fictional one-pair chips 40 mm apart
and is a bundle net, ``tx.d + rx.d``, constrained with
``ConstrainDiffPair(Topology(tx.d, rx.d))``: ``.timing(PAIR_DELAY)`` asks
each of P and N, pad to pad, for 260 ps with 2 ps tolerance,
``.timing_difference(PAIR_SKEW)`` keeps P and N within 1 ps of each other,
and ``.structure(SampleSubstrate.DRS_100)`` sets the pair's widths, spacing
and signal velocity (191.3 mm/ns). The straight path from pad to pad is
40 mm, about 209 ps, so a trace needs 9.4 mm more copper to reach the
window's 258 ps floor. The ``p`` trace of a staggered chip, below, starts
42 mm from its receiver (219.5 ps) and needs 7.4 mm more.

Where the router may add it is set in code. Each pair's path is a chain of
code routes through four control points from
``designer_placed_control_points``: an uncoupled route from each pad to a
``PairInsertion``, where the two traces join into a coupled pair; a coupled
route to the first ``PairPoint``; the section; a coupled route from the
second ``PairPoint`` to the far ``PairInsertion``; an uncoupled route to each
far pad. The section, between the two pair points, is the route configured
for length matching, ``Route.Config(envelope_overhead=ENVELOPE_OVERHEAD)``:
the router may meander the pair within a band 2.0 mm wider than the pair's
own copper.

Two settings on the chain are easy to drop and needed here, measured on
jitx 4.6.0. The transmitting insertion and both pair points are built with
``invert=True``, so each coupled route joins sides that can meet under the
chirality rules in the ``PairInsertion`` docstring; with every
``invert=True`` removed, the coupled route from the second pair point to
the receiving insertion was dropped on all four pairs ("Code route dropped:
its ends can never be joined") and every pair's topology was left
unconnected. Every control point is also attached to its pair with a
``PortAttachment``. The ``PairInsertion`` docstring says attachments should
not be needed in most designs, but with them removed the submit failed
with "State is not usable: INVALID-STATE".

Measured on jitx 4.6.0 (runtime 4.6.0), with a plain headless submit and
capture, no layout session:

- Every trace lands between 258.009 and 258.031 ps (258.02 ps on pairs 1
  to 3; 258.031 ps on P and 258.009 ps on N of pair 4), and every pair's
  skew is under 0.03 ps. The router stops at the lower edge of the 258 to
  262 ps window, not at the 260 ps target; single-ended sections asked for
  200 +/- 2 ps likewise landed at 198.02 ps.
- The meander stays inside the envelope in this design: each section's
  copper spans 2.317 mm across the pair's axis, the pair's 0.317 mm (two
  0.09 mm traces and the 0.137 mm gap) plus the 2.0 mm envelope, centred on
  the axis.
- Each 24 mm section grows to 33.2 mm on its longer trace.

Each section carries its own tag, and a design rule on that tag sets one
serpentine or deskew setting, so the four meanders differ:

1. ``WidePitchTag``: ``serpentine_params(min_pitch=3.0)``. The pair's
   meander segments sit 3.0 mm apart, centre to centre, so the copper of
   neighbouring segments is 2.683 mm apart: the pitch less the pair's
   0.317 mm of copper. Its bends have 0.60 mm and 0.83 mm radii, and each
   trace takes both, alternating, as it switches between the inside and
   the outside of a turn. Without a pitch rule the pitch varies: 2.06 to
   2.44 mm on pair 2, 2.21 to 2.39 mm on pair 3 (the trace without bumps)
   and 1.74 to 1.92 mm on pair 4. Pair 2 is not a clean control for pair
   1, since it also carries a deskew rule and starts at a staggered chip,
   and what sets the default pitch of each pair was not established.
2. ``SmallBumpTag``: ``coupled_pair_params(deskew_bump_radius=0.2)``. The
   transmitting chip of pairs 2 to 4 is ``ExampleStaggeredPairChip``, whose
   ``p`` pad sits 2.0 mm behind its ``n`` pad, so ``n`` starts out 2.0 mm
   short (10.5 ps of skew at this velocity). The router adds deskew bumps,
   small detours of four arcs, to the ``n`` trace only. Here the arcs have a
   0.2 mm radius: five bumps, four of quarter arcs that each span 0.8 mm
   along the trace, and a fifth of 63.2 degree arcs spanning 0.71 mm.
3. ``LargeBumpTag``: ``coupled_pair_params(deskew_bump_radius=0.6)``. The
   same skew is made up with two bumps of 0.6 mm radius, the second one
   shallower (68.1 degree arcs).
4. ``SpacedBumpTag``: ``coupled_pair_params(min_bump_spacing=2.0)``. The
   bumps keep the default 0.174 mm radius and sit exactly 2.0 mm apart along
   the trace, where pair 2's bumps sit 0.26 mm apart.

The example leaves out the other fields of these rules. What was measured
for each on jitx 4.6.0:

- ``min_radius`` gave no protection: bends came out below it with
  "Routing: Satisfied" in the issue report, 1.871 mm bends under a 2.5 mm
  minimum and 0.481 mm under 1.0 mm (single-ended), and 1.056 mm under
  1.5 mm (a pair).
- ``max_bump_length``, "the maximum length added by a deskew bump", gave
  no protection either: with it set to 0.3 mm the deskew bumps were the
  same as with no rule, each four quarter arcs of 0.174 mm radius, which
  add 0.40 mm (2 pi r of arc against a 4r span along the trace), again with
  no routing issue.
- ``long_lookahead`` at 20 mm changed nothing in the one case run.
- How ``skew_tolerance`` acts was not established.

Other cases measured on jitx 4.6.0:

- ``envelope_overhead=0``, or no ``Route.Config``, turns length matching
  off: the section stays straight and the delay line reports unmet.
- Route points are the recommended end for a length-matched section:
  translation warns that "It's recommended that length matched routes end
  at route points, which can resize to fit the meander envelope." Other
  ends can work. A single-ended section 30 mm long between the 0.6 mm
  square pads of ``ExampleChip``, with a 2.0 or 3.0 mm envelope, did not
  meander: the issue report carried an ``UnsquiggledRoute``, "a route end
  has no room for the envelope overhead (pad too small, or route point too
  close to the board edge)". The same section between 4 mm square pads
  with a 2.0 mm envelope meandered to 37.9 mm and met its 200 ps window at
  198.02 ps.
- A length-matched coupled section between two ``PairInsertion`` points
  (envelopes of 0.5, 1.0 and 2.0 mm) did not route at all ("Unable to find
  path for requested route"); with ``envelope_overhead=0`` the same section
  routed straight. Between two ``PairPoint`` points it meanders.
- On a one-pair version of this layout, ``min_bump_spacing`` at 4.0 mm took
  the meander away, and the pair missed its delay (220.3 ps of 260 ps).

Sizing each envelope is part of the design: give each section room for
the delay it has to add. A section with too small an envelope
reaches less delay, and the build reports the unmet timing on the
constraint, with "Routing: Satisfied". The fix is more room there, or
putting the delay in another section. Measured on jitx 4.6.0, a single-ended
section on ``SampleSubstrate.RS_50`` (0.1176 mm trace) with a 3.0 mm
envelope and a 1500 ps target reached 1.303 ns. A pitch rule wider than the
envelope does the same: a 0.2 mm envelope with ``min_pitch=1.0`` reached
171.5 ps of a 200 ps target.

What sets the gap between neighbouring meander segments, measured on jitx
4.6.0 on single-ended sections of ``SampleSubstrate.RS_50`` (0.1176 mm
trace, 0.2 mm clearance), each 24 mm long with a 3.0 mm envelope and asked
for more delay than it reached, so its meander packed as tightly as it was
allowed:

- The net's clearance rule does not set it: a 0.4 mm clearance rule on the
  net left the gap at 0.2 mm.
- With no pitch rule, the routing structure's clearance sets it: 0.2 mm,
  and 0.4 mm with the structure's clearance raised to 0.4 mm. That is how
  tightly a section packs when it cannot reach its delay; a section that
  meets its delay, like the pairs above, can sit wider.
- ``serpentine_params(min_pitch=...)`` replaces it, even below that
  clearance. The trace width plus 0.1, 0.2, 0.3 and 0.4 mm gave gaps of
  0.1, 0.2, 0.3 and 0.4 mm, and the trace width plus 0.2 mm on the 0.4 mm
  structure left the copper 0.2 mm apart under its 0.4 mm clearance.
- The gap did not go below 0.0588 mm on this 0.1176 mm trace: the trace
  width plus 0.05 mm, and the trace width alone, both gave that.
- None of these gaps raises a design issue, including the 0.1 mm and
  0.0588 mm gaps under the sample board's 0.127 mm
  ``min_copper_copper_space``: spacing rules raise no issue between copper
  of the same net, and neighbouring segments of one meander are the same
  net.
  A pitch that leaves a gap under the fabrication minimum is the designer's
  to catch, so check realized copper with your fabricator's design rule
  check.

The gap is the pitch less the copper across one meander segment: the trace
width for a single trace, and both traces plus the gap between them for a
pair (0.317 mm on ``DRS_100``, as in item 1). To hold a minimum gap, set
``min_pitch`` to that copper plus the gap.

The runtime tests in ``tests/test_serpentine_sections.py`` measure the
realized sections of this design.
"""

from __future__ import annotations

from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.constraints import Tag, Tags, design_constraint
from jitx.controlpoint import PairInsertion, PairPoint
from jitx.landpattern import Landpattern
from jitx.net import DiffPair, PortAttachment, Topology
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.si import ConstrainDiffPair
from jitx.toleranced import Toleranced
from jitxlib.symbols.box import BoxSymbol

from jitxexamples.patterns.si_parts import PadColumn, SquarePad

TX_X = -20.0
"""x of the transmitting chips, in mm."""

RX_X = 20.0
"""x of the receiving chips, in mm."""

ROW_Y = (15.0, 5.0, -5.0, -15.0)
"""y of the four pairs, in mm. 10 mm apart, so neighbouring envelopes never
meet."""

ENVELOPE_OVERHEAD = 2.0
"""Width, in mm, beyond the pair's copper, that each section may meander
within."""

PAIR_DELAY = Toleranced(260e-12, 2e-12)
"""Delay window for P and for N of every pair, pad to pad."""

PAIR_SKEW = 1e-12
"""Intra-pair skew window, P against N, in seconds."""

STAGGER = 2.0
"""How far, in mm, the staggered chip's ``p`` pad sits behind its ``n`` pad."""


class ExamplePairChip(Component):
    """Fictional chip with one differential pair, ``d``. Not a real product.
    Its two pads are 1.0 mm apart in one column, ``p`` below ``n``."""

    manufacturer = "Fictional"
    mpn = "EXAMPLE-1PAIR"
    reference_designator_prefix = "U"

    d = DiffPair()

    def __init__(self) -> None:
        self.landpattern = PadColumn(2)
        self.symbol = BoxSymbol()


class StaggeredPads(Landpattern):
    """Two square pads 1.0 mm apart on y, the first ``STAGGER`` mm behind the
    second on x."""

    def __init__(self) -> None:
        self.p_pad = SquarePad().at(-STAGGER, -0.5)
        self.n_pad = SquarePad().at(0.0, 0.5)


class ExampleStaggeredPairChip(Component):
    """Fictional chip whose ``p`` pad sits ``STAGGER`` mm behind its ``n``
    pad, so a pair leaving it starts with ``p`` longer than ``n``. Not a real
    product."""

    manufacturer = "Fictional"
    mpn = "EXAMPLE-1PAIR-STAGGERED"
    reference_designator_prefix = "U"

    d = DiffPair()

    def __init__(self) -> None:
        self.landpattern = StaggeredPads()
        self.symbol = BoxSymbol()


class WidePitchTag(Tag):
    """Section whose meander keeps at least 3.0 mm pitch."""


class SmallBumpTag(Tag):
    """Section whose deskew bumps have a 0.2 mm radius."""


class LargeBumpTag(Tag):
    """Section whose deskew bumps have a 0.6 mm radius."""


class SpacedBumpTag(Tag):
    """Section whose deskew bumps keep at least 2.0 mm apart."""


def designer_placed_control_points(
    y: float,
) -> tuple[PairInsertion, PairPoint, PairPoint, PairInsertion]:
    """The control points of one pair, at height ``y``.

    A designer would usually place these interactively: the two pair points
    bound the section that may meander, and where they sit decides where the
    meander goes. They are built here so the example is complete. JITX's
    layout API refuses to move a ``PairInsertion`` or ``PairPoint`` placed
    in code, so to place these interactively, leave them out of the code.

    Returns the insertion at the transmitting end, the two pair points that
    bound the length-matched section, and the insertion at the receiving end.
    """
    tx_insertion = PairInsertion(layer=0, invert=True).at(-16.0, y)
    section_start = PairPoint(layer=0, invert=True).at(-12.0, y)
    section_end = PairPoint(layer=0, invert=True).at(12.0, y)
    rx_insertion = PairInsertion(layer=0).at(16.0, y, rotate=180)
    return tx_insertion, section_start, section_end, rx_insertion


class SerpentineSections(Circuit):
    """Four pairs, each with its own serpentine or deskew rule."""

    def __init__(self) -> None:
        self.tx = [
            ExamplePairChip().at(TX_X, ROW_Y[0]),
            *(ExampleStaggeredPairChip().at(TX_X, y) for y in ROW_Y[1:]),
        ]
        self.rx = [ExamplePairChip().at(RX_X, y) for y in ROW_Y]
        tags: list[Tag] = [
            WidePitchTag(),
            SmallBumpTag(),
            LargeBumpTag(),
            SpacedBumpTag(),
        ]

        self.pairs = [tx.d + rx.d for tx, rx in zip(self.tx, self.rx, strict=True)]
        self.controls = [designer_placed_control_points(y) for y in ROW_Y]
        self.attachments: list[PortAttachment] = []
        # The routes of each chain other than its section: pads to the
        # insertions and insertions to the pair points.
        self.links: list[Route] = []
        self.sections: list[Route] = []
        for tx, rx, (tx_ins, start, end, rx_ins), tag in zip(
            self.tx, self.rx, self.controls, tags, strict=True
        ):
            # Every control point on the path is attached to the pair it
            # carries; the module docstring says why these are kept.
            self.attachments += [
                PortAttachment([tx.d.p, tx.d.n], control)
                for control in (tx_ins, start, end, rx_ins)
            ]
            self.links += [
                Route(tx.d.p, tx_ins.uncoupled.p, layer=0),
                Route(tx.d.n, tx_ins.uncoupled.n, layer=0),
                Route(tx_ins.coupled, start.back, layer=0),
                Route(end.front, rx_ins.coupled, layer=0),
                Route(rx.d.p, rx_ins.uncoupled.p, layer=0),
                Route(rx.d.n, rx_ins.uncoupled.n, layer=0),
            ]
            section = Route(
                start.front,
                end.back,
                layer=0,
                config=Route.Config(envelope_overhead=ENVELOPE_OVERHEAD),
            )
            Tags(tag).assign(section)
            self.sections.append(section)

        self.rules = [
            design_constraint(WidePitchTag()).serpentine_params(min_pitch=3.0),
            design_constraint(SmallBumpTag()).coupled_pair_params(
                deskew_bump_radius=0.2
            ),
            design_constraint(LargeBumpTag()).coupled_pair_params(
                deskew_bump_radius=0.6
            ),
            design_constraint(SpacedBumpTag()).coupled_pair_params(
                min_bump_spacing=2.0
            ),
        ]
        self.constraints = [
            ConstrainDiffPair(Topology(tx.d, rx.d))
            .timing(PAIR_DELAY)
            .timing_difference(PAIR_SKEW)
            .structure(SampleSubstrate.DRS_100)
            for tx, rx in zip(self.tx, self.rx, strict=True)
        ]


class serpentine_sections_design(SampleDesign):
    """The four pairs on the sample board."""

    circuit = SerpentineSections()

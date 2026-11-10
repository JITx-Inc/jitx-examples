"""A grounded coplanar line with two rows of fence vias, fenced through its
routing structure.

Use this pattern for an RF feed that needs coplanar ground beside the trace
and a via fence stitching that ground to the plane below. The fence belongs
to the routing structure: ``RoutingStructure.Layer(...).fence(via, pattern,
reference_layer=0)`` asks for fence vias along every trace the structure
shapes, on the net of the reference layer's plane. A ``fence_via`` design
rule does not do this: on jitx 4.6 it fenced no route on any of four tag
targets, and raised no issue.

Four pieces compose:

1. The structure, built by :py:func:`cpwg_structure` inside the circuit's
   ``__init__``. Built at module level, a ``RoutingStructure`` fails inside
   ``routing_structure(...)`` with ``TypeError: 'Instantiable' object is not
   iterable``.
2. A rule on the RF net's tag that applies it:
   ``design_constraint(RFLineTag()).routing_structure(structure,
   ref_net=GND)``. The rule takes the place of ``Constrain(...).structure``
   and ``>>``; a code route between the two pads is enough.
3. Ground pours on layers 0 and 1. The layer-0 pour is the coplanar ground,
   and the fence vias tie it to the layer-1 plane. The layer-0 pour runs
   ``POUR_END_MARGIN`` past each pad centre, so the fence vias that wrap
   each end of the line land on it as well as the straight rows; a pour
   that ends at the pad centres leaves those end vias on bare laminate,
   joined to the plane but to no layer-0 ground.
4. Ground vias in the layer-0 pour, one on each side of the line. A pour
   region with no same-net object in it is removed as an island, and the
   fence vias do not count. Built on jitx 4.6 with the pour ending at the
   pad centres, which cuts it into two halves, and the anchor below the
   line removed, the lower half was gone, the upper half stayed, the fence
   vias came back with no net, and the design reported
   ``No design issues.``

The relations, with w the trace width (``TRACE_WIDTH``), g the gap
(``GAP``), d the fence via pad (0.45 for ``SampleSubstrate.THVia``), o1 the
pattern's ``initial_offset`` (``FIRST_ROW_OFFSET``) and o its row spacing
(``ROW_SPACING``), as measured on jitx 4.6, each with the function that
computes it. The numbers after "here" come from building
:py:class:`layout_cpwg_two_row_fence_design` on that release.

- :py:func:`coplanar_gap`: the gap from the trace edge to the coplanar pour
  is the wider of g and the winning clearance rule between the trace and
  the pour, plus 0.01. Call that wider value C. Here the winning rule is a
  pair rule. ``GroundTag`` is on the GND net, a tag on a net reaches the
  net's pours, and this rule matches the line and the coplanar ground:
  ``design_constraint(RFLineTag(), GroundTag(), priority=2).clearance(GAP)``.
  Set both g and the pair rule to the gap: g is a floor, and a pair rule
  narrower than g leaves the gap at g plus 0.01 (measured on jitx 4.6).
  Without the pair rule, a ``clearance(<RF tag>, AnyObject)`` rule wins when
  there is one, as in the failure design.
  Here C = g, and the pour starts 0.36 from the centreline, 0.21 from the
  trace edge. A two-condition clearance between the RF tag and a tag the
  coplanar ground does not carry does not move this pour: in
  ``layout_sensitive_net_clearance`` a 1.0 rule between the RF and
  switch-node tags left a GND pour 0.137 from the line, the pullback with no
  rule.
- :py:func:`fence_row_centre`: o1 is measured from the trace edge to the via
  centre, not from the centreline. Row k sits at w/2 + o1 + (k-1)·o from
  the centreline. Here the rows came back at 0.601 and 1.201 against 0.6
  and 1.2 predicted.
- :py:func:`straight_run_fence_sites`: a straight run of length L holds
  L / pitch sites per side in row 2, and that or one fewer in row 1, where
  a site beside an end pad can drop. Here that is 20 per side per row
  along the 20 mm between the pad centres (``LINE_LENGTH`` /
  ``FENCE_PITCH``), with 19 also accepted in row 1. The vias around each
  end of the line follow the rows' radii from the end point, but the ends
  are only partly filled, so the ends are checked by position, not by
  count.
- :py:func:`checked_fence_pattern`: choose o1 - d/2 at or past the coplanar
  gap, C + 0.01 with C as above, so the first row's pads stay out of the
  gap. Here 0.45 - 0.225 = 0.225 against 0.21. The runtime does not
  enforce this: fence pads closer to the trace than the fab floor were
  placed with no issue.
- :py:func:`rows_in_coplanar_pour`: row k's pad reaches into the coplanar
  pour only while o1 + (k-1)·o + d/2 > C + 0.01, with C as above. Here row 1
  reaches 0.675 from the trace edge against 0.21. If a wider winning rule
  raises C past row 1's reach, move the rows out until o1 + d/2 > C + 0.01
  again.
- A ``pour_feature_size`` rule judges the whole coplanar ground strip, from
  the gap to the pour's outer edge, not the strip from the gap to row 1. The
  fence vias are on the pour's net and do not void it.

The dimensions are illustrative. Take w and g from the stackup's impedance
calculation; the 50 ohm on the structure is a label, not a solved value.

``rf_distribution``, the 2025-09 example this pattern rebuilds, set only
``offset=7*0.0254 + (0.45 + 0.1)/2`` to put the via edge 7 mil from a
0.1 mm trace. Two things follow from that:

- That formula measures from the centreline. The first row's offset is
  measured from the trace edge, so its via edge sat 0.4528 - 0.225 = 0.2278
  from the trace edge, not 0.1778.
- With ``initial_offset`` unset, ``offset`` is both the first row's offset
  and the spacing between rows (``ViaFencePattern`` docstring). Its rows sat
  0.4528 apart, so the 0.3 drills of the two rows were 0.1528 apart.

The 7 mil value, 7*0.0254 + 0.45/2, belongs in ``initial_offset``. Set
``offset`` separately, so that ``offset`` minus the drill is at least the
substrate's ``min_hole_to_hole``, as the test checks here. The runtime does
not check it for you: measured on jitx 4.6, stitch drills 0.2 apart were
placed with no issue, and a fence pitch of 0.3 was thinned with no issue.

The second design, :py:class:`layout_cpwg_two_row_fence_failure_design`,
adds ``design_constraint(RFLineTag(), AnyObject).clearance(RF_KEEPAWAY)``,
an RF keep-away of 1.0 to everything, and leaves out the pair rule, which
at priority 2 wins over the keep-away at its default priority (measured on
jitx 4.6, where a wider rule at a higher priority than 2 still won over the
pair rule). Built on jitx 4.6:

- The rule wins over g, and the coplanar pour starts 1.16 from the
  centreline, 1.01 from the trace edge.
- Row 1's pads, which reach 0.675 from the trace edge, sit in bare laminate
  between the trace and the pour. They still join the layer-1 plane, but
  touch no ground on layer 0, and the line has no coplanar ground within
  1.01 of its edge.
- The fence rows stay where the pattern puts them, 20 per side per row,
  although row 1 sits inside the 1.0 keep-away. Row 2's pads, which reach
  1.275 from the trace edge, still reach into the pour.
- A row-2 via sits at each side of the load pad's end: 1.203 from the load
  pad's centre, where the route ends, against row 2's 1.2, and 0.911 off
  the line's axis. The good design ends the same way. Built with neither the
  pair rule nor the keep-away, the line wraps that end with a row-1 via on
  each side instead, 0.6 from the pad centre. What decides which end vias
  survive is not established.
- The design reports ``No design issues.``

To keep an RF line away from a noisy net, write a two-condition clearance
between the RF tag and the noisy net's tag (see
``layout_sensitive_net_clearance``), not a clearance to ``AnyObject``.

The test, ``tests/test_layout_cpwg_two_row_fence.py``, checks these
relations offline. With ``JITX_PATTERN_RUNTIME=1`` and a runtime started at
the project root, it builds both designs and measures the fence rows, the
row counts and the pour gap, checks that each via around a route end sits
on a row's distance from the end point, and, on the good design, that every
fence via's pad lies on the coplanar pour.
"""

from __future__ import annotations

import math

from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.constraints import AnyObject, Tag, ViaFencePattern, design_constraint
from jitx.copper import Pour
from jitx.feature import Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Net, Port
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.shapes.composites import rectangle
from jitx.si import RoutingStructure
from jitx.via import Via
from jitxlib.symbols.box import BoxSymbol

TRACE_WIDTH = 0.3
"""w: the RF trace width, in mm."""

GAP = 0.2
"""g: the structure's clearance, the gap from the trace edge to the coplanar
ground, in mm."""

FIRST_ROW_OFFSET = 0.45
"""o1: from the trace edge to the centres of the first fence row, in mm."""

ROW_SPACING = 0.6
"""o: from one fence row's centres to the next, in mm."""

FENCE_PITCH = 1.0
"""Centre-to-centre spacing of the vias along a row, in mm."""

LINE_LENGTH = 20.0
"""Distance between the centres of the two RF pads, in mm."""

RF_KEEPAWAY = 1.0
"""The RF-to-everything clearance of the failure design, in mm."""

POUR_END_MARGIN = 3.0
"""How far the coplanar pour runs past each pad centre, in mm: past the
outermost fence via that wraps the line's end (row 2, 1.2 from the end
point, plus its 0.225 pad radius)."""

FENCE_VIA = SampleSubstrate.THVia
"""The fence via: a through via with a 0.45 mm pad and 0.3 mm drill."""

FENCE_PATTERN = ViaFencePattern(
    pitch=FENCE_PITCH,
    offset=ROW_SPACING,
    initial_offset=FIRST_ROW_OFFSET,
    num_rows=2,
)
"""Two rows of fence vias on each side of the trace."""


POUR_GAP_OFFSET = 0.01
"""How far past the winning clearance the coplanar pour starts, in mm
(measured on jitx 4.6)."""


def coplanar_gap(
    structure_clearance: float, winning_rule_clearance: float = 0.0
) -> float:
    """From the trace edge to the coplanar pour of a grounded coplanar line.

    The gap is 0.01 plus the wider of the routing structure layer's
    ``clearance`` and ``winning_rule_clearance``, the clearance rule that wins
    between the line and its ground by priority, then specificity (pass 0
    when no rule matches the pair). A winning rule below the structure's
    clearance does not narrow the gap. Measured on jitx 4.6: on a 0.3
    structure, a 0.6 rule at priority 0, 1 or 3 gave 0.61 and a 0.15 rule
    0.31; a 0.2 structure with a 0.5 rule and a 0.5 structure with a 0.2
    rule both gave 0.51.
    """
    return round(POUR_GAP_OFFSET + max(structure_clearance, winning_rule_clearance), 6)


def _first_row_offset(pattern: ViaFencePattern) -> float:
    """``initial_offset``, which defaults to ``offset`` when unset."""
    return pattern.offset if pattern.initial_offset is None else pattern.initial_offset


def fence_row_centre(trace_width: float, pattern: ViaFencePattern, row: int) -> float:
    """From a fenced line's centreline to the via centres of fence row ``row``.

    Row 1 is the nearest. ``initial_offset`` runs from the trace edge to row
    1's via centres and ``offset`` from one row's centres to the next, so row
    k sits at ``trace_width / 2 + initial_offset + (k - 1) * offset``.
    Measured on jitx 4.6 with a 0.5 trace and ``initial_offset`` and
    ``offset`` 0.6: rows at 0.851 and 1.451.
    """
    rows = pattern.num_rows or 1
    if not 1 <= row <= rows:
        raise ValueError(f"row {row} is outside the pattern's rows 1 to {rows}")
    return trace_width / 2 + _first_row_offset(pattern) + (row - 1) * pattern.offset


def checked_fence_pattern(
    pattern: ViaFencePattern, via: type[Via], pour_gap: float
) -> ViaFencePattern:
    """``pattern``, refused when its first row's pads sit in the gap.

    ``pour_gap`` runs from the trace edge to the coplanar pour, as
    :py:func:`coplanar_gap` gives it from the structure's clearance and the
    winning rule's: a pair rule wider than the structure widens the gap, and
    the pads have to clear that. A route fence's first row of pads keeps out
    of the gap when ``initial_offset - pad / 2 >= pour_gap``, with ``pad``
    the fence via's pad diameter. Nothing in JITX checks it: measured on
    jitx 4.6, fence pads 0.076 from the trace edge, under the fab floor,
    were placed with no issue. Also refuses a first-row offset that is not
    positive, which a route fence does not accept.
    """
    first = _first_row_offset(pattern)
    if first <= 0:
        raise ValueError(
            f"a route fence's initial_offset must be positive, not {first}"
        )
    # Rounded as coplanar_gap rounds, so a pattern exactly on the bound passes.
    edge = round(first - float(via.diameter) / 2, 6)
    if edge < round(pour_gap, 6):
        raise ValueError(
            f"first fence row's {via.__name__} pads start {edge:.3f} mm from the "
            f"trace edge, inside the {pour_gap} mm gap"
        )
    return pattern


def rows_in_coplanar_pour(
    pattern: ViaFencePattern, via: type[Via], pour_gap: float
) -> list[int]:
    """The fence rows, numbered from 1, whose via pads reach the coplanar pour.

    ``pour_gap`` runs from the trace edge to the pour, as
    :py:func:`coplanar_gap` gives it. Row k's pad reaches the pour when
    ``initial_offset + (k - 1) * offset + pad / 2 > pour_gap``. A row that
    does not reach it sits on bare laminate, joined to the plane below but
    to no ground beside the line. Measured on jitx 4.6 with ``initial_offset``
    and ``offset`` 0.6 and a 0.45 pad: with the pour 0.91 from the trace
    edge only row 2 reached it, and with the pour at 1.51 neither did.
    """
    first = _first_row_offset(pattern)
    pad = float(via.diameter) / 2
    return [
        k
        for k in range(1, (pattern.num_rows or 1) + 1)
        if round(first + (k - 1) * pattern.offset + pad, 6) > round(pour_gap, 6)
    ]


def straight_run_fence_sites(
    run_length: float, pitch: float, row: int
) -> tuple[int, int]:
    """Fence sites to accept per side along a straight run, lowest first.

    A row holds ``run_length / pitch`` sites per side along a straight run,
    rounded down. Row 1 can hold one fewer, a site beside an end pad, so it
    accepts that count less one up to the count; what drops that site was
    not established. Row 2 is exact. The vias around a route end are not
    counted: check them by position only. The range assumes the pattern
    sets neither ``min_pitch`` nor ``max_pitch``, which changed how many
    vias the runtime placed on a pour-outline fence (``fence_count_range``);
    it is never below 0.

    Measured on jitx 4.6, along 24 mm at pitch 1.0 with a 0.5 trace between
    0.6 by 0.6 end pads:

    - with the first row 0.6 from the trace edge (rows 0.851 and 1.451 from
      the centreline), 24 per side in both rows with no rule wider than the
      structure, and with a wider board rule ``(IsTrace, IsPour)`` at
      priority 3 that set the gap;
    - with the same rows, 23 per side in row 1 and 24 in row 2 under a
      clearance rule from the line's net tag to everything of 0.5, 0.9, 1.0
      or 1.5, and under a 0.6 pair rule to the ground's tag. At 0.5, 0.9 and
      1.5 the missing site is the row-1 site beside the destination pad, on
      the straight run;
    - with the first row 0.3 from the trace edge (rows 0.551 and 1.151) and
      no rule wider than the structure, 23 per side in row 1, the missing
      site beside the source pad.

    This module's failure design (20 mm, a 0.3 trace, a 1.0 keep-away) held
    20 per side in both rows. Not measured: other pitches and lengths, a
    length that is not a whole number of pitches, first-row offsets other
    than 0.3, 0.45 and 0.6, end pads other than 0.6 by 0.6 outside this
    module's own design (0.6 by 0.3), a single-row fence, and rows past 2,
    which are refused.
    """
    if row not in (1, 2):
        raise ValueError(f"row {row}: only rows 1 and 2 were measured")
    count = math.floor(run_length / pitch + 1e-9)
    if row == 1:
        return max(count - 1, 0), count
    return count, count


class RFLineTag(Tag):
    """RF nets that take the coplanar structure."""


class GroundTag(Tag):
    """The ground net the coplanar gap is measured to."""


def cpwg_structure() -> RoutingStructure:
    """The grounded coplanar structure on layer 0, with its two-row fence.

    Call it inside a circuit's ``__init__``, not at module level.
    """
    layer = RoutingStructure.Layer(
        trace_width=TRACE_WIDTH,
        clearance=GAP,
        velocity=150e9,
        insertion_loss=0.01,
    ).fence(
        FENCE_VIA,
        # The pair rule sets the gap at GAP too, so the pour starts at
        # coplanar_gap(GAP, GAP).
        checked_fence_pattern(FENCE_PATTERN, FENCE_VIA, coplanar_gap(GAP, GAP)),
        reference_layer=0,
    )
    return RoutingStructure({0: layer}, impedance=50, name="CPWG_50")


class RFPad(Pad):
    """A 0.6 mm by ``TRACE_WIDTH`` pad, as wide as the line it ends."""

    shape = rectangle(0.6, TRACE_WIDTH)
    soldermask = Soldermask(rectangle(0.7, TRACE_WIDTH + 0.1))


class RFPadLandpattern(Landpattern):
    pad = RFPad().at(0, 0)


class RFEndpoint(Component):
    """A fictional one-pin RF part, standing in for a connector or a radio
    pin. Not a real product."""

    manufacturer = "Fictional"
    mpn = "EXAMPLE-RF-PAD"
    reference_designator_prefix = "J"

    rf = Port()
    landpattern = RFPadLandpattern()
    symbol = BoxSymbol()

    def __init__(self) -> None:
        self.mappings = [PadMapping({self.rf: self.landpattern.pad})]


class CPWGLine(Circuit):
    """The RF line on layer 0 between two pads, with its coplanar ground.

    ``gap_rule=False`` leaves out the RF-to-ground pair rule that sets the
    gap, as the failure design does.
    """

    def __init__(self, gap_rule: bool = True) -> None:
        half = LINE_LENGTH / 2
        self.source = RFEndpoint().at(-half, 0)
        self.load = RFEndpoint().at(half, 0)
        self.rf = Net([self.source.rf, self.load.rf], name="RF")
        RFLineTag().assign(self.rf)
        self.route = Route(self.source.rf, self.load.rf, layer=0)

        self.gnd = Net(name="GND")
        GroundTag().assign(self.gnd)
        # The coplanar pour runs past both pads, so the fence vias that wrap
        # each end of the line land on it.
        self.coplanar = Pour(rectangle(LINE_LENGTH + 2 * POUR_END_MARGIN, 6), layer=0)
        self.plane = Pour(rectangle(LINE_LENGTH + 10, 20), layer=1)
        # One anchor on each side of the line.
        self.anchors = [FENCE_VIA().at(-half + 1.5, y) for y in (2.3, -2.3)]
        self.gnd += self.coplanar
        self.gnd += self.plane
        for anchor in self.anchors:
            self.gnd += anchor

        self.structure = cpwg_structure()
        self.structure_rule = design_constraint(RFLineTag()).routing_structure(
            self.structure, ref_net=self.gnd
        )
        if gap_rule:
            # The pair rule sets the gap; the structure's clearance stays at
            # or below it.
            self.gap_rule = design_constraint(
                RFLineTag(), GroundTag(), priority=2
            ).clearance(GAP)


class layout_cpwg_two_row_fence_design(SampleDesign):
    """The fenced coplanar line on the sample board."""

    circuit = CPWGLine()


class layout_cpwg_two_row_fence_failure_design(SampleDesign):
    """The same line with an RF clearance to everything that is wider than
    the gap. It builds with no issue and loses the coplanar ground beside the
    trace. It leaves out the pair rule, which at priority 2 wins over the
    keep-away (measured on jitx 4.6)."""

    circuit = CPWGLine(gap_rule=False)
    rf_keepaway = design_constraint(RFLineTag(), AnyObject).clearance(RF_KEEPAWAY)

"""The 50 ohm line's layers, tags and rules. The run that produced this board
also drew them on a launch-thru calibration fixture (two jacks back to back),
from these same functions, so its line, gap, fence and stitching were the
board's by construction.

Rules (``line_rules``; :py:mod:`.main` adds its branch rules to them):

- [2] ``RFLineTag`` on a signal net applies ``fenced_rs50()``, a copy of the
  substrate's ``RS_50`` with a one-row via fence on each side (the substrate
  class is not ours to edit). The copy keeps RS_50's width, velocity and
  loss.
- [2] ``(RFLineTag, CoplanarGroundTag)`` sets the coplanar gap to the top
  pour. The runtime stands a pour ``POUR_GAP_OFFSET`` (0.01 mm, measured in
  ``layout_cpwg_two_row_fence``) past the winning clearance, so the copy and
  this rule ask for 0.12 mm and the realized gap is RS_50's 0.13 mm.
- [3] ``(LaunchPadTag, CoplanarGroundTag)``: the pour stands
  ``LAUNCH_PAD_GAP`` (the line's 0.13 mm) off each jack's centre pad.
- [4] ``ExitNeckTag`` on each exit's neck route applies ``neck_structure()``
  (``EXIT_NECK_WIDTH`` in the line's slot), and ``(ExitNeckTag,
  CoplanarGroundTag)`` its gap, beating the net's ``RS_50`` and line gap.
- ``StitchTag`` on the top pour: a ``StdVia`` grid stitching it to the bottom
  plane.
"""

from __future__ import annotations

import shapely
from jitx.constraints import DesignConstraint, Tag, ViaFencePattern, design_constraint
from jitx.net import Net
from jitx.shapes import Shape
from jitx.shapes.primitive import Circle
from jitx.shapes.shapely import ShapelyGeometry
from jitx.si import RoutingStructure
from jitx.units import ohm
from jitx.via import Via
from jitxexamples.patterns.layout_cpwg_two_row_fence import (
    POUR_GAP_OFFSET,
    checked_fence_pattern,
    coplanar_gap,
)
from jitxexamples.patterns.layout_stitched_pour import checked_stitch_grid

from .substrate import DiplexerSubstrate

RF_LAYER = 0
"""Top copper: the RF lines and the coplanar ground."""

PLANE_LAYER = -1
"""Bottom copper: the solid ground plane."""

FLOOR_MARGIN = 0.02
"""Hold-off above a fabrication floor wherever copper is placed at one, mm:
the export draws curves as chords up to the realization tolerance (0.02) inside
the true arc, so copper drawn exactly at a floor can measure under it."""

FENCE_PITCH = 1.0
"""Fence via pitch along each 50 ohm line (the run's fence assumption: at
most 1.5)."""

STITCH_PITCH = 1.5
"""General stitch grid pitch over the top pour."""

STITCH_INSET = 0.25
"""Stitch via pad edge to the computed top pour boundary."""


# source: the run's launch tuning, step S1 against S0, measured on the launch-thru fixture
LAUNCH_PAD_GAP = 0.13
"""Realized gap from each jack's centre pad to the top pour, mm: the line's
own gap. Launch-tune S1 tried 0.33 mm; the S0/S1 contrast placed that
change on the pad (27.9 ps from the thru's centre, the pad's 29 ps) at
-0.142 pF per launch, but the baseline's excess C sits nearer the line
(8 to 19 ps), so the pad compensation helped 2.4 GHz and hurt 5-6 GHz.
Launch-tune S2 restores the line's gap here and compensates on the exit
(``EXIT_NECK_WIDTH``)."""

# source: the run's launch tuning, step S2 (Born first-order fit to the S0 thru,
# calibrated by the S0/S1 contrast)
EXIT_NECK_WIDTH = 0.38
"""Trace width of the exit's neck, mm: the exit's last ``EXIT_NECK_LENGTH``
before the launch point, inside the line's own slot (pour edge unchanged at
0.285 + 0.13 = 0.415 mm off the axis, so the neck's gap is 0.225 mm). A 2D
quasi-static solve (0.762 RO4350B, the export's mask and gap fill) gives
the neck 67 to 69 ohm and a net excess (C - L/50^2) of -61 to -65 pF/m
against RS_50, -0.116 pF over its 1.83 mm of narrow copper (-0.142 with
the 1.23 ratio the S0/S1 contrast measured against the 2D pad solve). The
S0 thru's first-order (Born) response is best cancelled by -0.12 to
-0.13 pF spread 9 to 19 ps from the thru's centre, which is where the
narrow copper sits (9.6 to 19.5 ps)."""

EXIT_NECK_LENGTH = 2.40
"""Neck route length, mm: from 0.60 mm past the pad's inner end to the
launch point (3.0 mm exit), x 2.57 to 4.97 from the board edge. The
full-width routes' end caps (half of 0.57 each) reach into it, so the
copper is neck-wide over about 1.83 mm, x 2.86 to 4.69."""


class RFLineTag(Tag):
    """The signal nets: they take the fenced ``RS_50`` structure."""


class CoplanarGroundTag(Tag):
    """The top ground pour, which the coplanar gap is measured to."""


class StitchTag(Tag):
    """Pours stitched to the bottom plane on a grid."""


class ExitNeckTag(Tag):
    """The neck ``Route`` of each exit: it takes ``neck_structure()`` and the
    neck's coplanar gap."""


class LaunchPadTag(Tag):
    """Each jack's centre pad: the top pour keeps ``LAUNCH_PAD_GAP`` from
    it."""


def corridor(
    a: tuple[float, float], b: tuple[float, float], half_width: float
) -> Shape:
    """The band ``half_width`` either side of the segment from ``a`` to ``b``,
    flat at both ends."""
    band = shapely.LineString([a, b]).buffer(half_width, cap_style="flat")
    return ShapelyGeometry(band)


def via_keepoff(centre: tuple[float, float], via: type[Via]) -> Shape:
    """A via keepout round a code-placed via: a generated via is kept out when
    its pad touches it, so the disc's radius is the drill plus
    ``min_hole_to_hole`` less the generated via's pad radius, which leaves
    the two drills ``min_hole_to_hole`` apart."""
    fab = DiplexerSubstrate.constraints
    radius = via.hole_diameter + fab.min_hole_to_hole - float(via.diameter) / 2
    return Circle(radius=radius).at(*centre)


def rs50_half_width() -> float:
    """Half the ``RS_50`` trace width on the top layer, mm."""
    return DiplexerSubstrate.RS_50.layers[RF_LAYER].trace_width / 2


def rs50_gap() -> float:
    """``RS_50``'s coplanar gap on the top layer, mm: the realized gap."""
    gap = DiplexerSubstrate.RS_50.layers[RF_LAYER].clearance
    assert gap is not None
    return gap


def gap_rule() -> float:
    """The clearance the structure copy and the gap rules ask for: the runtime
    stands a pour ``POUR_GAP_OFFSET`` past the winning clearance
    (``layout_cpwg_two_row_fence``, measured), so they ask for that much less
    and the realized gap is ``RS_50``'s own."""
    return rs50_gap() - POUR_GAP_OFFSET


def launch_pad_gap_rule() -> float:
    """The clearance the pad's gap rule asks for: ``LAUNCH_PAD_GAP`` less the
    runtime's ``POUR_GAP_OFFSET`` (as ``gap_rule``)."""
    return LAUNCH_PAD_GAP - POUR_GAP_OFFSET


def rs50_fence_row() -> float:
    """The line's fence row from its trace edge, mm: the via pad edge at the
    coplanar gap plus the minimum copper space, and the drill at least
    ``min_copper_hole_space`` from the trace edge, each plus
    ``FLOOR_MARGIN``."""
    fab = DiplexerSubstrate.constraints
    via = DiplexerSubstrate.StdVia
    return FLOOR_MARGIN + max(
        rs50_gap() + fab.min_copper_copper_space + float(via.diameter) / 2,
        fab.min_copper_hole_space + via.hole_diameter / 2,
    )


def neck_gap() -> float:
    """The neck's realized coplanar gap, mm: the line's slot edge less half
    the neck width, so the pour edge does not move."""
    return rs50_half_width() + rs50_gap() - EXIT_NECK_WIDTH / 2


def fenced_rs50() -> RoutingStructure:
    """``RS_50`` with one fence row each side: the first row's via pad edge at
    the coplanar gap plus the minimum copper space, and its drill at least
    ``min_copper_hole_space`` from the trace edge, each plus
    ``FLOOR_MARGIN``."""
    rs50 = DiplexerSubstrate.RS_50
    top = rs50.layers[RF_LAYER]
    via = DiplexerSubstrate.StdVia
    pour_gap = coplanar_gap(gap_rule(), gap_rule())
    assert abs(pour_gap - rs50_gap()) < 1e-9
    first_row = rs50_fence_row()
    fence = checked_fence_pattern(
        ViaFencePattern(pitch=FENCE_PITCH, offset=first_row, initial_offset=first_row),
        via,
        pour_gap,
    )
    return RoutingStructure(
        {
            RF_LAYER: RoutingStructure.Layer(
                trace_width=top.trace_width,
                clearance=gap_rule(),
                velocity=top.velocity,
                insertion_loss=top.insertion_loss,
            ).fence(via, fence, reference_layer=RF_LAYER)
        },
        impedance=rs50.impedance,
        name="RS_50 fenced",
    )


def neck_structure() -> RoutingStructure:
    """The exit neck: ``EXIT_NECK_WIDTH`` wide at ``neck_gap()``, fenced on
    the line's own via row (offset from the neck's edge by the width it
    gives up, so the row stays where the line's is). Its 0 ohm is a label
    that keeps impedance lookups on ``RS_50``, not an impedance."""
    top = DiplexerSubstrate.RS_50.layers[RF_LAYER]
    via = DiplexerSubstrate.StdVia
    row = rs50_fence_row() + rs50_half_width() - EXIT_NECK_WIDTH / 2
    fence = checked_fence_pattern(
        ViaFencePattern(pitch=FENCE_PITCH, offset=row, initial_offset=row),
        via,
        neck_gap(),
    )
    return RoutingStructure(
        {
            RF_LAYER: RoutingStructure.Layer(
                trace_width=EXIT_NECK_WIDTH,
                clearance=neck_gap() - POUR_GAP_OFFSET,
                velocity=top.velocity,
                insertion_loss=top.insertion_loss,
            ).fence(via, fence, reference_layer=RF_LAYER)
        },
        impedance=0 * ohm,
        name="RS_50 exit neck",
    )


def line_rules(structure: RoutingStructure, gnd: Net) -> list[DesignConstraint]:
    """The line's rules (module docstring): the fenced structure on
    ``RFLineTag``, the coplanar gap to ``CoplanarGroundTag`` from the line,
    the launch gap from each ``LaunchPadTag`` pad, the neck structure and
    gap on each ``ExitNeckTag`` route, and the ``StitchTag`` grid."""
    via = DiplexerSubstrate.StdVia
    fab = DiplexerSubstrate.constraints
    return [
        design_constraint(RFLineTag(), priority=2).routing_structure(
            structure, ref_net=gnd
        ),
        design_constraint(RFLineTag(), CoplanarGroundTag(), priority=2).clearance(
            gap_rule()
        ),
        design_constraint(LaunchPadTag(), CoplanarGroundTag(), priority=3).clearance(
            launch_pad_gap_rule()
        ),
        design_constraint(ExitNeckTag(), priority=4).routing_structure(
            neck_structure(), ref_net=gnd
        ),
        design_constraint(ExitNeckTag(), CoplanarGroundTag(), priority=4).clearance(
            neck_gap() - POUR_GAP_OFFSET
        ),
        design_constraint(StitchTag()).stitch_via(
            via, checked_stitch_grid(via, fab, STITCH_PITCH, STITCH_INSET)
        ),
    ]

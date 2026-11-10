"""An SMA end launch into a fenced grounded coplanar line, built in code.

A connector on each board edge launches into the line between them. The
two connectors sit 8.0 mm apart across the board, so the line turns at each
launch. Each launch has four parts: the connector placed by its exit's shape
and direction, a straight exit of a stated length, a small ground copper
square on the inside of the turn that sets the bend, and a hyperbolic cutout
in the ground under the centre pad and the start of the exit. Between the
launches runs the grounded coplanar line of ``layout_cpwg_two_row_fence``,
with its two rows of fence vias.

The numbers are the example's inputs, chosen for illustration, not validated
RF performance: a 3.0 mm straight exit, a 0.2 mm square 1.0 mm off the
trace, a 1.6 mm wide cutout under the centre pad, a 2.5 mm taper, and the
launch points 20 mm apart along the board and 8.0 mm across it. The
line's 0.3 mm trace and 0.2 mm gap come from ``layout_cpwg_two_row_fence``,
where the 50 ohm on the structure is a label, not a solved value. That
module's ``coplanar_gap`` puts the pour 0.01 mm beyond the 0.2 mm gap, so
the pour stands 0.21 mm off the trace on each side. The board uses the
two-layer sample substrate, 0.75 mm from top copper to bottom copper. Take
the cutout and the line from a field solver for your own stackup.

The connector
-------------

The connector is the Würth Elektronik 60312202114514 WR-SMA end launch,
from ``jitxexamples.components.connectors.wurth_elektronik_60312202114514``.
Its land pattern's frame puts x = 0 on the body face and +x into the board
along the 0.61 mm centre pad, so the exit's shape and direction come from
the part: ``EdgeLaunch`` places the connector at its own origin, and the
launch is placed with its origin on the board edge and its +x axis into the
board. The right-hand launch is the same circuit turned 180 degrees. The part
has ground pads on the top and on the bottom, so both ground pours have a
ground object on their layer and fill with no via placed to anchor them. The
part is made for a 1.6 mm board; this example uses its land pattern only.

The pads start at the board edge, closer to it than the sample fabrication
constraints' 0.5 mm ``min_copper_edge_space``. Land-pattern pads are placed
as drawn, and pads closer to the edge than ``min_copper_edge_space`` raise
no design issue, so confirm the edge distance with your fabricator and check
realized copper with your fabricator's design rule check.

The straight exit
-----------------

A code route from a pad to another pad does not leave the pad along its
axis. A ``RoutePoint`` on the axis does: the route from the centre pad to it
is a straight section on the axis, as ``wilkinson_tree`` makes its port
exits. :py:func:`launch_point` puts it ``LAUNCH_LENGTH`` past the inner end
of the centre pad. Its position follows from the connector and the stated
length, so it is not a point a designer would move.

The exit takes the structure's 0.3 mm width from the pad's centre, so the
copper steps from the 0.61 mm pad to the 0.3 mm trace at the pad's inner
end, over the cutout. The example draws no taper. To taper into the pad
instead, split the exit at a second ``RoutePoint`` near the pad, so that the
pad is the destination of the short route from that point, and give that
route ``Route.Config(destination_target=...)``, as ``code_route_basics``
does.

The tangency square
-------------------

Past the launch point the line turns toward the other connector. Where it
bends is set by a square of ground copper on the inside of the turn
(:py:func:`tangency_square`): ``TANGENCY_SQUARE`` (0.2 mm) on a side, on the
signal layer, running along the axis from the launch point to 0.2 mm past
it, its near side ``TANGENCY_CLEARANCE`` (1.0 mm) off the trace's copper
edge. The square carries ``TangencyTag``, and
``design_constraint(TangencyTag(), RFLineTag(), priority=3).clearance(1.0)``
holds the line's copper that clearance from it. The line then runs on the
axis past the square's far edge and bends around the square's corner on a
centre-line radius of half the trace plus the clearance, 1.15 mm. The
clearance to the square sets the bend radius: a larger clearance gives a
larger bend, with the square moved out to match.

The square has to stand the clearance off the trace's copper. Nearer than
that, the router cannot keep the clearance on the axis and leaves the route
unrealized. A rule clearance under the structure's own 0.2 mm loses to the
structure. The square goes on the inside of the turn only: squares on both
sides turn the line away at the launch point. The rule is at priority 3 so
that it wins over the gap rule between ``RFLineTag`` and ``GroundTag`` at
priority 2, since the square is on the ground net.

The square is copper, not a keepout. A route keepout gets no clearance from
the router, so the line's copper runs along its edge and bends at half the
trace whatever the clearance, and a keepout with ``via`` set would also
remove the fence vias it covers. The square is on the ground net and inside
the coplanar pour, and holds other-net copper off by its rule, with no
keepout at all. Hold any other copper off the line the same way: a tag on it
and a clearance rule to ``RFLineTag``, not a keepout.

The cutout
----------

A ``KeepOut`` with ``pour`` and ``via`` set, on each layer of
``REFERENCE_LAYERS``, voids the ground pour under the centre pad and the
start of the exit (:py:func:`cutout_outline`). It is a rectangle
``PAD_CUTOUT_WIDTH`` wide from the board edge to the inner end of the centre
pad, then a taper over ``CUTOUT_TAPER_LENGTH`` that narrows to the line's
coplanar slot (:py:func:`line_slot_width`: the trace and the coplanar gap on
each side, 0.72 mm). Its half-width h follows a hyperbola::

    h(s) = k / (s + s0),  s0 = L h1 / (h0 - h1),  k = h0 s0,

with s the distance along the taper, L its length, h0 the half-width under
the pad and h1 the slot's half-width. Here s0 = 2.045 mm and
k = 1.636 mm²: the cutout is 1.6 mm wide at the pad, 0.993 mm halfway along
the taper and 0.72 mm at its end. The outline is drawn with ``CUTOUT_STEPS``
straight segments per side.

The pour's edge follows the keepout's outline. The ``via`` flag keeps the
fence vias out of the cutout, and it is the example's guard for the first
row of the fence, nearer the trace, beside the 0.61 mm centre pad. That row's
via pads start 0.375 mm from the centreline, so a row-1 via beside the pad
would sit 0.07 mm from it, under the sample board's 0.127 mm
``min_copper_copper_space``. The example does not rely on the runtime to
keep fence vias to that floor: ``checked_fence_pattern`` in
``layout_cpwg_two_row_fence`` records fence pads placed nearer a trace than
the floor with no issue. Over the cutout the first row is left out; the
second runs beside it.

:py:func:`cutout_outline` refuses a cutout too narrow to be that guard.
:py:func:`row_one_hold` returns the first row's pad edge, 0.375 mm from the
centreline, and its reach: how far past the pad the first row would still
come closer than ``min_copper_copper_space`` to the pad's corner. The cutout
must be more than 0.75 mm wide out to that distance past the pad; a narrower
one raises a ``ValueError`` that names that width. A taper that has no
length, or that ends within that reach, raises a ``ValueError`` that names
the taper, since no cutout width can then hold the first row off the pad.
The cutout must also be wider than the 0.72 mm coplanar slot it tapers to,
or it raises a ``ValueError`` that names the slot, and narrower than the
7.1 mm between the connector's bottom ground pads. The taper is refused if
it is longer than the straight exit, since it assumes a straight trace over
it, and ``steps`` below 1 raises a ``ValueError`` that names ``steps``.

The line
--------

The structure, its rule and the gap rule are ``layout_cpwg_two_row_fence``'s
(see that module for why each is there): ``cpwg_structure``, applied by a
``routing_structure`` rule on ``RFLineTag`` with the ground as reference net,
and a pair rule between ``RFLineTag`` and ``GroundTag`` at the gap. The tag
sits on the RF net, so the structure shapes the exits as well as the line,
and the fence runs along both. ``straight_run_fence_sites`` in
``layout_cpwg_two_row_fence`` gives the vias per side it accepts for each
row on a straight line between end pads. Between this line's two bends, on a
20.28 mm run, the build held 19 vias per side in the second row, one fewer
than that count gives, so check the rows here by their gaps. The pair
rule sets the gap beside the routes but not beside the centre pad, where the
coplanar pour keeps its own pullback from the pad. Check that gap in the
realized copper against your fabricator's minimum copper space.

The test, ``tests/test_rf_connector_launch.py``, checks the geometry offline.
With ``JITX_PATTERN_RUNTIME=1`` and a runtime started at the project root,
it builds the design and measures the exits, the bend around each square and
the line's clearance to it, the cutout in the computed ground pour against
the hyperbola, the fence rows, and each fence via's distance from the signal
copper.
"""

from __future__ import annotations

import math

from jitx import KeepOut, LayerSet, Net, Pour
from jitx.board import Board
from jitx.circuit import Circuit, Route
from jitx.copper import Copper
from jitx.constraints import Tag, design_constraint
from jitx.controlpoint import RoutePoint
from jitx.design import Design
from jitx.net import Port
from jitx.sample import SampleFabConstraints, SampleSubstrate
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Polygon
from jitx.via import ViaDiameter

from jitxexamples.components.connectors.wurth_elektronik_60312202114514 import (
    CENTER_PAD_LENGTH,
    CENTER_PAD_WIDTH,
    GROUND_INNER,
    Wurth60312202114514,
)
from jitxexamples.patterns.layout_cpwg_two_row_fence import (
    FENCE_PATTERN,
    FENCE_VIA,
    GAP,
    TRACE_WIDTH,
    GroundTag,
    RFLineTag,
    coplanar_gap,
    cpwg_structure,
    fence_row_centre,
)

RF_LAYER = 0
"""The layer of the connector's centre pad and the line: the layer
``cpwg_structure`` is defined on."""

REFERENCE_LAYERS = (1,)
"""The ground layers under the line that the cutout voids. The sample board
has one, its bottom layer."""

LAUNCH_LENGTH = 3.0
"""From the inner end of the connector's centre pad to the launch point, in
mm: the length of the straight exit past the pad."""

PAD_CUTOUT_WIDTH = 1.6
"""Width of the cutout under the centre pad, in mm."""

CUTOUT_TAPER_LENGTH = 2.5
"""Length of the cutout's hyperbolic taper, from the inner end of the centre
pad along the exit, in mm."""

CUTOUT_STEPS = 32
"""Straight segments the taper's outline is drawn with, per side."""

TANGENCY_SQUARE = 0.2
"""Side of the ground copper square that sets each bend, in mm."""

TANGENCY_CLEARANCE = 1.0
"""Clearance from the line's copper to each square, in mm. The square's near
side stands this far off the trace's copper edge, and the line bends around
the square's corner on a centre-line radius of half the trace plus this."""

LINE_LENGTH = 20.0
"""Distance along the board between the two launch points, in mm."""

LAUNCH_OFFSET = 8.0
"""Distance across the board between the two connectors' axes, in mm. The
line turns at each launch point to cover it."""

BOARD_WIDTH = 20.0
"""Board size across the line, in mm."""

BOARD_LENGTH = LINE_LENGTH + 2 * (CENTER_PAD_LENGTH + LAUNCH_LENGTH)
"""Board size along the line, in mm: the line and a launch at each end. Each
connector's body face sits on a board edge."""

POUR_INSET = 0.5
"""How far inside the board edge the ground pours stop, in mm: the sample
fabrication constraints' ``min_copper_edge_space``."""

MIN_COPPER_SPACE = SampleFabConstraints.min_copper_copper_space
"""The sample fabrication constraints' minimum copper-to-copper space, in mm:
the floor fence row 1 has to keep from the centre pad."""


def line_slot_width() -> float:
    """Width of the line's coplanar slot on the signal layer, in mm: the trace
    and the coplanar gap on each side, as ``coplanar_gap`` gives it for the
    line's structure and pair rule."""
    return TRACE_WIDTH + 2 * coplanar_gap(GAP, GAP)


def cutout_half_width(s: float, start: float, end: float, length: float) -> float:
    """Half-width of the cutout's taper ``s`` mm along it, narrowing from
    ``start`` to ``end`` over ``length``, in mm.

    The outline is a hyperbola, h = k / (s + s0), so 1 / h changes linearly
    along the taper.
    """
    if not 0 <= s <= length:
        raise ValueError(f"{s} mm is outside the {length} mm taper")
    if not start > end > 0:
        raise ValueError(f"a taper from {start} to {end} mm does not narrow")
    return 1 / (1 / start + (1 / end - 1 / start) * s / length)


def _fence_pad_radius() -> float:
    diameter = FENCE_VIA.diameter
    pad = diameter.pad if isinstance(diameter, ViaDiameter) else diameter
    return pad / 2


def row_one_hold() -> tuple[float, float]:
    """Where the cutout has to hold fence row 1 off the centre pad.

    Returns ``(edge, reach)``, in mm. ``edge`` is how far row 1's via pads
    start from the centreline, from ``fence_row_centre`` and the fence via's
    pad. ``reach`` is how far past the inner end of the centre pad a row-1
    pad would still come closer than ``MIN_COPPER_SPACE`` to the pad's
    corner. Up to ``reach``, the cutout's half-width has to exceed ``edge``,
    so that every row-1 site there touches the cutout's via keepout. A
    ``reach`` of 0 means row 1 clears the centre pad by itself.
    """
    radius = _fence_pad_radius()
    centre = fence_row_centre(TRACE_WIDTH, FENCE_PATTERN, 1)
    across = centre - CENTER_PAD_WIDTH / 2
    floor = radius + MIN_COPPER_SPACE
    reach = math.sqrt(floor**2 - across**2) if floor > across else 0.0
    return centre - radius, reach


def cutout_outline(
    pad_cutout_width: float = PAD_CUTOUT_WIDTH,
    taper_length: float = CUTOUT_TAPER_LENGTH,
    steps: int = CUTOUT_STEPS,
) -> list[tuple[float, float]]:
    """The cutout's outline in the connector's frame: x = 0 on the board edge,
    +x into the board along the centre pad.

    A rectangle ``pad_cutout_width`` wide under the centre pad, then the
    hyperbolic taper over ``taper_length``, in ``steps`` straight segments,
    down to :py:func:`line_slot_width`. Raises ``ValueError`` for fewer than
    one step; for a taper with no length, or one that ends within the reach
    of :py:func:`row_one_hold`, where no width holds fence row 1 off the
    centre pad; for a taper longer than the straight exit; for a cutout no
    wider than the line's coplanar slot, which would not narrow; for one too
    narrow to hold fence row 1 off the centre pad; and for one as wide as
    the gap between the connector's ground pads.
    """
    if steps < 1:
        raise ValueError(f"steps must be at least 1, not {steps}")
    if taper_length <= 0:
        raise ValueError(f"the taper must have a length, not {taper_length} mm")
    edge, reach = row_one_hold()
    if taper_length <= reach:
        raise ValueError(
            f"the {taper_length} mm taper ends within {reach:.3f} mm of the "
            "centre pad, where fence row 1 would come closer to the pad than the "
            f"{MIN_COPPER_SPACE} mm min_copper_copper_space; make it longer"
        )
    if taper_length > LAUNCH_LENGTH:
        raise ValueError(
            f"the {taper_length} mm taper runs past the {LAUNCH_LENGTH} mm "
            "straight exit"
        )
    slot = line_slot_width()
    if pad_cutout_width <= slot:
        raise ValueError(
            f"a {pad_cutout_width} mm cutout is no wider than the line's "
            f"{slot:.3f} mm coplanar slot, so its taper would not narrow"
        )
    if pad_cutout_width >= GROUND_INNER:
        raise ValueError(
            f"a {pad_cutout_width} mm cutout reaches the ground pads, "
            f"{GROUND_INNER} mm apart"
        )
    start, end = pad_cutout_width / 2, slot / 2
    if reach > 0:
        held = cutout_half_width(reach, start, end, taper_length)
        if held <= edge:
            raise ValueError(
                f"a {pad_cutout_width} mm cutout leaves fence row 1 beside the "
                f"centre pad: row 1's via pads start {edge:.3f} mm from the "
                f"centreline, so the cutout must be wider than {2 * edge:.3f} mm "
                f"to {reach:.3f} mm past the pad, or row 1 comes closer to the "
                f"pad than the {MIN_COPPER_SPACE} mm min_copper_copper_space"
            )
    upper = [(0.0, start)] + [
        (
            CENTER_PAD_LENGTH + taper_length * i / steps,
            cutout_half_width(taper_length * i / steps, start, end, taper_length),
        )
        for i in range(steps + 1)
    ]
    lower = [(x, -y) for x, y in reversed(upper)]
    return upper + lower


def launch_point() -> tuple[float, float]:
    """The launch point in the connector's frame: on the centre pad's axis,
    ``LAUNCH_LENGTH`` past the pad's inner end. It is fixed by the
    connector and the stated length."""
    return (CENTER_PAD_LENGTH + LAUNCH_LENGTH, 0.0)


def tangency_square(side: int) -> Polygon:
    """The square that sets the bend past the launch point, in the
    connector's frame, on ``side`` of the axis (1 for +y, -1 for -y): the
    inside of the turn. It runs from the launch point to ``TANGENCY_SQUARE``
    past it along the axis, its near side ``TANGENCY_CLEARANCE`` off the
    trace's copper edge."""
    if side not in (1, -1):
        raise ValueError(f"side must be 1 or -1, not {side}")
    x0, _ = launch_point()
    near = TRACE_WIDTH / 2 + TANGENCY_CLEARANCE
    far = near + TANGENCY_SQUARE
    return Polygon(
        [
            (x0, side * near),
            (x0 + TANGENCY_SQUARE, side * near),
            (x0 + TANGENCY_SQUARE, side * far),
            (x0, side * far),
        ]
    )


class TangencyTag(Tag):
    """Copper the line keeps ``TANGENCY_CLEARANCE`` from: the squares that
    set its bends."""


class EdgeLaunch(Circuit):
    """One end launch, in the connector's frame: the connector, its straight
    exit to the launch point, the tangency square past it and the cutout
    under the pad. Place it with its origin on the board edge and its +x
    axis into the board.

    ``turn`` is the side the line turns to past the launch point, 1 for the
    connector's +y and -1 for its -y; the square goes on that side.
    ``rf`` is the signal, joined to the centre pin and the launch point.
    Connect ``GND`` to the board ground; the square is on that net.
    """

    rf = Port()
    GND = Port()

    def __init__(self, turn: int = 1) -> None:
        self.connector = Wurth60312202114514().at(0, 0)
        self.launch_point = RoutePoint(layer=RF_LAYER).at(*launch_point())
        self.signal = Net([self.rf, self.connector.sig, self.launch_point.port])
        self.square = Copper(tangency_square(turn), layer=RF_LAYER)
        TangencyTag().assign(self.square)
        self.ground = Net([self.GND, self.connector.gnd, self.square])
        self.exit = Route(self.connector.sig, self.launch_point, layer=RF_LAYER)
        self.cutout = KeepOut(
            Polygon(cutout_outline()),
            layers=LayerSet(*REFERENCE_LAYERS),
            pour=True,
            via=True,
        )


class ConnectorLaunchLine(Circuit):
    """A launch on each board edge and the fenced coplanar line between their
    launch points."""

    def __init__(self) -> None:
        half = BOARD_LENGTH / 2
        # The left launch sits low and the right one high, so the line turns
        # toward +y leaving the left one and toward -y leaving the right one:
        # the connector's +y both times, since the right one is turned 180
        # degrees.
        self.launches = [
            EdgeLaunch(turn=1).at(-half, -LAUNCH_OFFSET / 2),
            EdgeLaunch(turn=1).at(half, LAUNCH_OFFSET / 2, rotate=180),
        ]
        self.rf = Net([launch.rf for launch in self.launches], name="RF")
        RFLineTag().assign(self.rf)
        self.line = Route(
            self.launches[0].launch_point,
            self.launches[1].launch_point,
            layer=RF_LAYER,
        )

        self.gnd = Net([launch.GND for launch in self.launches], name="GND")
        GroundTag().assign(self.gnd)
        outline = rectangle(BOARD_LENGTH - 2 * POUR_INSET, BOARD_WIDTH - 2 * POUR_INSET)
        self.coplanar = Pour(outline, layer=RF_LAYER)
        self.planes = [Pour(outline, layer=layer) for layer in REFERENCE_LAYERS]
        self.gnd += self.coplanar
        for plane in self.planes:
            self.gnd += plane

        # layout_cpwg_two_row_fence's structure and rules, applied as there.
        self.structure = cpwg_structure()
        self.structure_rule = design_constraint(RFLineTag()).routing_structure(
            self.structure, ref_net=self.gnd
        )
        self.gap_rule = design_constraint(
            RFLineTag(), GroundTag(), priority=2
        ).clearance(GAP)
        # Above the gap rule's priority 2: the squares are ground copper.
        self.tangency_rule = design_constraint(
            TangencyTag(), RFLineTag(), priority=3
        ).clearance(TANGENCY_CLEARANCE)


class LaunchBoard(Board):
    shape = rectangle(BOARD_LENGTH, BOARD_WIDTH)


class rf_connector_launch_design(Design):
    """Two SMA end launches joined by the fenced coplanar line, on the
    two-layer sample substrate."""

    board = LaunchBoard()
    substrate = SampleSubstrate()
    circuit = ConnectorLaunchLine()

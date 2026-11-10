"""A fenced 1:4 Wilkinson divider tree, built in code from one 1:2 cell.

``WilkinsonCell`` is one 1:2 divider. ``WilkinsonTree`` puts three of them in
a tree, one cell feeding two, so the circuit hierarchy follows the RF tree.
``WilkinsonFeed`` adds an input connector, four output connectors and the
code routes between them, and a timing constraint asks the router to match
the four paths from the input to each output. Everything is placed with
``.at()``; the placer moves nothing.

The numbers are the example's inputs, chosen for illustration, not validated
RF performance: 5.8 GHz, effective permittivity 4.4, 0.3 mm lines, 0.18 mm
arms (0.6 times the line width), a 2.0 mm input stub, a 100 ohm 0201
isolation resistor, 20 mm output pitch, 20 mm between stages, 2.0 mm
straight exits, 0.2 mm tangency squares 1.0 mm off the trace, and a 0.5 ps
timing tolerance against output 0. The line is declared 50 ohm
(``rf_structure``) and the arm 70.7 ohm (``arm_structure``), but both
impedances are labels on those widths. The board uses the sample substrate,
0.75 mm from top copper to bottom copper, with no dielectric constant set,
which does not realize either one; nothing here solves a width for an
impedance.

The example ports an earlier experiment. It drops that experiment's
soldermask openings over the dividers and along the lines, and its stackup
with its reference and keepout layers. It keeps the experiment's arc guards.

The cell
--------

1. Body. Each arm is a guided quarter wavelength, c / f / sqrt(er) / 4 =
   6.160 mm, bent into an arc whose ends land on the isolation resistor's
   pads. ``pad_pitch`` reads the pad spacing from the resistor's landpattern
   (0.672 mm for the 0201 used here), and ``arc_angle`` solves the sweep:
   170.65 degrees on a 2.068 mm radius per arm. ``CellGeometry`` raises
   ``ValueError`` for a sweep outside 30 to 175 degrees or a radius under
   twice the arm width. Each output stub leaves its arm's end along -y for
   0.6 mm, then turns outward for 2.0 mm to its output pad. An arm and its
   stub share copper only inside the resistor pad they both end on, so the
   arm runs its full quarter wave before its output. The two stubs' first
   legs are 0.372 mm apart, edge to edge, inside the body; the outward legs
   put the two output pads 4.672 mm apart, centre to centre, which holds
   the cell's straight exits to the floor under "The joins". The stubs and arms
   are buffered with flat ends, mitred at the turns, and unioned into one
   polygon, drawn as ``OverlappableCopper``, which is on no net and which
   the router and the overlap checks ignore. ``Polyline`` and
   ``ArcPolyline`` take no end-cap argument on jitx 4.6.0, and in the Python
   conversion they get round caps (a 1 mm, 0.3 mm wide ``Polyline``
   converts to 0.3706 mm squared, not 0.3; what the runtime draws was not
   checked). One flat-ended polygon has no round caps to stick out where an
   arm meets a stub.
2. Port pads. ``CellPorts``, an embedded part that is not soldered and not
   in the BOM, puts a pad the width of the line at the input and at each
   output, where the body ends, with no soldermask opening. Routes end on
   those pads. A ``BridgingPinModel`` from the input to each output carries
   the delay and loss of the drawn centreline (10.760 mm of line, 75.29 ps),
   so the timing constraint resolves through the cell. A
   ``VirtualConnection`` from each output pad to its resistor pad says the
   body joins them, so they report no ratsnest; ``jitx.virtual`` is marked
   experimental.
3. Isolation resistor. ``jitxlib.parts.Resistor(resistance=100 ohm,
   case="0201")``. In this repository it resolves offline, through the parts
   chain in ``pyproject.toml``, from ``src/jitxexamples/parts/example-passives.csv``.
4. Keepouts. ``body_keepout`` covers the body grown by the 0.15 mm
   clearance, on the RF layer, for pours, routes and vias, so pours and
   routes stay off the body. The pour does not avoid the body by itself:
   with ``pour=False`` on this keepout, the top pour covers part of each
   body. ``resistor_keepout`` covers the rectangle over the resistor's two
   pads and the gap between them, grown the same way, for pours and vias.
   There is no via keepout over the ring the arms make: one there removes
   every fence via inside the ring, the first row of the region fence
   included, and leaves the inside of the loop unfenced.
5. Region fence. ``fence_pour`` is a ground ``Pour`` whose outline is the
   body copper itself, on the ground layer, where the fence via stops. It
   carries ``BodyFenceTag``, and the substrate's ``fence_via`` rule on that
   tag puts two rows of vias around it, as in ``fenced_pour_outline``, so
   the body is fenced like a trace: the first row stands 0.6 mm off the body
   copper all the way round, inside the loop as well as outside it. On the
   ground layer the pour realizes as the body's copper. Drawn on the RF
   layer instead, inside the body keepout, it realizes empty, but its fence
   still stands, so either layer gives the same fence. A fence pour grown
   past the body copper moves the rows off the body by the growth. The pour
   gets its ground from the cell's ``GND`` port, which joins nothing else
   inside the cell, so the runtime log of each build warns "The following
   circuit port(s) have no internal connections" for each cell's ``GND``.

The joins
---------

Every line leaves a cell port or a connector straight along the pad's axis
to a route point: at a cell, ``TANGENT_LENGTH`` past the pad's outer edge,
and at a connector, the same distance past the inner end of the connector's
centre pad. Their positions follow from the pads; no designer places them.

Where the line turns past that route point, a square of ground copper on the
inside of the turn sets the bend (``tangency_square``): ``TANGENCY_SQUARE``
(0.2 mm) on a side, from the route point to 0.2 mm past it along the axis,
its near side ``TANGENCY_CLEARANCE`` (1.0 mm) off the trace's copper edge.
The squares carry ``TangencyTag``, and
``design_constraint(TangencyTag(), RFLineTag()).clearance(1.0)`` holds the
lines' copper that far from them. A plain route then holds the axis past the
square's far edge and bends around its corner on a centre-line radius of
half the trace plus the clearance, 1.15 mm, so the clearance to the square
sets the bend. A square nearer the trace than the clearance leaves the route
unrealized, and a rule clearance under the structure's own loses to it. The
square is copper, not a keepout: a route keepout gets no clearance, so the
line runs along its edge and bends at half the trace whatever the clearance.
The input line runs straight on. Each of its two squares, one past each
end's route point, sits to the left of its own exit's axis, and the two axes
point opposite ways, so the squares sit on opposite sides of the line, each
the clearance off its copper edge. The line is straight, so neither sets a
bend; they are there so that every port and connector exit has its square.

Each join and each output feed is a ``Section`` of five routes: the straight
exit; a plain route around the exit's square to a bend route point
``BEND_REACH`` (3.0 mm) on, 45 degrees off the axis toward the turn; a middle
route with ``Route.Config(envelope_overhead=ENVELOPE)``, a region 3.0 mm
wider than the trace in which the router may meander it to meet the timing
constraint; the same bend at the far end; and the straight entry. The middle
route runs only between the bend points because a route with an envelope
does not keep the clearance to tagged copper: its copper can reach a square
and no issue is reported. The translator also warns that length-matched
routes should end at route points, which can resize to fit the meander
envelope.

The routes run on ``rf_structure``, whose ``RoutingStructure.Layer.fence``
adds two rows of ground vias along each route. A ``routing_structure`` rule
on ``RFLineTag`` applies it to every RF net, with the board ground as
reference net. The first cell sits ``FEED_OFFSET`` below the tree's axis, so
the two joins differ in length and the router has something to match.

A cell's straight exits, each from its port pad along the pad's axis to
its square's far edge, stand at least the floor apart at their closest,
whichever way they point. The floor is set by two lines leaving side by
side, so that neither line's fence rows crowd the other's: each line's
outer fence row, 1.35 mm off its centre line, twice, plus the space
between two fence via centres, 0.554 mm for this via's 0.3 mm drill and
the sample fabrication
constraints' 0.254 mm ``min_hole_to_hole``, 3.254 mm in all. Here the two
output exits are collinear and leave in opposite directions, so they are
closest at the output pads, 4.672 mm apart.

The connectors are Würth Elektronik 60312202114514 WR-SMA end launch jacks
(``components/connectors/wurth_elektronik_60312202114514``). Each sits with
its body face on a board edge and its centre pad running into the board: the
input on the left edge and the four outputs on the right, which sets the
board's width. The part has ground pads on the top and on the bottom, so the
ground plane on the bottom layer has a ground object on its layer and fills
with no via placed to anchor it. The connector's 1.73 mm slot is for a
1.6 mm board, so it would not clamp this one; the example uses the part for
its land pattern. The component module keeps the URL of the vendor's HFSS
model for later use. The pads start at the board edge, closer to it than
the sample fabrication constraints' 0.5 mm ``min_copper_edge_space``
allows. Land-pattern pads are placed as drawn, and pads closer to the edge
than ``min_copper_edge_space`` raise no design issue, so confirm the edge
distance with your fabricator and check realized copper with your
fabricator's design rule check.

``ConstrainReferenceDifference`` bounds each output against output 0, so two
other outputs can differ by up to twice the tolerance. At 0.5 ps against
output 0, any two outputs fall within 1 ps, 2.09 degrees at 5.8 GHz.

The design builds with every route routed and the timing constraint met.
The router meanders until each output stands just inside the 0.5 ps
tolerance of output 0, so the worst pair, an output on each side of output
0, differs by just under 1 ps. The top pour stops the body keepout's 0.15 mm
from every body and covers none of it.

The region fence's first row stands all the way round inside the loop.
Its second row comes back with few vias; why is not known. Five of the
six output exits keep both route fence rows on both sides. Along the exit
of the first output section (``feeds[0]``), the outer row on the inside of
the turn comes back with no vias; why is not known. Count the rows in your own build if your design
depends on them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import shapely
from shapely.geometry.base import BaseGeometry
from jitx import KeepOut, LayerSet, Net, Pour
from jitx.board import Board
from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.constraints import Tag, ViaFencePattern, design_constraint
from jitx.container import Container
from jitx.controlpoint import RoutePoint
from jitx.copper import Copper
from jitx.design import Design
from jitx.feature import OverlappableCopper
from jitx.inspect import visit
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Port, Topology
from jitx.placement import Positionable
from jitx.sample import SampleSubstrate
from jitx.shapes import Shape
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Polygon
from jitx.shapes.shapely import ShapelyGeometry
from jitx.si import BridgingPinModel, ConstrainReferenceDifference, RoutingStructure
from jitx.transform import Point, Transform
from jitx.units import ohm
from jitx.virtual import VirtualConnection
from jitxlib.parts import Resistor
from jitxlib.physics import phase_velocity
from jitxlib.symbols.box import BoxSymbol

from jitxexamples.components.connectors.wurth_elektronik_60312202114514 import (
    CENTER_PAD_LENGTH,
    Wurth60312202114514,
)

SPEED_OF_LIGHT = 299_792_458e3
"""Speed of light in vacuum, in mm/s."""

FREQUENCY = 5.8e9
"""Design frequency, in Hz."""

EFFECTIVE_ER = 4.4
"""Effective relative permittivity of the microstrip."""

Z0 = 50.0
"""System impedance, in ohms. The isolation resistor is twice this."""

TRACE_WIDTH = 0.3
"""Width of the lines and stubs, in mm, labelled 50 ohm in ``rf_structure``."""

ARM_WIDTH = 0.18
"""Width of the arms, in mm: 0.6 times the line width. ``arm_structure``
declares it as the 70.7 ohm arm line, and the body reads it from there."""

INPUT_STUB_LENGTH = 2.0
"""Length of the stub from the input pad to the arms, in mm."""

OUTPUT_DROP = 0.6
"""Length of each output stub's first leg, along -y from its arm's end, in
mm."""

OUTPUT_STUB_LENGTH = 2.0
"""Length of each output stub's second leg, outward from the turn to the
output pad, in mm. The exit floor under "The joins" needs 1.29 mm here.
With legs from 1.3 to 1.9 mm, the region fence's first row inside the loop
came back with a via missing beside a route fence via, for a reason not
known; at 2.0 mm the row stands full."""

MIN_ARC_DEGREES = 30.0
"""Smallest arm sweep the cell accepts, in degrees."""

MAX_ARC_DEGREES = 175.0
"""Largest arm sweep the cell accepts, in degrees."""

RESISTOR_CASE = "0201"
"""Package of the isolation resistor."""

CLEARANCE = 0.15
"""Gap from RF copper to other copper on the RF layer, in mm."""

INSERTION_LOSS = 0.05
"""Line loss, in dB/mm."""

RF_LAYER = 0
"""Layer of the lines and the divider bodies."""

GROUND_LAYER = 1
"""Reference plane layer, and the layer the fence via stops on."""

FENCE_VIA = SampleSubstrate.THVia
"""Via used by both fences: 0.45 mm pad, 0.3 mm drill."""

FENCE_PATTERN = ViaFencePattern(pitch=1.0, offset=0.6, initial_offset=0.6, num_rows=2)
"""Two rows at 1.0 mm pitch, the first 0.6 mm out from the copper edge and the
second 0.6 mm beyond it."""

OUTPUT_PITCH = 20.0
"""Distance between neighbouring output connectors, in mm. The second-stage
cells sit at plus and minus this, so they are twice it apart, each centred
between its two connectors."""

STAGE_SPACING = 20.0
"""Distance from the first cell to the second-stage cells, in mm."""

FEED_OFFSET = 4.0
"""How far the first cell sits below the tree's axis, in mm. It makes the two
joins differ in length."""

ENVELOPE = 3.0
"""Width, beyond the trace, of the region each matched section may meander
in, in mm."""

INPUT_RUN = 15.0
"""Distance along x from the input connector to the first cell, in mm. The
output connectors sit ``STAGE_SPACING`` beyond the second-stage cells."""

BOARD_MARGIN = 10.0
"""Board edge distance beyond the outermost output connectors along y, in
mm."""

BOARD_WIDTH = INPUT_RUN + 2 * STAGE_SPACING
"""Board width along x, in mm: the input-to-output connector span. The
connectors are end launches, so their body faces sit on the left and right
board edges."""

BOARD_HEIGHT = 3 * OUTPUT_PITCH + 2 * BOARD_MARGIN
"""Board height along y, in mm: the span of the four output connectors plus
the margin on each side."""

TIMING_TOLERANCE = 0.5e-12
"""Allowed delay difference from output 0 to each other output, in s. Any two
outputs then differ by at most twice this, 1 ps."""

TANGENT_LENGTH = 2.0
"""How far each port's straight exit runs past the pad's outer edge, in mm,
to its route point."""

TANGENCY_SQUARE = 0.2
"""Side of the ground copper square past each exit's route point, in mm."""

TANGENCY_CLEARANCE = 1.0
"""Clearance from a line's copper to each tangency square, in mm. The
square's near side stands this far off the trace's copper edge, and the line
bends around the square's corner on a centre-line radius of half the trace
plus this."""

BEND_REACH = 3.0
"""How far each section's bend route point stands from its exit's route
point, in mm, at 45 degrees off the exit's axis toward the turn: clear of
the square, so the matched route starts and ends clear of it."""

IN_DIRECTION = (0.0, 1.0)
"""Direction a line leaves the input pad by, in the cell's frame."""

OUT_A_DIRECTION = (-1.0, 0.0)
"""Direction a line leaves output A by, in the cell's frame."""

OUT_B_DIRECTION = (1.0, 0.0)
"""Direction a line leaves output B by, in the cell's frame."""


def quarter_wavelength(frequency: float, er: float) -> float:
    """Guided quarter wavelength at ``frequency`` (Hz), in mm."""
    return SPEED_OF_LIGHT / frequency / math.sqrt(er) / 4


def arc_angle(length: float, chord: float) -> float:
    """Half the sweep, in radians, of an arc of ``length`` whose ends are
    ``chord`` apart: the root of ``length * sin(t) / t = chord`` on (0, pi).
    With the radius ``length / (2 * t)``, each half of the arc turns through
    ``t``."""
    if not 0 < chord < length:
        raise ValueError(f"chord {chord} mm is out of reach of a {length} mm arc")
    lo, hi = 1e-9, math.pi
    for _ in range(200):
        mid = (lo + hi) / 2
        if length * math.sin(mid) / mid > chord:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def pad_pitch(part: Component) -> float:
    """Centre-to-centre distance of a two-terminal part's pads, read from its
    landpattern."""
    centres = [pad.transform.trs[0] for _, pad in visit(part, Pad) if pad.transform]
    if len(centres) != 2:
        raise ValueError(f"expected two pads, found {len(centres)}")
    (x1, y1), (x2, y2) = centres
    return math.hypot(x2 - x1, y2 - y1)


def _arc_points(
    radius: float, start_deg: float, sweep_deg: float, steps: int = 180
) -> list[tuple[float, float]]:
    """Points along an arc centred ``radius`` below the origin, starting at
    ``start_deg`` and turning through ``sweep_deg``."""
    points = []
    for i in range(steps + 1):
        a = math.radians(start_deg + sweep_deg * i / steps)
        points.append((radius * math.cos(a), -radius + radius * math.sin(a)))
    return points


@dataclass(frozen=True)
class CellGeometry:
    """One cell's copper in its own frame: the input pad above the origin, the
    two arms leaving the origin left and right and curling down to end on the
    resistor's pads, and the output stubs leaving the arm ends straight down,
    then turning outward to the output pads."""

    quarter_wave: float
    arm_width: float
    angle: float
    radius: float
    input_pad: tuple[float, float]
    out_a: tuple[float, float]
    out_b: tuple[float, float]
    arm_end_a: tuple[float, float]
    arm_end_b: tuple[float, float]

    @classmethod
    def from_inputs(cls, resistor_pitch: float, arm_width: float) -> CellGeometry:
        """Solve the arms so their ends are ``resistor_pitch`` apart.

        Raises ``ValueError`` when an arm would sweep less than 30 or more
        than 175 degrees, or when the arc radius is under twice the arm
        width: the guards of the experiment this example comes from."""
        q = quarter_wavelength(FREQUENCY, EFFECTIVE_ER)
        # Both arms together are one arc of length 2q, half-sweep theta, so
        # each arm turns through theta.
        theta = arc_angle(2 * q, resistor_pitch)
        r = q / theta
        if not MIN_ARC_DEGREES <= math.degrees(theta) <= MAX_ARC_DEGREES:
            raise ValueError(
                f"arm sweep {math.degrees(theta):.1f} degrees is outside "
                f"[{MIN_ARC_DEGREES}, {MAX_ARC_DEGREES}]"
            )
        if r < 2 * arm_width:
            raise ValueError(
                f"arc radius {r:.3f} mm is under twice the arm width {arm_width} mm"
            )
        end_x = r * math.cos(math.pi / 2 + theta)
        end_y = -r + r * math.sin(math.pi / 2 + theta)
        turn_y = end_y - OUTPUT_DROP
        return cls(
            quarter_wave=q,
            arm_width=arm_width,
            angle=theta,
            radius=r,
            input_pad=(0.0, INPUT_STUB_LENGTH),
            out_a=(end_x - OUTPUT_STUB_LENGTH, turn_y),
            out_b=(-end_x + OUTPUT_STUB_LENGTH, turn_y),
            arm_end_a=(end_x, end_y),
            arm_end_b=(-end_x, end_y),
        )

    @property
    def path_length(self) -> float:
        """Input pad to either output pad, along the drawn centreline: the
        input stub, one arm, and both legs of an output stub."""
        return INPUT_STUB_LENGTH + self.quarter_wave + OUTPUT_DROP + OUTPUT_STUB_LENGTH

    def body(self) -> shapely.Polygon:
        """The body outline: stubs and arms, flat-ended where they meet, with a
        mitred corner where each output stub turns."""
        sweep = math.degrees(self.angle)
        pieces = [
            shapely.LineString([self.input_pad, (0.0, 0.0)]).buffer(
                TRACE_WIDTH / 2, cap_style="flat"
            ),
            shapely.LineString(_arc_points(self.radius, 90.0, sweep)).buffer(
                self.arm_width / 2, cap_style="flat"
            ),
            shapely.LineString(_arc_points(self.radius, 90.0, -sweep)).buffer(
                self.arm_width / 2, cap_style="flat"
            ),
            *[
                shapely.LineString([end, (end[0], out[1]), out]).buffer(
                    TRACE_WIDTH / 2, cap_style="flat", join_style="mitre"
                )
                for end, out in (
                    (self.arm_end_a, self.out_a),
                    (self.arm_end_b, self.out_b),
                )
            ],
        ]
        body = shapely.union_all(pieces)
        assert isinstance(body, shapely.Polygon)
        return body


def _pad_copper(part: Component) -> BaseGeometry:
    """Union of a placed part's pads, in the frame the part is placed in."""
    placement = part.transform
    assert isinstance(placement, Transform)
    shapes: list[BaseGeometry] = []
    for _, pad in visit(part, Pad):
        assert pad.transform is not None
        shape = pad.shape if isinstance(pad.shape, Shape) else pad.shape.shape
        shapes.append((placement * pad.transform * shape).to_shapely().g)
    return shapely.union_all(shapes)


def _polygon(g: BaseGeometry) -> Polygon:
    primitive = ShapelyGeometry(g).to_primitive()
    assert isinstance(primitive, Polygon)
    return primitive


class PortPad(Pad):
    """A square pad the width of the line, where a route meets the body. It
    sits mid-line and nothing is soldered to it, so it has no soldermask
    opening."""

    def __init__(self) -> None:
        self.shape = rectangle(TRACE_WIDTH, TRACE_WIDTH)


class CellPortPads(Landpattern):
    def __init__(self, g: CellGeometry) -> None:
        self.sig_in = PortPad().at(*g.input_pad, rotate=90)
        self.sig_out_a = PortPad().at(*g.out_a, rotate=180)
        self.sig_out_b = PortPad().at(*g.out_b)


class CellPorts(Component):
    """The cell's three port pads, the ends routes attach to."""

    manufacturer = "Embedded"
    mpn = "WILKINSON-PORTS"
    reference_designator_prefix = "X"
    in_bom = False
    soldered = False

    sig_in = Port()
    sig_out_a = Port()
    sig_out_b = Port()

    def __init__(self, g: CellGeometry) -> None:
        self.landpattern = CellPortPads(g)
        self.symbol = BoxSymbol()
        self.mappings = [
            PadMapping(
                {
                    self.sig_in: self.landpattern.sig_in,
                    self.sig_out_a: self.landpattern.sig_out_a,
                    self.sig_out_b: self.landpattern.sig_out_b,
                }
            )
        ]


class BodyFenceTag(Tag):
    """Pours drawn in a cell body's outline: fence vias go around them."""


class RFLineTag(Tag):
    """Nets that run on the fenced structure, ``rf_structure``."""


class WilkinsonSubstrate(SampleSubstrate):
    """The two-layer sample substrate with the body fence rule attached."""

    body_fence = design_constraint(BodyFenceTag()).fence_via(FENCE_VIA, FENCE_PATTERN)


def tangent_end(
    placement: Transform, pad: tuple[float, float], direction: tuple[float, float]
) -> Point:
    """End of a port's straight exit, ``TANGENT_LENGTH`` past the pad's outer
    edge, mapped by ``placement`` from the cell's frame into the caller's."""
    reach = TRACE_WIDTH / 2 + TANGENT_LENGTH
    return placement * (pad[0] + direction[0] * reach, pad[1] + direction[1] * reach)


def mapped_direction(placement: Transform, direction: tuple[float, float]) -> Point:
    """``direction`` in the cell's frame, turned by ``placement`` into the
    caller's frame."""
    ox, oy = placement * (0.0, 0.0)
    x, y = placement * direction
    return (x - ox, y - oy)


def turn_side(point: Point, direction: Point, toward: Point) -> int:
    """The side of a line leaving ``point`` along ``direction`` that
    ``toward`` lies on: 1 for its left, -1 for its right. The line turns
    that way, so that is the inside of the turn."""
    across = -direction[1] * (toward[0] - point[0]) + direction[0] * (
        toward[1] - point[1]
    )
    return 1 if across >= 0 else -1


def tangency_square(point: Point, direction: Point, side: int) -> Polygon:
    """The square past an exit's route point ``point``, on ``side`` (1 for
    the left of ``direction``, -1 for its right): from the point to
    ``TANGENCY_SQUARE`` further along ``direction``, its near side
    ``TANGENCY_CLEARANCE`` off the trace's copper edge."""
    near = side * (TRACE_WIDTH / 2 + TANGENCY_CLEARANCE)
    far = side * (TRACE_WIDTH / 2 + TANGENCY_CLEARANCE + TANGENCY_SQUARE)
    dx, dy = direction
    return Polygon(
        [
            (point[0] + dx * along - dy * across, point[1] + dy * along + dx * across)
            for along, across in (
                (0.0, near),
                (TANGENCY_SQUARE, near),
                (TANGENCY_SQUARE, far),
                (0.0, far),
            )
        ]
    )


def bend_point(point: Point, direction: Point, side: int) -> Point:
    """``BEND_REACH`` from ``point``, 45 degrees off ``direction`` toward
    ``side`` (1 for its left)."""
    k = BEND_REACH / math.sqrt(2.0)
    dx, dy = direction
    return (point[0] + k * (dx - side * dy), point[1] + k * (dy + side * dx))


class TangencyTag(Tag):
    """Copper the lines keep ``TANGENCY_CLEARANCE`` from: the squares that
    set their bends."""


class WilkinsonCell(Circuit):
    """One 1:2 Wilkinson divider, fenced, with tangent ports.

    Connect ``GND`` to the board ground; the region fence is on that net.
    """

    sig_in = Port()
    sig_out_a = Port()
    sig_out_b = Port()
    GND = Port()

    def __init__(self) -> None:
        self.isolation = Resistor(resistance=2 * Z0 * ohm, case=RESISTOR_CASE)
        # Kept on self: a structure dropped during instantiation logs "lost
        # during instantiation".
        self.arm_structure = arm_structure()
        arm = self.arm_structure.layers[RF_LAYER]
        g = CellGeometry.from_inputs(pad_pitch(self.isolation), arm.trace_width)
        self.geometry = g

        self.ports = CellPorts(g).at(0, 0)
        self.isolation.at(0, g.arm_end_a[1], rotate=90)

        body = g.body()
        self.body = OverlappableCopper(_polygon(body), layer=RF_LAYER)
        outline = _polygon(body.buffer(CLEARANCE))
        self.body_keepout = KeepOut(
            outline, layers=LayerSet(RF_LAYER), pour=True, route=True, via=True
        )
        # The resistor's pads stick out past the arm ends, so they get their
        # own keepout: the hull of both pads, grown by the clearance.
        pads = _pad_copper(self.isolation)
        self.resistor_keepout = KeepOut(
            _polygon(pads.convex_hull.buffer(CLEARANCE)),
            layers=LayerSet(RF_LAYER),
            pour=True,
            via=True,
        )
        # The region fence's pour is the body copper itself, so the body is
        # fenced like a trace.
        self.fence_pour = Pour(_polygon(body), layer=GROUND_LAYER)
        BodyFenceTag().assign(self.fence_pour)
        self.ground = Net([self.GND, self.fence_pour])

        self.line_in = Net([self.sig_in, self.ports.sig_in])
        self.line_a = Net([self.sig_out_a, self.ports.sig_out_a, self.isolation.p1])
        self.line_b = Net([self.sig_out_b, self.ports.sig_out_b, self.isolation.p2])
        self.bridges = [
            VirtualConnection(
                port, pad, source_layer=RF_LAYER, destination_layer=RF_LAYER
            )
            for port, pad in (
                (self.ports.sig_out_a, self.isolation.p1),
                (self.ports.sig_out_b, self.isolation.p2),
            )
        ]

        delay = g.path_length / phase_velocity(EFFECTIVE_ER)
        loss = g.path_length * INSERTION_LOSS
        self.models = [
            BridgingPinModel(self.ports.sig_in, out, delay=delay, loss=loss)
            for out in (self.ports.sig_out_a, self.ports.sig_out_b)
        ]


def arm_structure() -> RoutingStructure:
    """The arm line, declared 70.7 ohm (Z0 times the square root of 2, what a
    Wilkinson arm needs) at ``ARM_WIDTH``. The impedance is a label: nothing
    here solves the width for it. Build it inside a circuit's ``__init__``,
    like ``rf_structure``."""
    return RoutingStructure(
        {
            RF_LAYER: RoutingStructure.Layer(
                trace_width=ARM_WIDTH,
                clearance=CLEARANCE,
                velocity=phase_velocity(EFFECTIVE_ER),
                insertion_loss=INSERTION_LOSS,
            )
        },
        impedance=round(Z0 * math.sqrt(2), 1) * ohm,
        name="Wilkinson arm",
    )


def rf_structure() -> RoutingStructure:
    """The fenced microstrip the routes use, declared 50 ohm. Build it inside
    a circuit's ``__init__``: a ``RoutingStructure`` built at module level
    fails to translate."""
    return RoutingStructure(
        {
            RF_LAYER: RoutingStructure.Layer(
                trace_width=TRACE_WIDTH,
                clearance=CLEARANCE,
                velocity=phase_velocity(EFFECTIVE_ER),
                insertion_loss=INSERTION_LOSS,
            ).fence(FENCE_VIA, FENCE_PATTERN, reference_layer=GROUND_LAYER)
        },
        impedance=Z0 * ohm,
        name="Fenced 50 ohm microstrip",
    )


def _transform(obj: Positionable) -> Transform:
    t = obj.transform
    assert isinstance(t, Transform)
    return t


class Section(Container):
    """A join between two pads, in five routes: a straight exit to a route
    point on the source pad's axis, a bend around that exit's tangency square
    to a second route point, a middle the router may meander within
    ``envelope``, the same bend at the far end, and a straight entry.

    ``src_point`` and ``dst_point`` are the exits' route points and
    ``src_direction`` and ``dst_direction`` their axes, pointing away from
    the pads. Each square goes on the inside of its exit's turn, the side the
    other end lies on, and joins ``gnd``. The route points follow from the
    pads and the stated lengths; nothing here is a designer's choice."""

    def __init__(
        self,
        net: Net,
        gnd: Net,
        src: Port,
        src_point: Point,
        src_direction: Point,
        dst: Port,
        dst_point: Point,
        dst_direction: Point,
        envelope: float,
    ) -> None:
        src_side = turn_side(src_point, src_direction, dst_point)
        dst_side = turn_side(dst_point, dst_direction, src_point)
        self.start = RoutePoint(layer=RF_LAYER).at(*src_point)
        self.bend_start = RoutePoint(layer=RF_LAYER).at(
            *bend_point(src_point, src_direction, src_side)
        )
        self.bend_end = RoutePoint(layer=RF_LAYER).at(
            *bend_point(dst_point, dst_direction, dst_side)
        )
        self.end = RoutePoint(layer=RF_LAYER).at(*dst_point)
        for point in (self.start, self.bend_start, self.bend_end, self.end):
            net += point.port
        self.squares = [
            Copper(tangency_square(src_point, src_direction, src_side), layer=RF_LAYER),
            Copper(tangency_square(dst_point, dst_direction, dst_side), layer=RF_LAYER),
        ]
        TangencyTag().assign(self.squares)
        for square in self.squares:
            gnd += square
        # A route with an envelope does not keep the clearance to the
        # squares, so the matched route runs only between the bend points.
        self.routes = [
            Route(src, self.start, layer=RF_LAYER),
            Route(self.start, self.bend_start, layer=RF_LAYER),
            Route(
                self.bend_start,
                self.bend_end,
                layer=RF_LAYER,
                config=Route.Config(envelope_overhead=envelope),
            ),
            Route(self.bend_end, self.end, layer=RF_LAYER),
            Route(self.end, dst, layer=RF_LAYER),
        ]


class WilkinsonTree(Circuit):
    """Three cells as a 1:4 tree: one cell feeding two.

    ``rf_out`` runs from the bottom output to the top one.
    """

    rf_in = Port()
    rf_out = [Port() for _ in range(4)]
    GND = Port()

    def __init__(self, envelope: float = ENVELOPE) -> None:
        self.first = WilkinsonCell().at(0, -FEED_OFFSET, rotate=90)
        self.second = [
            WilkinsonCell().at(STAGE_SPACING, y, rotate=90)
            for y in (-OUTPUT_PITCH, OUTPUT_PITCH)
        ]
        self.ground = Net([self.GND, self.first.GND] + [c.GND for c in self.second])
        self.feed = Net([self.rf_in, self.first.sig_in])
        self.joins_nets = [
            Net([self.first.sig_out_a, self.second[0].sig_in]),
            Net([self.first.sig_out_b, self.second[1].sig_in]),
        ]
        self.outs = [
            Net([out, cell_port])
            for out, cell_port in zip(
                self.rf_out,
                [p for c in self.second for p in (c.sig_out_a, c.sig_out_b)],
                strict=True,
            )
        ]
        first = _transform(self.first)
        g = self.first.geometry
        self.joins = [
            Section(
                net,
                self.ground,
                src,
                tangent_end(first, pad, direction),
                mapped_direction(first, direction),
                cell.ports.sig_in,
                tangent_end(_transform(cell), cell.geometry.input_pad, IN_DIRECTION),
                mapped_direction(_transform(cell), IN_DIRECTION),
                envelope,
            )
            for net, src, pad, direction, cell in (
                (
                    self.joins_nets[0],
                    self.first.ports.sig_out_a,
                    g.out_a,
                    OUT_A_DIRECTION,
                    self.second[0],
                ),
                (
                    self.joins_nets[1],
                    self.first.ports.sig_out_b,
                    g.out_b,
                    OUT_B_DIRECTION,
                    self.second[1],
                ),
            )
        ]


class WilkinsonFeed(Circuit):
    """The tree between one input connector and four output connectors."""

    def __init__(self, envelope: float = ENVELOPE) -> None:
        # The connectors span INPUT_RUN + 2 * STAGE_SPACING along x, centred
        # on the board. Each second-stage cell, at plus or minus OUTPUT_PITCH,
        # sits midway between its two output connectors.
        in_x = -(INPUT_RUN + 2 * STAGE_SPACING) / 2
        self.tree = WilkinsonTree(envelope).at(in_x + INPUT_RUN, 0)
        # Each connector's origin is its body face, on the board edge, and its
        # +x axis runs into the board along the centre pad.
        self.j_in = Wurth60312202114514().at(in_x, -FEED_OFFSET)
        self.j_out = [
            Wurth60312202114514().at(
                in_x + INPUT_RUN + 2 * STAGE_SPACING, y, rotate=180
            )
            for cell_y in (-OUTPUT_PITCH, OUTPUT_PITCH)
            for y in (cell_y - OUTPUT_PITCH / 2, cell_y + OUTPUT_PITCH / 2)
        ]
        self.gnd = Net(name="GND")
        self.gnd += self.tree.GND
        for j in [self.j_in, *self.j_out]:
            self.gnd += j.gnd
        self.top = Pour(rectangle(BOARD_WIDTH - 2, BOARD_HEIGHT - 2), layer=RF_LAYER)
        self.plane = Pour(
            rectangle(BOARD_WIDTH - 2, BOARD_HEIGHT - 2), layer=GROUND_LAYER
        )
        self.gnd += self.top
        self.gnd += self.plane
        # A pour with no same-net object on its layer comes back empty, and
        # fence vias do not count. The connectors' ground pads on the bottom
        # are on the plane's layer, so the plane fills with no via placed to
        # anchor it.

        self.rf_rule = design_constraint(RFLineTag()).routing_structure(
            rf_structure(), ref_net=self.gnd
        )
        self.lines = [
            Net([self.j_in.sig, self.tree.rf_in]),
            *[
                Net([j.sig, out])
                for j, out in zip(self.j_out, self.tree.rf_out, strict=True)
            ],
        ]
        for n in [*self.lines, self.tree.feed, *self.tree.joins_nets, *self.tree.outs]:
            RFLineTag().assign(n)

        tree = _transform(self.tree)
        # The input connector sits on the first cell's axis, so the input
        # line runs straight on: route points on the axis at both ends, a
        # square past each to the left of that end's own outward axis (so on
        # opposite sides of the line), and no bend or envelope. The input is
        # common to every path, so it needs no matching.
        first = tree * _transform(self.tree.first)
        in_points = [
            _transform(self.j_in) * (CENTER_PAD_LENGTH + TANGENT_LENGTH, 0.0),
            tangent_end(first, self.tree.first.geometry.input_pad, IN_DIRECTION),
        ]
        in_directions = [
            mapped_direction(_transform(self.j_in), (1.0, 0.0)),
            mapped_direction(first, IN_DIRECTION),
        ]
        self.input_points = [RoutePoint(layer=RF_LAYER).at(*p) for p in in_points]
        for point in self.input_points:
            self.lines[0] += point.port
        self.input_squares = [
            Copper(tangency_square(p, d, 1), layer=RF_LAYER)
            for p, d in zip(in_points, in_directions, strict=True)
        ]
        TangencyTag().assign(self.input_squares)
        for square in self.input_squares:
            self.gnd += square
        self.input_routes = [
            Route(self.j_in.sig, self.input_points[0], layer=RF_LAYER),
            Route(self.input_points[0], self.input_points[1], layer=RF_LAYER),
            Route(self.input_points[1], self.tree.first.ports.sig_in, layer=RF_LAYER),
        ]
        exits = [
            (cell, port, pad, direction)
            for cell in self.tree.second
            for port, pad, direction in (
                (cell.ports.sig_out_a, cell.geometry.out_a, OUT_A_DIRECTION),
                (cell.ports.sig_out_b, cell.geometry.out_b, OUT_B_DIRECTION),
            )
        ]
        self.feeds = [
            Section(
                line,
                self.gnd,
                port,
                tangent_end(tree * _transform(cell), pad, direction),
                mapped_direction(tree * _transform(cell), direction),
                j.sig,
                _transform(j) * (CENTER_PAD_LENGTH + TANGENT_LENGTH, 0.0),
                mapped_direction(_transform(j), (1.0, 0.0)),
                envelope,
            )
            for line, (cell, port, pad, direction), j in zip(
                self.lines[1:], exits, self.j_out, strict=True
            )
        ]

        self.tangency_rule = design_constraint(TangencyTag(), RFLineTag()).clearance(
            TANGENCY_CLEARANCE
        )

        paths = [Topology(self.j_in.sig, j.sig) for j in self.j_out]
        self.matching = ConstrainReferenceDifference(
            paths[0], paths[1:]
        ).timing_difference(TIMING_TOLERANCE)


class WilkinsonBoard(Board):
    shape = rectangle(BOARD_WIDTH, BOARD_HEIGHT, radius=2)


class wilkinson_tree_design(Design):
    """The fenced 1:4 Wilkinson tree on the two-layer sample substrate."""

    board = WilkinsonBoard()
    substrate = WilkinsonSubstrate()
    circuit = WilkinsonFeed()

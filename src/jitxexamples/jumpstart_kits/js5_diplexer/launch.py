"""The edge-launch geometry of each Würth 60312202114514 WR-SMA jack: where
it sits on its board edge, its straight exit, the ground cutout under its
centre pad, its in-pad ground vias and the via keep-off over its ground pads.

Shapes are in the jack frame unless a function says board frame. The jack
frame is the land pattern's (``jitxexamples.components.connectors.
wurth_elektronik_60312202114514``): x = 0 on the body face, which sits on the
board edge, +x into the board along the centre pad, pads centred on y = 0.
The module says that frame is also the frame of Würth's HFSS model, which
the run that produced this board confirmed by inspection.

The functions at the end (``launch_point`` to ``in_pad_via_keepoffs``) build
one jack's launch objects in the board frame. :py:mod:`.main` calls them for
its three jacks; the run's launch-thru fixture called them for two jacks back
to back, so the launch it tuned is the board's by construction.

What the part asks for (module docstring, from the data sheet drawing's
recommended land pattern, rev 001.001): a 0.61 mm centre pad at least 1.97 mm
from the board end, and ground pads 9.9 outer by 7.1 inner overall width by
5.0 long on the top AND the bottom of the board, the shell straddling the
edge. The drawing gives no ground vias ("The land pattern has no ground
vias") and says the VSWR "varies decisively according to PCB layout". What
this board adds to that, each with its source:

- the straight exit and the bottom-ground cutout under the centre pad, from
  ``jitxexamples.patterns.rf_connector_launch`` (the idiom; its numbers are
  illustrative, not solved, and are kept here as starting values);
- in-pad ground vias joining each top ground pad to the bottom one under it
  (``GROUND_VIA_*``): the part's top and bottom pads are one shell contact,
  and on a 0.76 mm board nothing else ties them together at the launch. They
  are plated and left open (``DiplexerSubstrate.InPadVia``): JLCPCB neither
  fills nor caps vias on its Rogers boards;
- a generated-via keep-off over each ground pad: the stitch grid's
  ``StdVia`` is not a via-in-pad via, so none may land in a solder pad;
- a neck on the exit's last ``EXIT_NECK_LENGTH`` (:py:mod:`.lines`
  ``EXIT_NECK_WIDTH`` in the line's own slot) that cancels the launch's
  excess shunt capacitance (the run's launch tuning, step S2).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import shapely
from jitx import KeepOut, LayerSet
from jitx.circuit import Route
from jitx.controlpoint import RoutePoint
from jitx.net import Port
from jitx.shapes import Shape
from jitx.shapes.shapely import ShapelyGeometry
from jitx.transform import Transform
from jitx.via import Via
from jitxexamples.components.connectors.wurth_elektronik_60312202114514 import (
    CENTER_PAD_LENGTH,
    GROUND_INNER,
    GROUND_LENGTH,
    GROUND_OUTER,
)
from jitxexamples.patterns.rf_connector_launch import cutout_half_width

from .lines import (
    EXIT_NECK_LENGTH,
    FLOOR_MARGIN,
    PLANE_LAYER,
    RF_LAYER,
    ExitNeckTag,
    rs50_gap,
    rs50_half_width,
    via_keepoff,
)
from .substrate import DiplexerSubstrate

GROUND_PAD_Y = (GROUND_OUTER + GROUND_INNER) / 4
"""Each ground pad's centre off the axis, mm: (9.9 + 7.1) / 4 = 4.25 (module
land pattern)."""

GROUND_PAD_WIDTH = (GROUND_OUTER - GROUND_INNER) / 2
"""Each ground pad's width across the axis, mm: (9.9 - 7.1) / 2 = 1.40."""


@dataclass(frozen=True)
class JackPlacement:
    """Where a jack's origin sits on its board edge, and which way its +x
    (into the board, along the centre pad) points."""

    x: float
    y: float
    rotate: float

    @property
    def transform(self) -> Transform:
        return Transform((self.x, self.y), rotate=self.rotate)

    def board(self, x: float, y: float) -> tuple[float, float]:
        """A jack-frame point in board coordinates, rounded to 1 nm so that a
        rotation leaves no residue."""
        bx, by = self.transform * (x, y)
        return (round(bx, 6), round(by, 6))

    def launch_point(self) -> tuple[float, float]:
        """The launch point, board frame: on the centre pad's axis,
        ``LAUNCH_LENGTH`` past the pad's inner end."""
        return self.board(CENTER_PAD_LENGTH + LAUNCH_LENGTH, 0.0)

    def neck_point(self) -> tuple[float, float]:
        """Where the exit's neck starts, board frame: on the axis
        ``EXIT_NECK_LENGTH`` short of the launch point."""
        return self.board(CENTER_PAD_LENGTH + LAUNCH_LENGTH - EXIT_NECK_LENGTH, 0.0)


# ---------------------------------------------------------------- exit and cutout

LAUNCH_LENGTH = 3.0
"""Straight exit from the centre pad's inner end to the launch point, mm
(``rf_connector_launch.LAUNCH_LENGTH``). The line then runs on, on the same
axis, to the tee or its arm node, so the exit is straight by construction."""

PAD_CUTOUT_WIDTH = 1.6
"""Bottom-ground cutout width under the centre pad, mm
(``rf_connector_launch.PAD_CUTOUT_WIDTH``). That module's value is
illustrative for its own stack; here it is the starting value, unsolved on
this 0.762 mm RO4350B board (open item)."""

CUTOUT_TAPER_LENGTH = 2.5
"""Hyperbolic taper of the cutout from the pad's inner end, mm
(``rf_connector_launch.CUTOUT_TAPER_LENGTH``), shorter than the exit."""

CUTOUT_STEPS = 32
"""Straight segments per side of the taper (``rf_connector_launch``)."""


def cutout_outline(slot_width: float) -> Shape:
    """The bottom-ground cutout in the jack frame: ``PAD_CUTOUT_WIDTH`` wide
    from the board edge to the centre pad's inner end, then the hyperbolic
    taper (``rf_connector_launch.cutout_half_width``) over
    ``CUTOUT_TAPER_LENGTH`` down to ``slot_width``, the line's coplanar slot
    (trace plus a gap each side).

    Raises ``ValueError`` when the cutout would not narrow, would reach the
    ground pads (``GROUND_INNER`` apart) or the taper would run past the
    exit, as the idiom refuses those."""
    if not slot_width < PAD_CUTOUT_WIDTH < GROUND_INNER:
        raise ValueError(
            f"cutout {PAD_CUTOUT_WIDTH} mm must lie between the {slot_width} mm slot "
            f"and the {GROUND_INNER} mm between the ground pads"
        )
    if not 0 < CUTOUT_TAPER_LENGTH <= LAUNCH_LENGTH:
        raise ValueError(f"taper {CUTOUT_TAPER_LENGTH} mm must lie within the exit")
    start, end = PAD_CUTOUT_WIDTH / 2, slot_width / 2
    upper = [(0.0, start)] + [
        (
            CENTER_PAD_LENGTH + CUTOUT_TAPER_LENGTH * i / CUTOUT_STEPS,
            cutout_half_width(
                CUTOUT_TAPER_LENGTH * i / CUTOUT_STEPS, start, end, CUTOUT_TAPER_LENGTH
            ),
        )
        for i in range(CUTOUT_STEPS + 1)
    ]
    lower = [(x, -y) for x, y in reversed(upper)]
    return ShapelyGeometry(shapely.Polygon(upper + lower))


# ---------------------------------------------------------------- ground pads

GROUND_VIA_PITCH = 1.0
"""In-pad ground via pitch along each ground pad, mm: the line fence's pitch
(:py:data:`.lines.FENCE_PITCH`, at most 1.5)."""


def ground_pad_shapes() -> list[Shape]:
    """The two ground pad outlines on one side, jack frame (module land
    pattern: ``GROUND_LENGTH`` from the edge, ``GROUND_PAD_WIDTH`` wide,
    centred ``GROUND_PAD_Y`` off the axis)."""
    w = GROUND_PAD_WIDTH / 2
    return [
        ShapelyGeometry(shapely.box(0.0, y - w, GROUND_LENGTH, y + w))
        for y in (GROUND_PAD_Y, -GROUND_PAD_Y)
    ]


def ground_via_sites(via_pad: float, edge_floor: float) -> list[tuple[float, float]]:
    """In-pad ground via centres, jack frame: one row on each ground pad's
    centreline, ``GROUND_VIA_PITCH`` apart, as many as fit with each via pad
    at least ``edge_floor`` from the board edge (x = 0) and inside the pad's
    far end, centred along the pad so both ends keep the same margin.

    With a 0.45 mm via pad and a 0.22 mm edge floor (0.20 fabrication floor
    plus the 0.02 hold-off): the first centre may sit at 0.445, the last at
    5.0 - 0.225 = 4.775, so 5 vias fit at 1.0 pitch, centred at 0.5 to 4.5.
    """
    first = edge_floor + via_pad / 2
    last = GROUND_LENGTH - via_pad / 2
    count = math.floor((last - first) / GROUND_VIA_PITCH + 1e-9) + 1
    if count < 1:
        raise ValueError("no in-pad via fits the ground pad")
    inset = (GROUND_LENGTH - (count - 1) * GROUND_VIA_PITCH) / 2
    xs = [inset + k * GROUND_VIA_PITCH for k in range(count)]
    return [(round(x, 6), y) for y in (GROUND_PAD_Y, -GROUND_PAD_Y) for x in xs]


# ---------------------------------------------------------------- one jack's launch

IN_PAD_VIA = DiplexerSubstrate.InPadVia
"""The in-pad ground via: the substrate's open via-in-pad class (0.45 pad,
0.30 drill), plated, not filled, capped or tented."""


def launch_point(at: JackPlacement) -> RoutePoint:
    """The control point ending the jack's straight exit, on the pad's axis
    ``LAUNCH_LENGTH`` past its inner end."""
    return RoutePoint(layer=RF_LAYER).at(at.launch_point())


def neck_point(at: JackPlacement) -> RoutePoint:
    """The control point where the exit narrows to its neck, on the pad's
    axis."""
    return RoutePoint(layer=RF_LAYER).at(at.neck_point())


def exit_route(sig: Port, neck: RoutePoint) -> Route:
    """The exit's full-width part, from the centre pad to its neck point: the
    route heads for its destination, which lies on the pad's axis."""
    return Route(sig, neck, layer=RF_LAYER)


def neck_route(neck: RoutePoint, point: RoutePoint) -> Route:
    """The exit's neck between its neck point and the launch point, on the
    axis; ``ExitNeckTag`` gives it :py:func:`.lines.neck_structure`. It is
    drawn from the launch point back to the neck point: its fence then
    starts at the line's end, and on the diplexer every fence step across
    the joints stays within the 1.5 mm fence pitch limit (drawn the other way, one side
    left a 1.64 mm step)."""
    route = Route(point, neck, layer=RF_LAYER)
    ExitNeckTag().assign(route)
    return route


def launch_cutout(at: JackPlacement) -> KeepOut:
    """The bottom ground cut out under the centre pad and the start of the
    exit (``cutout_outline`` to the ``RS_50`` slot): no pour, no generated
    via."""
    slot = 2 * (rs50_half_width() + rs50_gap())
    return KeepOut(
        at.transform * cutout_outline(slot),
        layers=LayerSet(PLANE_LAYER),
        pour=True,
        via=True,
    )


def ground_pad_keepouts(at: JackPlacement) -> list[KeepOut]:
    """No generated via in a top ground pad: the stitch grid's ``StdVia`` is
    not a via-in-pad via, and the shell's ground tabs are soldered there."""
    return [
        KeepOut(at.transform * pad, layers=LayerSet(RF_LAYER), via=True)
        for pad in ground_pad_shapes()
    ]


def in_pad_via_sites(at: JackPlacement) -> list[tuple[float, float]]:
    """The in-pad ground via centres, board frame (``ground_via_sites``), each
    via pad at least the fabrication edge floor plus ``FLOOR_MARGIN`` from
    the edge: the vias keep the 0.20 mm floor, which only the jack's own
    pads are exempt from."""
    if not IN_PAD_VIA.via_in_pad:
        raise ValueError(f"{IN_PAD_VIA.__name__} is not a via-in-pad via")
    floor = DiplexerSubstrate.constraints.min_copper_edge_space + FLOOR_MARGIN
    return [
        at.board(x, y) for x, y in ground_via_sites(float(IN_PAD_VIA.diameter), floor)
    ]


def in_pad_vias(at: JackPlacement) -> list[Via]:
    """Open in-pad vias joining each top ground pad to the bottom one under
    it; the caller joins them to its ground net."""
    return [IN_PAD_VIA().at(x, y) for x, y in in_pad_via_sites(at)]


def in_pad_via_keepoffs(at: JackPlacement) -> list[KeepOut]:
    """Generated vias (stitch grid, fences) keep ``min_hole_to_hole`` from
    the in-pad vias: the stitch grid does not see them."""
    return [
        KeepOut(via_keepoff(xy, IN_PAD_VIA), layers=LayerSet(RF_LAYER), via=True)
        for xy in in_pad_via_sites(at)
    ]

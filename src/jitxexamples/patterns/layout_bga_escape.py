"""Step a power trace down to pass between BGA balls, with the width read
from the balls.

Use this pattern when a power ball sits inside a BGA and a power trace at
the ``PowerTag`` width does not fit between the balls its escape runs past.
On a hex grid at 1.0 mm pitch with 0.5 mm pads, an escape leaving a ball
runs between two neighbouring balls whose pads are 0.5 mm apart. A 0.4 mm
power trace fits in that channel with 0.05 mm to each pad, under the
0.127 mm fab floor of the sample substrate. So the run between the balls is
a separate escape segment at a narrower width.

The mechanism is the one in ``layout_qfn_escape``, on the same priority
ladder (net-tag rules at 2, escape segments at 4):

1. A rule on the net's tag:
   ``design_constraint(PowerTag(), priority=2).trace_width(0.4)``.
2. The net routed as two code routes that meet at a ``RoutePoint`` 1.0 mm
   outside the package's outer balls: the trunk from the source to the
   transition and the escape from the transition to the ball.
3. A rule on a tag assigned to the escape ``Route`` object, at priority 4,
   with the derived width. The trunk keeps the ``PowerTag`` width.

The escape width is derived by :py:func:`derive_escape` from the placed
pads, the substrate's fab constraints and the escape clearance s_e the
caller chose (the clearance that governs the net, or a lower one at or above
``min_copper_copper_space``). It draws the escape's centreline from the ball
centre to the transition and takes c, the smallest distance from that line
to any other pad. A trace of width w on that line clears every other pad by
c - w/2, so ``layout_qfn_escape.escape_width`` keeps w at most 2·(c - s_e),
below the ball's width, rounded down to ``WIDTH_GRID`` (0.01 mm), and at or
above ``min_copper_width``. On this part c is 0.25 mm (half the 1.0 mm
between the flanking ball centres, less the 0.25 mm pad radius). The design
writes no clearance rule, so s_e is the sample substrate's 0.127 mm floor,
and the escape is 0.24 mm, which clears the flanking pads by 0.13 mm.

The part is :py:class:`PlaceholderHexBGA`: a 4 by 3 ball hex grid built from
the ``HexBGA`` landpattern of the ``si_bga_optimization`` demo, at that
demo's 1.0 mm pitch and 0.5 mm ball. The demo's ``GenericHexGridBGA`` ties
every ball that is not a signal to GND, so it has no power ball to escape.
The power ball is at the origin, with its six neighbours 1.0 mm away; it
escapes in -x between the two outer-column balls at (-0.866, +-0.5).

Measured on jitx 4.6, building :py:class:`layout_bga_escape_design`: the
escape realized 0.24 mm wide and the trunk 0.4 mm, the escape's copper came
no closer than 0.13 mm to any other ball pad, and the design's issues listed
routing as satisfied.

The test, ``tests/test_layout_bga_escape.py``, checks the derivation and the
rules offline. With ``JITX_PATTERN_RUNTIME=1`` and a runtime started at the
project root, it builds the design and measures each segment's width and the
escape's distance to the other balls.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import jitx
from jitx import RoutePoint
from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.constraints import Tag, design_constraint
from jitx.inspect import visit
from jitx.landpattern import Landpattern, Pad, PadMapping, PadShape
from jitx.net import Net, Port
from jitx.sample import SampleDesign
from jitx.shapes.shapely import ShapelyGeometry
from jitx.substrate import FabricationConstraints
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry

from jitxexamples.demos.si_bga_optimization.generic_bga import (
    BGA_BALL_DIAMETER,
    BGA_HPITCH,
    HexBGA,
)
from jitxexamples.patterns.layout_qfn_escape import PowerSource, escape_width

POWER_WIDTH = 0.4
"""The power nets' trace width (the ``PowerTag`` width), in mm."""

WIDTH_GRID = Decimal("0.01")
"""The grid the escape width is rounded down to, in mm."""

ESCAPE_RUN = 1.0
"""From the outermost ball pad's edge to the transition, in mm."""

BGA_ROWS = 4
BGA_COLS = 3

POWER_BALL = (1, 2)
"""The power ball's (row, column) in ``HexBGA.get_pad`` terms: row 1 counted
from 0, column 2 counted from 1. It sits at the origin."""

OUTWARD = (-1.0, 0.0)
"""The escape's direction out of the package."""

ARC_TOLERANCE = 1e-4
"""How far a polygonized ball pad may stray from its circle, in mm. The
default of 0.01 mm moves the pad edge by more than the margin this
derivation works to."""


class PowerTag(Tag):
    """Power nets: routed at ``POWER_WIDTH``."""


class BgaEscapeTag(Tag):
    """Escape segments between BGA balls."""


class PlaceholderHexBGA(Component):
    """A placeholder 12-ball hex-grid BGA. Not an orderable part.

    One ball is ``VDD``; the rest are unused.
    """

    manufacturer = "Fictional"
    mpn = "EXAMPLE-HEXBGA12"
    reference_designator_prefix = "U"

    VDD = Port()
    NC = [Port() for _ in range(BGA_ROWS * BGA_COLS - 1)]

    landpattern = (
        HexBGA(
            num_rows=BGA_ROWS,
            num_cols=BGA_COLS,
            pitch=BGA_HPITCH,
            ball_diameter=BGA_BALL_DIAMETER,
        )
        .pad_config(SMDPadConfig())
        .package_body(
            RectanglePackage(
                width=Toleranced.exact(3.0),
                length=Toleranced.exact(4.5),
                height=Toleranced.exact(0.9),
            )
        )
    )
    symbol = BoxSymbol()

    def __init__(self) -> None:
        lp = self.landpattern
        vdd = lp.get_pad(*POWER_BALL)
        others = [p for _, p in visit(lp, Pad) if p is not vdd]
        entries: list[tuple[Port, Pad]] = [(self.VDD, vdd)]
        entries += list(zip(self.NC, others, strict=True))
        self.mappings = [PadMapping(entries)]
        for port in self.NC:
            port.no_connect()


def pad_geometry(pad: Pad) -> BaseGeometry:
    """The pad's copper in its landpattern's frame, circles polygonized to
    ``ARC_TOLERANCE``."""
    shape = pad.shape
    if isinstance(shape, PadShape):
        shape = shape.shape
    assert pad.transform is not None
    return ShapelyGeometry.from_shape(pad.transform * shape, tolerance=ARC_TOLERANCE).g


@dataclass(frozen=True)
class BgaEscape:
    """The derived escape for one ball, in the landpattern's frame."""

    channel_clearance: float
    """c: the smallest distance from the escape's centreline to another pad."""
    escape_clearance: float
    """s_e: the clearance the escape keeps to the other pads."""
    width: float
    ball_center: tuple[float, float]
    transition: tuple[float, float]


def derive_escape(
    landpattern: Landpattern,
    target: Pad,
    outward: tuple[float, float],
    fab: FabricationConstraints,
    *,
    escape_clearance: float,
) -> BgaEscape:
    """Read the pads of ``landpattern`` and derive the escape for ``target``,
    leaving in ``outward`` (an axis direction) to a transition
    ``ESCAPE_RUN`` past the outermost pad edge.

    The width is ``layout_qfn_escape.escape_width`` of the ball's width
    across the escape, c (the smallest distance from the centreline, ball
    centre to transition, to any other pad) and ``escape_clearance``,
    rounded down to ``WIDTH_GRID``. Raises ``ValueError`` as that function
    does.
    """
    shapes = {id(p): pad_geometry(p) for _, p in visit(landpattern, Pad)}
    copper = shapes[id(target)]
    cx, cy = copper.centroid.x, copper.centroid.y
    # The transition sits ESCAPE_RUN past the outermost pad edge.
    minx, miny, maxx, maxy = (
        min(g.bounds[0] for g in shapes.values()),
        min(g.bounds[1] for g in shapes.values()),
        max(g.bounds[2] for g in shapes.values()),
        max(g.bounds[3] for g in shapes.values()),
    )
    dx, dy = outward
    tx = cx if dx == 0 else (minx - ESCAPE_RUN if dx < 0 else maxx + ESCAPE_RUN)
    ty = cy if dy == 0 else (miny - ESCAPE_RUN if dy < 0 else maxy + ESCAPE_RUN)
    centreline = LineString([(cx, cy), (tx, ty)])
    # The polygonized pads stray up to ARC_TOLERANCE from their circles, so c
    # is read to that resolution: 0.249975 on this part is 0.25.
    measured = min(centreline.distance(g) for k, g in shapes.items() if k != id(target))
    clearance = round(measured / ARC_TOLERANCE) * ARC_TOLERANCE
    bminx, bminy, bmaxx, bmaxy = copper.bounds
    across = bmaxy - bminy if dy == 0 else bmaxx - bminx
    return BgaEscape(
        channel_clearance=round(clearance, 6),
        escape_clearance=escape_clearance,
        width=escape_width(
            round(across, 6), clearance, escape_clearance, fab, grid=WIDTH_GRID
        ),
        ball_center=(cx, cy),
        transition=(tx, ty),
    )


class BgaPowerEscape(Circuit):
    """A power source feeding a BGA ball: a trunk at the ``PowerTag`` width
    and a derived escape between the balls."""

    def __init__(self) -> None:
        self.u1 = PlaceholderHexBGA().at(0, 0)
        fab = jitx.current.substrate.constraints
        # The design writes no clearance rule, so the escape keeps the fab
        # floor, the lowest escape clearance the derivation accepts.
        self.escape_geometry = derive_escape(
            self.u1.landpattern,
            self.u1.landpattern.get_pad(*POWER_BALL),
            OUTWARD,
            fab,
            escape_clearance=fab.min_copper_copper_space,
        )
        tx, ty = self.escape_geometry.transition
        self.source = PowerSource().at(tx - 4.0, ty)
        self.transition = RoutePoint(layer=0).at(tx, ty)

        self.vdd = Net([self.source.out, self.u1.VDD], name="VDD")
        self.vdd += self.transition.port
        PowerTag().assign(self.vdd)

        self.trunk = Route(self.source.out, self.transition.pad, layer=0)
        self.escape = Route(self.transition.pad, self.u1.VDD, layer=0)
        BgaEscapeTag().assign(self.escape)

        # Priority ladder: 2 net-tag rules, 4 escape segments.
        self.power_rule = design_constraint(PowerTag(), priority=2).trace_width(
            POWER_WIDTH
        )
        self.escape_rule = design_constraint(BgaEscapeTag(), priority=4).trace_width(
            self.escape_geometry.width
        )


class layout_bga_escape_design(SampleDesign):
    """The BGA power escape on the sample board."""

    circuit = BgaPowerEscape()

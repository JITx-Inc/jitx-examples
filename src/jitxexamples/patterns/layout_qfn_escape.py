"""Step a power trace down to fit a QFN pad, with the width read from the pad.

Use this pattern when a power trace is wider than the pads it reaches.
A 0.8 mm trace centred on a 0.17 mm QFN pad at 0.5 mm pitch reaches
0.4 mm to each side, and the next pads start 0.415 mm from that centre: a
0.015 mm gap, under the 0.127 mm fab floor of the sample substrate. So the
last stretch into the pad is a separate escape segment at a narrower width.

Three pieces compose, on the priority ladder of the layout-constraints
skill (net-tag rules at 2, escape segments at 4):

1. A rule on the net's tag:
   ``design_constraint(PowerTag(), priority=2).trace_width(0.8)``.
2. A transition. The net is routed as two code routes that meet at a
   ``RoutePoint`` 1.0 mm outside the pad: the trunk from the source to the
   transition and the escape from the transition into the pad.
3. A rule on a tag assigned to the escape ``Route`` object, at a higher
   priority: ``design_constraint(QfnEscapeTag(), priority=4)
   .trace_width(escape_width)``. Both rules match the escape segment and the
   higher priority wins there; the trunk keeps the ``PowerTag`` width.

The escape width is derived, not typed. :py:func:`derive_escape` reads the
placed QFN's pad geometry and the substrate's fab constraints, and takes the
escape clearance s_e the caller chose: the clearance that governs the net,
or a lower one at or above ``min_copper_copper_space``. It finds:

- the pad width across the escape direction, and the pad gap: the smallest
  distance from the pad's copper to any other pad's copper. It raises if
  that gap is below ``min_copper_copper_space``;
- c, the smallest distance from the escape's centreline (pad centre to
  transition) to any other pad. The escape leaves along the pad's long
  axis, so c is half the pad width plus the gap to the adjacent pad;
- the escape width, from :py:func:`escape_width`: below the pad width by
  ``ESCAPE_PAD_INSET`` (0.02 mm), at most 2·(c - s_e), rounded down to
  ``WIDTH_GRID`` (0.01 mm), and at or above ``min_copper_width``. Wherever
  the pad gap is at or above s_e, the pad bound decides: a trace narrower
  than the pad and running straight out of it is never closer to a
  neighbouring pad than the pads are to each other.

For this placeholder QFN on :py:class:`jitx.sample.SampleSubstrate`, the
generator's pads come out 0.17 mm wide (0.25 mm leads, density level C), the
gap between pads is 0.33 mm, c is 0.415 mm, and with s_e at the 0.127 mm fab
floor (the design writes no clearance rule) the pad bound gives a 0.15 mm
escape.

Measured on jitx 4.6, building :py:class:`layout_qfn_escape_design`: the
escape realized 0.15 mm wide and the trunk 0.8 mm, the escape's copper came
no closer than 0.34 mm to any of the other 15 QFN pads (0.33 mm between the
pads, plus half the 0.02 mm the escape is narrower than its pad), and the
design's issues listed routing as satisfied.

A ``Route.Config(trace_width=...)`` on the escape would also set its width.
Measured on jitx 4.6, a ``Route.Config`` won over a width rule and a
clearance rule, both at the default priority. That puts a number on one
route, out of reach of those rules; prefer the tag.

The test, ``tests/test_layout_qfn_escape.py``, checks the derivation and the
rules offline. With ``JITX_PATTERN_RUNTIME=1`` and a runtime started at the
project root, it builds the design and measures each segment's width and the
escape's distance to the neighbouring pads.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal

import jitx
from jitx import RoutePoint
from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.constraints import Tag, design_constraint
from jitx.feature import Soldermask
from jitx.inspect import visit
from jitx.landpattern import Landpattern, Pad, PadMapping, PadShape
from jitx.net import Net, Port
from jitx.sample import SampleDesign
from jitx.shapes.composites import rectangle
from jitx.substrate import FabricationConstraints
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.qfn import QFN, QFNLead
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.leads import LeadProfile
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.symbols.box import BoxSymbol
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry

POWER_WIDTH = 0.8
"""The power nets' trace width (the ``PowerTag`` width), in mm."""

ESCAPE_PAD_INSET = Decimal("0.02")
"""How much narrower than the pad the escape is, before rounding, in mm."""

WIDTH_GRID = Decimal("0.01")
"""The grid the escape width is rounded down to, in mm."""

ESCAPE_RUN = 1.0
"""From the pad's outer edge to the transition, in mm."""

QFN_LEADS = 16


class PowerTag(Tag):
    """Power nets: routed at ``POWER_WIDTH``."""


class QfnEscapeTag(Tag):
    """Escape segments into a QFN pad."""


class PlaceholderQfn16(Component):
    """A placeholder 16-lead, 0.5 mm pitch QFN. Not an orderable part.

    Pad 1 is ``VDD``; the rest are unused.
    """

    manufacturer = "Fictional"
    mpn = "EXAMPLE-QFN16"
    reference_designator_prefix = "U"

    VDD = Port()
    NC = [Port() for _ in range(QFN_LEADS - 1)]

    landpattern = (
        QFN(num_leads=QFN_LEADS)
        .lead_profile(
            LeadProfile(
                span=Toleranced.exact(3.0),
                pitch=0.5,
                type=QFNLead(
                    length=Toleranced.exact(0.4), width=Toleranced.exact(0.25)
                ),
            )
        )
        .package_body(
            RectanglePackage(
                width=Toleranced.exact(3.0),
                length=Toleranced.exact(3.0),
                height=Toleranced.exact(0.9),
            )
        )
        .density_level(DensityLevel.C)
    )
    symbol = BoxSymbol()

    def __init__(self) -> None:
        pads = self.landpattern.p
        entries: list[tuple[Port, Pad]] = [(self.VDD, pads[1])]
        entries += [(port, pads[i]) for i, port in enumerate(self.NC, start=2)]
        self.mappings = [PadMapping(entries)]
        for port in self.NC:
            port.no_connect()


class SourcePad(Pad):
    shape = rectangle(1.0, 1.0)
    soldermask = Soldermask(rectangle(1.1, 1.1))


class SourceLandpattern(Landpattern):
    pad = SourcePad().at(0, 0)


class PowerSource(Component):
    """A fictional one-pin power source. Not a real product."""

    manufacturer = "Fictional"
    mpn = "EXAMPLE-PWR-PAD"
    reference_designator_prefix = "J"

    out = Port()
    landpattern = SourceLandpattern()
    symbol = BoxSymbol()

    def __init__(self) -> None:
        self.mappings = [PadMapping({self.out: self.landpattern.pad})]


def pad_geometry(pad: Pad) -> BaseGeometry:
    """The pad's copper in its landpattern's frame."""
    shape = pad.shape
    if isinstance(shape, PadShape):
        shape = shape.shape
    assert pad.transform is not None
    return (pad.transform * shape).to_shapely().g


@dataclass(frozen=True)
class Escape:
    """The derived escape for one QFN pad, in the landpattern's frame."""

    pad_width: float
    pad_gap: float
    centreline_clearance: float
    """c: the smallest distance from the escape's centreline to another pad."""
    escape_clearance: float
    """s_e: the clearance the escape keeps to the other pads."""
    width: float
    pad_center: tuple[float, float]
    outward: tuple[float, float]
    transition: tuple[float, float]


def strictly_inside_width(pad_width: float, floor: float) -> float:
    """``pad_width`` less the inset, rounded down to the grid; checked
    against the pad and the fab floor."""
    steps = (Decimal(str(pad_width)) - ESCAPE_PAD_INSET) / WIDTH_GRID
    width = float(steps.to_integral_value(rounding=ROUND_FLOOR) * WIDTH_GRID)
    if not width < pad_width:
        raise ValueError(f"escape {width} is not narrower than the {pad_width} pad")
    if width < floor:
        raise ValueError(f"escape {width} is below the fab floor {floor}")
    return width


def escape_width(
    pad_width: float,
    centreline_clearance: float,
    escape_clearance: float,
    fab: FabricationConstraints,
    *,
    grid: Decimal = WIDTH_GRID,
) -> float:
    """The width of an escape segment that leaves a pad past other pads.

    ``pad_width`` is the narrowest pad the escape rule selects, measured
    across the escape; ``centreline_clearance`` is c, the smallest distance
    from the escape's centreline (pad centre to transition) to any other
    pad; ``escape_clearance`` is s_e, the clearance the escape keeps, either
    the clearance that governs the net or a lower one at or above the fab's
    ``min_copper_copper_space``. The width is:

    - strictly below ``pad_width``, by ``ESCAPE_PAD_INSET`` before rounding;
    - at most ``2 * (c - s_e)``, so the escape's edge keeps s_e from every
      other pad;
    - rounded down to ``grid``, and at or above ``min_copper_width``.

    Raises ``ValueError`` when ``escape_clearance`` is below
    ``min_copper_copper_space`` or the width that results is below
    ``min_copper_width``. On a BGA at 1.0 pitch with 0.5 balls, the channel
    between the balls is 0.5 and c 0.25, so the escape is 0.3 at s_e 0.1 and
    0.26 at s_e 0.12.
    """
    if escape_clearance < fab.min_copper_copper_space:
        raise ValueError(
            f"escape clearance {escape_clearance} is below min_copper_copper_space "
            f"{fab.min_copper_copper_space}"
        )

    def exact(value: float) -> Decimal:
        return Decimal(str(round(value, 6)))

    by_pad = exact(pad_width) - ESCAPE_PAD_INSET
    by_neighbours = 2 * (exact(centreline_clearance) - exact(escape_clearance))
    steps = min(by_pad, by_neighbours) / grid
    width = float(steps.to_integral_value(rounding=ROUND_FLOOR) * grid)
    if not width < pad_width:
        raise ValueError(f"escape {width} is not narrower than the {pad_width} pad")
    if width < fab.min_copper_width:
        raise ValueError(
            f"escape {width} is below min_copper_width {fab.min_copper_width}: the "
            f"pad is {pad_width} wide and the nearest other pad {centreline_clearance} "
            f"from the escape's centreline"
        )
    return width


def derive_escape(
    landpattern: Landpattern,
    target: Pad,
    fab: FabricationConstraints,
    *,
    escape_clearance: float,
) -> Escape:
    """Read the pads of ``landpattern`` and derive the escape for ``target``.

    The escape leaves along the pad's long axis, away from the body centre,
    to a transition ``ESCAPE_RUN`` past the pad's outer edge. Its width is
    :py:func:`escape_width` of the pad width across that axis, c (the
    smallest distance from the centreline to another pad) and
    ``escape_clearance``. Raises ``ValueError`` if two pads sit closer than
    ``min_copper_copper_space``, or as :py:func:`escape_width` does.
    """
    pads = [p for _, p in visit(landpattern, Pad)]
    shapes = {id(p): pad_geometry(p) for p in pads}
    copper = shapes[id(target)]
    cx, cy = copper.centroid.x, copper.centroid.y
    minx, miny, maxx, maxy = copper.bounds
    along_x = (maxx - minx) > (maxy - miny)
    if along_x:
        outward = (-1.0 if cx < 0 else 1.0, 0.0)
        pad_width, depth = maxy - miny, maxx - minx
    else:
        outward = (0.0, -1.0 if cy < 0 else 1.0)
        pad_width, depth = maxx - minx, maxy - miny
    others = [g for k, g in shapes.items() if k != id(target)]
    gap = min(copper.distance(g) for g in others)
    if gap < fab.min_copper_copper_space:
        raise ValueError(f"pads {gap} apart, under the fab floor")
    run = depth / 2 + ESCAPE_RUN
    transition = (cx + outward[0] * run, cy + outward[1] * run)
    centreline = LineString([(cx, cy), transition])
    c = min(centreline.distance(g) for g in others)
    return Escape(
        pad_width=round(pad_width, 6),
        pad_gap=round(gap, 6),
        centreline_clearance=round(c, 6),
        escape_clearance=escape_clearance,
        width=escape_width(round(pad_width, 6), c, escape_clearance, fab),
        pad_center=(cx, cy),
        outward=outward,
        transition=transition,
    )


class QfnPowerEscape(Circuit):
    """A power source feeding the QFN's VDD pad: a trunk at the ``PowerTag``
    width and a derived escape."""

    def __init__(self) -> None:
        self.u1 = PlaceholderQfn16().at(0, 0)
        target = self.u1.landpattern.p[1]
        fab = jitx.current.substrate.constraints
        # The design writes no clearance rule, so the escape keeps the fab
        # floor, the lowest escape clearance the derivation accepts.
        self.escape_geometry = derive_escape(
            self.u1.landpattern,
            target,
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
        QfnEscapeTag().assign(self.escape)

        # Priority ladder: 2 net-tag rules, 4 escape segments.
        self.power_rule = design_constraint(PowerTag(), priority=2).trace_width(
            POWER_WIDTH
        )
        self.escape_rule = design_constraint(QfnEscapeTag(), priority=4).trace_width(
            self.escape_geometry.width
        )


class layout_qfn_escape_design(SampleDesign):
    """The QFN power escape on the sample board."""

    circuit = QfnPowerEscape()

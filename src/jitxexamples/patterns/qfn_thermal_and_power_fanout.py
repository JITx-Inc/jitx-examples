"""Thermal vias in a QFN's exposed pad, and power pins fanned out to a plane.

The part is the RP2040 from ``jitxexamples.components.mcus``: a 56-lead,
0.4 mm pitch QFN whose 3.1 mm square exposed pad is its only ground pin.
The board is a 4-layer substrate: parts and fanout on layer 0, a ground
plane on layer 1 and a 3.3 V plane on layer 2.

Thermal vias
------------

:py:func:`thermal_via_grid` places the largest grid of vias that fits the
exposed pad with its vias at least ``THERMAL_VIA_PITCH`` (1.1 mm) apart and
each via pad's rim ``edge_margin`` inside the pad's copper. The default
margin is the substrate's ``min_soldermask_bridge`` plus its
``solder_mask_registration``: each via is tented by a soldermask dam that
reaches ``solder_mask_registration`` past its pad, so the dam ends one mask
bridge inside the pad edge and meets the mask frame there. On the RP2040's
pad with this substrate's ``ThermalVia``, that is a 2 by 2 grid at a
2.036 mm pitch.

``ThermalVia`` is the smallest via on the substrate's floors: a 0.254 mm
drill, the ``min_drill_diameter``, in a 0.56 mm pad, which leaves a
0.153 mm annular ring against the 0.1524 mm ``min_annular_ring``. The
smallest via leaves the most of the pad open for paste.

The function refuses a via class whose ``via_in_pad`` is ``False`` and a
pitch below ``min_stitch_pitch`` (the larger of one via pad and one drill
plus ``min_hole_to_hole``). JITX accepts a via inside a pad whose via class
disallows it without raising a design issue, so the check lives here.
``ThermalVia`` sits inside a pad, so it declares ``via_in_pad = True``;
confirm with your fabricator that tented, unfilled vias inside a pad are
accepted.

:py:func:`thermal_pad_opening` builds the soldermask and paste opening: the
pad less a frame one mask bridge wide, a web one mask bridge wide along each
row and column of vias, and a dam around each via, with every corner of what
is left rounded to half of ``min_soldermask_opening``. The rounding drops
any part of a cell narrower than ``min_soldermask_opening``: here the four
corner cells, where each via's dam meets the frame, so 5 cells remain. The
same shape is the pad's soldermask and its paste
(:py:func:`thermal_pad_config`), so solder lands only in those cells and
cannot wick down an open via barrel. ``StitchedRP2040`` passes that config
to the landpattern's ``thermal_pad`` before the RP2040 maps its pads, and
the circuit places a ``ThermalVia`` at each grid position on the ground net.

The paste covers 5.32 of the pad's 9.61 square millimetres, 55 percent,
where the unstitched RP2040 pastes the whole pad. Check that against your
assembler's stencil guidance for an exposed pad. The pitch sets the
tradeoff: a larger ``THERMAL_VIA_PITCH`` gives fewer vias, so fewer paths
for heat into the planes, and more paste; a smaller one gives the
reverse.

Power fanout
------------

The six ``IOVDD`` pins fan out to the 3.3 V plane, each through three pieces
of copper, on the rules ``layout_qfn_escape`` teaches:

1. An escape from the pad to a ``RoutePoint`` 1.0 mm past the pad's outer
   edge. Its width is :py:func:`~jitxexamples.patterns.layout_qfn_escape.derive_escape`
   read from the landpattern: 0.13 mm on these 0.15 mm pads, narrower than
   the pad so it never comes closer to a neighbouring pad than the pads are
   to each other. A ``QfnEscapeTag`` on each escape ``Route`` and a
   priority-4 rule on that tag set the width.
2. A trunk from the ``RoutePoint`` to a fanout via, at ``POWER_WIDTH``
   (0.8 mm) from the priority-2 rule on the net's ``PowerTag``. Both rules
   match the escape, and the higher priority wins there.
3. The fanout via, a ``PowerVia`` with a 1.0 mm pad, wider than the trunk,
   through every layer. On layer 2 it sits inside the 3.3 V pour and joins
   it.

The fanout vias are where a designer would choose to drop to the plane, so
:py:func:`designer_placed_fanout_points` returns them in a function of its
own: a designer would place them in the physical design view instead, and
they are written here so the example is complete.

Each plane is held by vias of its own net inside it, the thermal vias for
the ground plane and the fanout vias for the 3.3 V plane. A pour with no pad
or via of its own net inside it comes back empty.

All copper and mask stay at or above the substrate's
``FabricationConstraints``: the escapes are 0.13 mm against a 0.127 mm
``min_copper_width``, both via classes meet ``min_drill_diameter`` and
``min_annular_ring``, the thermal via drills sit 1.782 mm apart against a
0.254 mm ``min_hole_to_hole``, every mask web is ``min_soldermask_bridge``
wide, and every part of the opening is at least ``min_soldermask_opening``
across.

The test, ``tests/test_qfn_thermal_and_power_fanout.py``, checks the grid,
the opening and the escape width offline. With ``JITX_PATTERN_RUNTIME=1``
and a runtime started at the project root, it builds the design and measures
the realized escapes, trunks and planes.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import jitx
import shapely
from jitx.circuit import Circuit, Route
from jitx.constraints import design_constraint
from jitx.controlpoint import RoutePoint
from jitx.copper import Pour
from jitx.design import Design
from jitx.landpattern import Pad, PadShape
from jitx.net import Net
from jitx.sample import SampleBoard, SampleFabConstraints, SampleStackup
from jitx.shapes import Shape
from jitx.shapes.composites import rectangle
from jitx.shapes.shapely import ShapelyGeometry
from jitx.substrate import FabricationConstraints, Substrate
from jitx.via import Via, ViaDiameter, ViaType
from jitxlib.landpatterns.pads import SMDPadConfig
from shapely.geometry.base import BaseGeometry

from jitxexamples.components.mcus.raspberry_pi_RP2040 import RP2040Component
from jitxexamples.patterns.layout_qfn_escape import (
    POWER_WIDTH,
    Escape,
    PowerTag,
    QfnEscapeTag,
    derive_escape,
    pad_geometry,
)
from jitxexamples.patterns.layout_stitched_pour import min_stitch_pitch

THERMAL_VIA_PITCH = 1.1
"""The smallest centre-to-centre spacing of the thermal vias, in mm."""

FANOUT_RUN = 1.5
"""From an escape's ``RoutePoint`` to its fanout via's centre, in mm."""

GROUND_PLANE_LAYER = 1
"""The ground plane's layer, under the parts."""

POWER_PLANE_LAYER = 2
"""The 3.3 V plane's layer."""

PLANE = rectangle(16.0, 16.0)
"""The outline of both planes, centred on the RP2040, in mm."""

DAM_SEGMENTS = 24
"""Segments per quarter circle of each via's mask dam and corner rounding."""


class FanoutSubstrate(Substrate):
    """Four copper layers with the sample fabrication constraints, a via
    allowed inside a pad, and a power via."""

    stackup = SampleStackup(4)
    constraints = SampleFabConstraints()

    class ThermalVia(Via):
        """A through via allowed inside a pad: 0.56 mm pad, 0.254 mm drill."""

        start_layer = 0
        stop_layer = -1
        diameter = 0.56
        hole_diameter = 0.254
        type = ViaType.MechanicalDrill
        via_in_pad = True

    class PowerVia(Via):
        """A through via for the fanout: 1.0 mm pad, 0.5 mm drill."""

        start_layer = 0
        stop_layer = -1
        diameter = 1.0
        hole_diameter = 0.5
        type = ViaType.MechanicalDrill


def via_pad_diameter(via: type[Via]) -> float:
    """The via's pad diameter, from a plain diameter or a ``ViaDiameter``."""
    diameter = via.diameter
    if isinstance(diameter, ViaDiameter):
        return float(diameter.pad)
    return float(diameter)


def default_edge_margin(fab: FabricationConstraints) -> float:
    """Via pad rim to exposed-pad edge: one mask bridge plus the mask
    registration, so each via's dam ends one bridge inside the pad edge."""
    return fab.min_soldermask_bridge + fab.solder_mask_registration


def thermal_via_grid(
    pad_size: tuple[float, float],
    via: type[Via],
    fab: FabricationConstraints,
    *,
    pitch: float,
    edge_margin: float | None = None,
) -> list[tuple[float, float]]:
    """Thermal via centres for an exposed pad, in the pad's own frame.

    Along each axis the grid holds as many vias as fit with centres at least
    ``pitch`` apart and each via pad's rim ``edge_margin`` inside the pad
    edge (:py:func:`default_edge_margin` when ``None``), spread evenly over
    that span and centred on the pad. Rows run along x, bottom row first.

    Raises ``ValueError`` when ``via`` does not allow a via in a pad (JITX
    does not report one), when ``pitch`` is below
    :py:func:`~jitxexamples.patterns.layout_stitched_pour.min_stitch_pitch`,
    and when the pad has no room for one via.
    """
    if not via.via_in_pad:
        raise ValueError(
            f"{via.__name__} has via_in_pad = False; declare a via class that "
            f"allows a via in a pad, and confirm it with the fabricator"
        )
    floor = min_stitch_pitch(via, fab)
    if pitch < floor:
        raise ValueError(
            f"thermal via pitch {pitch} mm is below {floor:.3f} mm, the larger of "
            f"one {via.__name__} pad and its drill plus min_hole_to_hole"
        )
    margin = default_edge_margin(fab) if edge_margin is None else edge_margin
    inset = margin + via_pad_diameter(via) / 2

    def axis(extent: float) -> list[float]:
        span = extent - 2 * inset
        if span < 0:
            raise ValueError(
                f"exposed pad side {extent} mm is too small for a via with its "
                f"centre {inset} mm in from each edge"
            )
        count = math.floor(span / pitch + 1e-9) + 1
        if count == 1:
            return [0.0]
        step = span / (count - 1)
        return [-span / 2 + i * step for i in range(count)]

    xs = axis(pad_size[0])
    ys = axis(pad_size[1])
    return [(x, y) for y in ys for x in xs]


def thermal_pad_opening(
    pad_size: tuple[float, float],
    positions: Sequence[tuple[float, float]],
    via: type[Via],
    fab: FabricationConstraints,
) -> Shape:
    """The soldermask and paste opening of a stitched exposed pad.

    The pad, in its own frame, less a frame ``min_soldermask_bridge`` wide
    along its edge, a web of the same width along each row and column of
    ``positions``, and a dam around each via that reaches
    ``solder_mask_registration`` past its pad. Every corner of what is left
    is rounded to half of ``min_soldermask_opening``, which drops any part
    narrower than ``min_soldermask_opening``. Raises ``ValueError`` when
    nothing of the pad is left open.
    """
    w, h = pad_size
    bridge = fab.min_soldermask_bridge
    pad = shapely.box(-w / 2, -h / 2, w / 2, h / 2)
    mask: list[BaseGeometry] = [
        pad.difference(
            shapely.box(
                -w / 2 + bridge, -h / 2 + bridge, w / 2 - bridge, h / 2 - bridge
            )
        )
    ]
    for x in sorted({round(x, 6) for x, _ in positions}):
        mask.append(shapely.box(x - bridge / 2, -h / 2, x + bridge / 2, h / 2))
    for y in sorted({round(y, 6) for _, y in positions}):
        mask.append(shapely.box(-w / 2, y - bridge / 2, w / 2, y + bridge / 2))
    dam = via_pad_diameter(via) / 2 + fab.solder_mask_registration
    for x, y in positions:
        mask.append(shapely.Point(x, y).buffer(dam, quad_segs=DAM_SEGMENTS))
    rounding = fab.min_soldermask_opening / 2
    opening = (
        pad.difference(shapely.union_all(mask))
        .buffer(-rounding, quad_segs=DAM_SEGMENTS)
        .buffer(rounding, quad_segs=DAM_SEGMENTS)
    )
    if opening.is_empty or opening.geom_type not in ("Polygon", "MultiPolygon"):
        raise ValueError(f"no opening is left on the {w} x {h} mm pad")
    return ShapelyGeometry(opening)


def thermal_pad_config(
    pad_size: tuple[float, float],
    positions: Sequence[tuple[float, float]],
    via: type[Via],
    fab: FabricationConstraints,
) -> SMDPadConfig:
    """An ``SMDPadConfig`` whose soldermask and paste are both
    :py:func:`thermal_pad_opening`."""
    opening = thermal_pad_opening(pad_size, positions, via, fab)
    return SMDPadConfig(soldermask=opening, paste=opening)


def pad_bounds(pad: Pad) -> tuple[float, float, float, float]:
    """The pad copper's bounds in its landpattern's frame."""
    minx, miny, maxx, maxy = pad_geometry(pad).bounds
    return float(minx), float(miny), float(maxx), float(maxy)


class StitchedRP2040(RP2040Component):
    """The RP2040 with thermal vias in its exposed pad.

    ``thermal_via_positions`` are the via centres in the landpattern's frame;
    the circuit that places the part places a via at each.
    """

    def __init__(
        self, via: type[Via], fab: FabricationConstraints, pitch: float
    ) -> None:
        landpattern = self.landpattern
        (exposed,) = landpattern.thermal_pads
        minx, miny, maxx, maxy = pad_bounds(exposed)
        size = (maxx - minx, maxy - miny)
        cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
        grid = thermal_via_grid(size, via, fab, pitch=pitch)
        self.thermal_via_positions = [(cx + x, cy + y) for x, y in grid]
        shape = exposed.shape
        if isinstance(shape, PadShape):
            shape = shape.shape
        landpattern.thermal_pad(shape, config=thermal_pad_config(size, grid, via, fab))
        super().__init__()


def designer_placed_fanout_points(
    escapes: Sequence[Escape],
) -> list[tuple[float, float]]:
    """Where each power pin's trunk drops to the plane: one fanout via per
    escape, ``FANOUT_RUN`` straight out past its ``RoutePoint``.

    A designer would place these interactively, where the board has room
    for each via; they are written here so the example is complete.
    """
    return [
        (
            e.transition[0] + e.outward[0] * FANOUT_RUN,
            e.transition[1] + e.outward[1] * FANOUT_RUN,
        )
        for e in escapes
    ]


class QfnThermalAndPowerFanout(Circuit):
    """The stitched RP2040, its ground plane, and its six ``IOVDD`` pins fanned
    out to the 3.3 V plane."""

    def __init__(self) -> None:
        fab = jitx.current.substrate.constraints
        thermal_via = FanoutSubstrate.ThermalVia
        self.u1 = StitchedRP2040(thermal_via, fab, THERMAL_VIA_PITCH).at(0, 0)

        self.GND = Net([self.u1.GND], name="GND")
        self.thermal_vias = [
            thermal_via().at(x, y) for x, y in self.u1.thermal_via_positions
        ]
        for via in self.thermal_vias:
            self.GND += via
        self.ground_plane = Pour(PLANE, layer=GROUND_PLANE_LAYER)
        self.GND += self.ground_plane

        self.P3V3 = Net(name="3V3")
        PowerTag().assign(self.P3V3)
        (mapping,) = self.u1.mappings
        pads: list[Pad] = []
        for port in self.u1.IOVDD:
            pad = mapping[port]
            if not isinstance(pad, Pad):
                (pad,) = pad
            pads.append(pad)
        # The design writes no clearance rule, so the escapes keep the fab
        # floor, the lowest escape clearance the derivation accepts.
        self.escapes = [
            derive_escape(
                self.u1.landpattern,
                pad,
                fab,
                escape_clearance=fab.min_copper_copper_space,
            )
            for pad in pads
        ]
        fanout_points = designer_placed_fanout_points(self.escapes)

        self.transitions: list[RoutePoint] = []
        self.fanout_vias: list[FanoutSubstrate.PowerVia] = []
        self.escape_routes: list[Route] = []
        self.trunks: list[Route] = []
        for port, escape, point in zip(
            self.u1.IOVDD, self.escapes, fanout_points, strict=True
        ):
            transition = RoutePoint(layer=0).at(*escape.transition)
            via = FanoutSubstrate.PowerVia().at(*point)
            self.P3V3 += port
            self.P3V3 += transition.port
            self.P3V3 += via
            route = Route(transition.pad, port, layer=0)
            QfnEscapeTag().assign(route)
            self.transitions.append(transition)
            self.fanout_vias.append(via)
            self.escape_routes.append(route)
            self.trunks.append(Route(transition.pad, via, layer=0))
        self.power_plane = Pour(PLANE, layer=POWER_PLANE_LAYER)
        self.P3V3 += self.power_plane

        # Priority ladder: 2 net-tag rules, 4 escape segments. The narrowest
        # pad the escape rule selects sets its width.
        self.power_rule = design_constraint(PowerTag(), priority=2).trace_width(
            POWER_WIDTH
        )
        self.escape_rule = design_constraint(QfnEscapeTag(), priority=4).trace_width(
            min(e.width for e in self.escapes)
        )


class qfn_thermal_and_power_fanout_design(Design):
    """The stitched, fanned-out RP2040 on the 4-layer substrate."""

    board = SampleBoard()
    substrate = FanoutSubstrate()
    circuit = QfnThermalAndPowerFanout()

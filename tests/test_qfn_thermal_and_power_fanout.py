"""Tests for the QFN thermal via and power fanout pattern.

Expected values are worked out here from what the tests read: the RP2040's
exposed pad and IOVDD pads from its landpattern, the via pads and drills
from the substrate's via classes, and the mask and drill floors from the
substrate's fabrication constraints. The grid's edge margin is the one the
mask geometry needs: a dam reaching ``solder_mask_registration`` past a via
pad ends one ``min_soldermask_bridge`` inside the pad edge, where the mask
frame starts.

The runtime tests submit the design, capture it and measure the realized
escapes, trunks and planes. They need a JITX runtime started from the
repository root and ``JITX_PATTERN_RUNTIME=1``.
"""

from __future__ import annotations

import math
import os
import shutil
import unittest
from pathlib import Path
from typing import ClassVar

import jitx
import shapely
from jitx.circuit import Route
from jitx.feature import Paste, Soldermask
from jitx.inspect import visit
from jitx.landpattern import Pad, PadShape
from jitx.sample import SampleSubstrate
from jitx.shapes import Shape
from jitx.shapes.primitive import ArcPolyline, Empty
from jitx.substrate import FabricationConstraints
from jitx.test import TestCase
from jitx.transform import Transform
from jitx.via import Via
from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry

from jitxexamples.patterns.layout_qfn_escape import POWER_WIDTH
from jitxexamples.patterns.qfn_thermal_and_power_fanout import (
    THERMAL_VIA_PITCH,
    FanoutSubstrate,
    QfnThermalAndPowerFanout,
    qfn_thermal_and_power_fanout_design,
    thermal_via_grid,
)

RUNTIME = os.environ.get("JITX_PATTERN_RUNTIME") == "1"


def _pad_copper(pad: Pad, frame: Transform | None = None) -> BaseGeometry:
    """The pad's copper in its landpattern's frame, or in ``frame`` above it."""
    shape = pad.shape
    if isinstance(shape, PadShape):
        shape = shape.shape
    assert pad.transform is not None
    placed = pad.transform * shape
    return (placed if frame is None else frame * placed).to_shapely().g


def _xy(obj: Via) -> tuple[float, float]:
    assert obj.transform is not None
    x, y = obj.transform.translation
    return float(x), float(y)


def _radius(via: type[Via]) -> float:
    diameter = via.diameter
    assert isinstance(diameter, float)
    return diameter / 2


def _feature(pad: Pad, kind: type[Soldermask] | type[Paste]) -> BaseGeometry:
    ((_, feature),) = list(visit(pad, kind))
    return feature.shape.to_shapely().g


def _iovdd_pads(c: QfnThermalAndPowerFanout) -> list[Pad]:
    (mapping,) = c.u1.mappings
    pads: list[Pad] = []
    for port in c.u1.IOVDD:
        pad = mapping[port]
        if not isinstance(pad, Pad):
            (pad,) = pad
        pads.append(pad)
    return pads


class _DrillBoundVia(FanoutSubstrate.ThermalVia):
    """A via that exists only to make the drill term of the pitch floor
    bind: its drill plus ``min_hole_to_hole``, 0.4 mm + 0.254 mm = 0.654 mm,
    is larger than its 0.6 mm pad. Its 0.1 mm annular ring is under the
    sample fab's ``min_annular_ring``, so it is not a via to build."""

    diameter = 0.6
    hole_diameter = 0.4


class TestQfnThermalAndPowerFanout(TestCase):
    def setUp(self) -> None:
        design = qfn_thermal_and_power_fanout_design()
        circuit = design.circuit
        assert isinstance(circuit, QfnThermalAndPowerFanout)
        self.c = circuit
        self.fab: FabricationConstraints = design.substrate.constraints
        (self.exposed,) = circuit.u1.landpattern.thermal_pads
        self.copper = _pad_copper(self.exposed)
        self.via = FanoutSubstrate.ThermalVia
        self.r = _radius(self.via)
        self.margin = self.fab.min_soldermask_bridge + self.fab.solder_mask_registration

    def test_thermal_vias_fill_the_largest_grid_the_pad_holds(self) -> None:
        # Along each side, n vias fit when (n - 1) pitches fit the span
        # between the outermost centres and n pitches do not, and the
        # outermost via pads sit exactly the margin inside the pad edge.
        minx, miny, maxx, maxy = self.copper.bounds
        inset = self.margin + self.r
        placed = [(round(x, 6), round(y, 6)) for x, y in map(_xy, self.c.thermal_vias)]
        for lo, hi, coords in (
            (minx, maxx, sorted({x for x, _ in placed})),
            (miny, maxy, sorted({y for _, y in placed})),
        ):
            span = hi - lo - 2 * inset
            n = len(coords)
            self.assertLessEqual((n - 1) * THERMAL_VIA_PITCH, span + 1e-6)
            self.assertLess(span, n * THERMAL_VIA_PITCH)
            self.assertAlmostEqual(coords[0] - self.r - lo, self.margin, places=5)
            self.assertAlmostEqual(hi - (coords[-1] + self.r), self.margin, places=5)
        self.assertEqual(
            len(placed), len({x for x, _ in placed}) * len({y for _, y in placed})
        )
        inside = self.copper.buffer(-self.margin + 1e-6)
        for x, y in placed:
            self.assertTrue(inside.contains(Point(x, y).buffer(self.r)))
        gaps = [math.dist(a, b) for i, a in enumerate(placed) for b in placed[i + 1 :]]
        self.assertGreaterEqual(min(gaps), THERMAL_VIA_PITCH)
        drill = self.via.hole_diameter
        self.assertGreaterEqual(min(gaps) - drill, self.fab.min_hole_to_hole)

    def test_thermal_vias_are_on_the_exposed_pads_net(self) -> None:
        members = list(self.c.GND.connected)
        for via in self.c.thermal_vias:
            self.assertIn(via, members)

    def test_mask_and_paste_are_one_opening_with_a_dam_on_every_via(self) -> None:
        mask = _feature(self.exposed, Soldermask)
        paste = _feature(self.exposed, Paste)
        self.assertLess(mask.symmetric_difference(paste).area, 1e-9)
        # Inside the copper by one mask bridge: the frame.
        self.assertTrue(
            self.copper.buffer(-self.fab.min_soldermask_bridge + 1e-6).contains(mask)
        )
        # A web one mask bridge wide runs along each row and column of vias,
        # across the whole pad.
        placed = [_xy(v) for v in self.c.thermal_vias]
        minx, miny, maxx, maxy = self.copper.bounds
        half = self.fab.min_soldermask_bridge / 2
        for x in {round(x, 6) for x, _ in placed}:
            line = LineString([(x, miny), (x, maxy)])
            self.assertGreaterEqual(mask.distance(line), half - 1e-6)
        for y in {round(y, 6) for _, y in placed}:
            line = LineString([(minx, y), (maxx, y)])
            self.assertGreaterEqual(mask.distance(line), half - 1e-6)
        # Every via is under a dam that reaches the mask registration past
        # its pad; the dam is a polygonized circle, so allow 0.001 mm.
        dam = self.r + self.fab.solder_mask_registration
        for x, y in placed:
            self.assertGreaterEqual(mask.distance(Point(x, y)), dam - 1e-3)

    def test_every_opening_is_at_least_the_minimum_soldermask_opening(self) -> None:
        # A part of the opening narrower than min_soldermask_opening is lost
        # to an opening (shrink, then grow) at half that width. Both arcs are
        # polygonized, so allow 0.001 mm2.
        mask = _feature(self.exposed, Soldermask)
        half = self.fab.min_soldermask_opening / 2
        opened = mask.buffer(-half, quad_segs=64).buffer(half, quad_segs=64)
        self.assertLess(mask.difference(opened).area, 1e-3)

    def test_every_via_class_meets_the_drill_and_annular_ring_floors(self) -> None:
        for via in (FanoutSubstrate.ThermalVia, FanoutSubstrate.PowerVia):
            with self.subTest(via=via.__name__):
                diameter = via.diameter
                assert isinstance(diameter, float)
                ring = (diameter - via.hole_diameter) / 2
                self.assertGreaterEqual(via.hole_diameter, self.fab.min_drill_diameter)
                self.assertGreaterEqual(ring, self.fab.min_annular_ring)

    def test_refuses_an_exposed_pad_too_small_for_one_via(self) -> None:
        side = 2 * (self.margin + self.r) - 0.01
        with self.assertRaisesRegex(ValueError, "too small"):
            thermal_via_grid((side, side), self.via, self.fab, pitch=THERMAL_VIA_PITCH)

    def test_refuses_a_via_class_that_disallows_a_via_in_a_pad(self) -> None:
        with self.assertRaisesRegex(ValueError, "via_in_pad = False"):
            thermal_via_grid(
                (3.1, 3.1), SampleSubstrate.THVia, self.fab, pitch=THERMAL_VIA_PITCH
            )

    def test_refuses_a_pitch_that_puts_drills_under_the_hole_floor(self) -> None:
        # A pitch between the pad and the drill floor: only the drill floor
        # refuses it.
        via = _DrillBoundVia
        drill_floor = via.hole_diameter + self.fab.min_hole_to_hole
        pitch = (_radius(via) * 2 + drill_floor) / 2
        self.assertGreater(pitch, _radius(via) * 2)
        with self.assertRaisesRegex(ValueError, f"is below {drill_floor:.3f}"):
            thermal_via_grid((3.1, 3.1), via, self.fab, pitch=pitch)

    def test_escape_is_narrower_than_every_iovdd_pad_and_above_the_floor(self) -> None:
        width = self.c.escape_rule.trace_width_constraint
        assert width is not None
        for pad in _iovdd_pads(self.c):
            minx, miny, maxx, maxy = _pad_copper(pad).bounds
            self.assertLess(width.width, min(maxx - minx, maxy - miny))
        self.assertGreaterEqual(width.width, self.fab.min_copper_width)
        self.assertGreater(self.c.escape_rule.priority, self.c.power_rule.priority)

    def test_each_fanout_via_lands_inside_the_power_plane(self) -> None:
        plane = self.c.power_plane.shape.to_shapely().g
        r = _radius(FanoutSubstrate.PowerVia)
        for via in self.c.fanout_vias:
            self.assertTrue(plane.contains(Point(_xy(via)).buffer(r)))
        ground = self.c.ground_plane.shape.to_shapely().g
        for via in self.c.thermal_vias:
            self.assertTrue(ground.contains(Point(_xy(via)).buffer(self.r)))


def _copper(route: Route) -> BaseGeometry:
    return shapely.union_all(
        [s.to_shapely().g for t in route.traces or [] for s in t.shapes]
    )


def _widths(route: Route) -> set[float]:
    widths: set[float] = set()
    for trace in route.traces or []:
        for shape in trace.shapes:
            geometry = shape.geometry if isinstance(shape, Shape) else shape
            assert isinstance(geometry, ArcPolyline), type(geometry)
            widths.add(round(geometry.width, 4))
    return widths


@unittest.skipUnless(RUNTIME, "needs a JITX runtime")
class TestQfnThermalAndPowerFanoutRuntime(TestCase):
    root: ClassVar[QfnThermalAndPowerFanout]
    complete: ClassVar[bool]
    unmet: ClassVar[list[str]]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        design = qfn_thermal_and_power_fanout_design
        # A changed design aborts a headless submit at "stabilization" unless
        # its stored state is removed first.
        shutil.rmtree(
            Path(__file__).resolve().parents[1]
            / "designs"
            / f"{design.__module__}.{design.__qualname__}",
            ignore_errors=True,
        )
        with jitx.runtime as rt:
            rd = rt.submit(design)
            rd.capture(wait=90)
            root = rd.root.circuit
            assert isinstance(root, QfnThermalAndPowerFanout)
            cls.root = root
            report = rd.issues(satisfied=True, wait=40)
            cls.complete = report.complete
            cls.unmet = [g.text for g in report.groups() if not g.satisfied]

    def setUp(self) -> None:
        self.c = type(self).root
        self.fab = FanoutSubstrate().constraints

    def test_every_route_is_made_with_no_open_issue(self) -> None:
        self.assertTrue(self.complete, "issue report incomplete: raise wait")
        self.assertEqual(self.unmet, [])
        for route in [*self.c.escape_routes, *self.c.trunks]:
            status = route.status
            assert status is not None
            self.assertTrue(status.routed)

    def test_escapes_stay_inside_their_pad_width_and_clear_the_other_pads(
        self,
    ) -> None:
        lp = self.c.u1.landpattern
        pads = [p for _, p in visit(lp, Pad)]
        for route, pad in zip(self.c.escape_routes, _iovdd_pads(self.c), strict=True):
            copper = _pad_copper(pad)
            minx, miny, maxx, maxy = copper.bounds
            (width,) = _widths(route)
            self.assertLess(width, min(maxx - minx, maxy - miny))
            self.assertGreaterEqual(width, self.fab.min_copper_width)
            others = [_pad_copper(p) for p in pads if p is not pad]
            gap = min(copper.distance(g) for g in others)
            escape = _copper(route)
            # Narrower than the pad and straight out of it, the escape is no
            # closer to another pad than its own pad is.
            self.assertGreaterEqual(min(escape.distance(g) for g in others), gap - 1e-4)

    def test_trunks_run_at_the_power_width_into_each_fanout_via(self) -> None:
        for trunk, via in zip(self.c.trunks, self.c.fanout_vias, strict=True):
            self.assertEqual(_widths(trunk), {POWER_WIDTH})
            self.assertLess(_copper(trunk).distance(Point(_xy(via))), 1e-3)

    def test_each_plane_holds_its_vias_solid(self) -> None:
        # A via that no relief rule matches joins its pour solid, so each
        # via's pad lies wholly in its plane's computed copper.
        for plane, vias, via in (
            (self.c.power_plane, self.c.fanout_vias, FanoutSubstrate.PowerVia),
            (self.c.ground_plane, self.c.thermal_vias, FanoutSubstrate.ThermalVia),
        ):
            self.assertNotIsInstance(plane.shape, Empty)
            copper = plane.shape.to_shapely().g
            for v in vias:
                pad = Point(_xy(v)).buffer(_radius(via))
                self.assertLess(pad.difference(copper).area, 1e-3)

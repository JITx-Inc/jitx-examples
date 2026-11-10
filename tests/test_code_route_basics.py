"""Tests for the code route basics pattern.

The offline tests check the layout the example sets up for each lesson: the
via column really blocks the straight path (with nothing in the way a sketch
turn leaves the route straight, measured on jitx 4.6.0), each sketch names
its side beyond the column, the pour surrounds the configured route so its
pullback can show the trace space, and the tapered route's target fits
inside its pad (JITX does not check that). Expected values are worked out
from the placed parts, vias, pads and pour that the tests read.

The runtime tests submit the design, capture it and measure the realized
traces: the side each sketched route passes on, the configured route's
width, its pullback from the pour and its rectangular end, and the tapered
row's width along its first route and along its short last route. They
need a JITX runtime started from the repository root and
``JITX_PATTERN_RUNTIME=1``.
"""

from __future__ import annotations

import math
import os
import unittest
from typing import ClassVar

import jitx
import shapely
from jitx import Pour
from jitx.circuit import Route
from jitx.component import Component
from jitx.controlpoint import RoutePoint
from jitx.inspect import visit
from jitx.landpattern import Pad
from jitx.net import Port
from jitx.sample import SampleSubstrate
from jitx.shapes import Shape
from jitx.shapes.primitive import Arc, ArcPolyline
from jitx.test import TestCase
from jitx.via import ViaDiameter
from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry

from jitxexamples.patterns.code_route_basics import (
    CodeRouteBasics,
    code_route_basics_design,
)

RUNTIME = os.environ.get("JITX_PATTERN_RUNTIME") == "1"


def _xy(
    obj: Component | SampleSubstrate.THVia | RoutePoint[Port],
) -> tuple[float, float]:
    """Placed position of a part, via or route point. Each ``ExampleChip``
    has one pad, at its origin."""
    assert obj.transform is not None
    x, y = obj.transform.translation
    return float(x), float(y)


def _via_radius() -> float:
    diameter = SampleSubstrate.THVia().diameter
    pad = diameter.pad if isinstance(diameter, ViaDiameter) else diameter
    return pad / 2


def _column(c: CodeRouteBasics, row_y: float) -> list[tuple[float, float]]:
    return [_xy(v) for v in c.vias if abs(_xy(v)[1] - row_y) < 5.0]


def _sketched_rows(
    c: CodeRouteBasics,
) -> list[tuple[str, Route, int, tuple[float, float], tuple[float, float]]]:
    """Name, route, side named by the row (1 above, -1 below) and the two pad
    centres of each sketched row."""
    a0, b0, a1, b1 = c.sketched_chips
    return [
        ("above", c.above, 1, _xy(a0), _xy(b0)),
        ("below", c.below, -1, _xy(a1), _xy(b1)),
    ]


class TestCodeRouteBasics(TestCase):
    def setUp(self) -> None:
        design = code_route_basics_design()
        circuit = design.circuit
        assert isinstance(circuit, CodeRouteBasics)
        self.c = circuit
        self.via_radius = _via_radius()
        self.min_width = design.substrate.constraints.min_copper_width

    def test_each_via_column_blocks_its_row(self) -> None:
        for name, _, _, a, b in _sketched_rows(self.c):
            with self.subTest(name):
                straight = LineString([a, b]).buffer(self.min_width / 2)
                column = shapely.union_all(
                    [Point(v).buffer(self.via_radius) for v in _column(self.c, a[1])]
                )
                self.assertTrue(straight.intersects(column))

    def test_sketch_runs_pad_to_pad_with_turns_on_the_named_side(self) -> None:
        for name, route, side, a, b in _sketched_rows(self.c):
            with self.subTest(name):
                sketch = route.sketch
                assert sketch is not None
                self.assertEqual(tuple(sketch.start.point), a)
                self.assertEqual(tuple(sketch.end.point), b)
                reach = max(abs(vy - a[1]) for _, vy in _column(self.c, a[1]))
                reach += self.via_radius
                self.assertTrue(sketch.turns)
                for _, ty in sketch.turns:
                    self.assertGreater(side * (ty - a[1]), reach)

    def test_pour_surrounds_the_configured_route(self) -> None:
        config = self.c.configured.config
        assert config is not None
        assert config.trace_width is not None and config.trace_space is not None
        a, b = _xy(self.c.configured_a), _xy(self.c.configured_b)
        keep = LineString([a, b]).buffer(config.trace_width / 2 + config.trace_space)
        pour = self.c.pour.shape.to_shapely().g
        self.assertTrue(pour.contains(keep))
        self.assertTrue(pour.contains(Point(_xy(self.c.pour_via))))

    def test_taper_target_is_wider_than_the_trace_and_inside_the_pad(self) -> None:
        # The Route.Target docstring: a rectangle target is centred on the
        # endpoint in the pad's own frame, and is not checked against the
        # pad. The row's intent is a narrow trace widening into its pad.
        config = self.c.tapered.config
        assert config is not None and config.trace_width is not None
        target = config.destination_target
        assert target is not None
        assert target.width is not None and target.height is not None
        ((_, pad),) = list(visit(self.c.tapered_b, Pad))
        assert pad.transform is not None
        shape = pad.shape if isinstance(pad.shape, Shape) else pad.shape.shape
        copper = (pad.transform * shape).to_shapely().g
        cx, cy = pad.transform.translation
        end = shapely.box(
            cx - target.width / 2,
            cy - target.height / 2,
            cx + target.width / 2,
            cy + target.height / 2,
        )
        self.assertLess(end.difference(copper).area, 1e-9)
        self.assertGreater(target.height, config.trace_width)


def _centreline(route: Route) -> LineString:
    """The realized trace's centre line, arcs sampled every 5 degrees."""
    points: list[tuple[float, float]] = []
    for trace in route.traces or []:
        for shape in trace.shapes:
            line = shape.geometry if isinstance(shape, Shape) else shape
            assert isinstance(line, ArcPolyline), type(line)
            for element in line.elements:
                if isinstance(element, Arc):
                    cx, cy = element.center
                    steps = max(2, math.ceil(abs(element.arc) / 5))
                    for i in range(steps + 1):
                        t = math.radians(element.start + element.arc * i / steps)
                        r = element.radius
                        points.append((cx + r * math.cos(t), cy + r * math.sin(t)))
                else:
                    points.append((float(element[0]), float(element[1])))
    return LineString(points)


def _copper(route: Route) -> BaseGeometry:
    shapes = [s.to_shapely().g for t in route.traces or [] for s in t.shapes]
    return shapely.union_all(shapes)


@unittest.skipUnless(RUNTIME, "needs a JITX runtime")
class TestCodeRouteBasicsRuntime(TestCase):
    root: ClassVar[CodeRouteBasics]
    unmet: ClassVar[list[str]]
    complete: ClassVar[bool]
    pours: ClassVar[list[BaseGeometry]]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        with jitx.runtime as rt:
            design = rt.submit(code_route_basics_design)
            design.capture(wait=60)
            root = design.root.circuit
            assert isinstance(root, CodeRouteBasics)
            cls.root = root
            report = design.issues(satisfied=True, wait=40)
            cls.complete = report.complete
            cls.unmet = [g.text for g in report.groups() if not g.satisfied]
            cls.pours = []
            for trace, pour in visit(root, Pour):
                shape = trace.transform * pour.shape if trace.transform else pour.shape
                cls.pours.append(shape.to_shapely().g)

    def setUp(self) -> None:
        self.c = type(self).root
        self.min_width = SampleSubstrate().constraints.min_copper_width

    def test_every_route_is_made_with_no_open_issue(self) -> None:
        self.assertTrue(self.complete, "issue report incomplete: raise wait")
        self.assertEqual(self.unmet, [])
        routes = (
            self.c.plain,
            self.c.above,
            self.c.below,
            self.c.configured,
            self.c.tapered_run,
            self.c.tapered,
        )
        for route in routes:
            status = route.status
            assert status is not None
            self.assertTrue(status.routed)

    def test_plain_route_is_straight_at_minimum_width(self) -> None:
        a, b = _xy(self.c.plain_a), _xy(self.c.plain_b)
        line = _centreline(self.c.plain)
        self.assertAlmostEqual(line.length, math.dist(a, b), places=3)
        self.assertLess(line.hausdorff_distance(LineString([a, b])), 1e-3)
        for trace in self.c.plain.traces or []:
            for shape in trace.shapes:
                geometry = shape.geometry if isinstance(shape, Shape) else shape
                assert isinstance(geometry, ArcPolyline)
                self.assertAlmostEqual(geometry.width, self.min_width, places=4)

    def test_sketched_routes_pass_on_the_named_side(self) -> None:
        # Only the ``above`` row tests the sketch: on jitx 4.6.0 the same row
        # with no sketch passed below, so ``below`` would pass without one.
        via_radius = _via_radius()
        for name, route, side, a, _ in _sketched_rows(self.c):
            with self.subTest(name):
                column = _column(self.c, a[1])
                column_x = column[0][0]
                reach = max(abs(vy - a[1]) for _, vy in column) + via_radius
                cut = LineString([(column_x, a[1] - 10), (column_x, a[1] + 10)])
                crossing = _centreline(route).intersection(cut)
                self.assertIsInstance(crossing, shapely.Point)
                assert isinstance(crossing, shapely.Point)
                self.assertGreater(side * (crossing.y - a[1]), reach)

    def test_configured_route_width_pullback_and_fitted_end(self) -> None:
        config = self.c.configured.config
        assert config is not None
        assert config.trace_width is not None and config.trace_space is not None
        a, b = _xy(self.c.configured_a), _xy(self.c.configured_b)
        copper = _copper(self.c.configured)

        middle = (a[0] + b[0]) / 2
        cut = LineString([(middle, a[1] - 5), (middle, a[1] + 5)])
        self.assertAlmostEqual(copper.intersection(cut).length, config.trace_width, 3)

        (pour,) = self.pours
        self.assertGreaterEqual(copper.distance(pour), config.trace_space - 1e-3)

        # A rectangle target is centred on the destination pad (its
        # docstring); the copper covers all of it, corners included.
        target = config.destination_target
        assert target is not None
        assert target.width is not None and target.height is not None
        end = shapely.box(
            b[0] - target.width / 2,
            b[1] - target.height / 2,
            b[0] + target.width / 2,
            b[1] + target.height / 2,
        )
        self.assertLess(end.difference(copper).area, 1e-6)

    def test_tapered_row_holds_its_width_then_tapers_into_the_pad(self) -> None:
        # The taper the Route.Target docstring's pad frame implies, on the
        # last route only: the trace width where that route starts, and at
        # the target's near edge (the target is centred on the pad) the
        # target's extent across the trace. This trace runs along the pads'
        # x axis, so that extent is the rectangle's height. The first route
        # has no target, so it keeps its trace width all the way.
        run = self.c.tapered_run.config
        config = self.c.tapered.config
        assert run is not None and run.trace_width is not None
        assert config is not None and config.trace_width is not None
        target = config.destination_target
        assert target is not None
        assert target.width is not None and target.height is not None
        a, b = _xy(self.c.tapered_a), _xy(self.c.tapered_b)
        start = _xy(self.c.taper_start)
        first, last = _copper(self.c.tapered_run), _copper(self.c.tapered)

        def width(copper: BaseGeometry, x: float) -> float:
            cut = LineString([(x, a[1] - 5), (x, a[1] + 5)])
            return copper.intersection(cut).length

        for x in (a[0], (a[0] + start[0]) / 2, start[0] - 0.1):
            self.assertAlmostEqual(width(first, x), run.trace_width, places=3)
        near_edge = b[0] - target.width / 2
        self.assertAlmostEqual(width(last, start[0]), config.trace_width, delta=0.01)
        self.assertAlmostEqual(width(last, near_edge), target.height, places=3)
        middle = width(last, (start[0] + near_edge) / 2)
        self.assertGreater(middle, config.trace_width + 0.01)
        self.assertLess(middle, target.height - 0.01)

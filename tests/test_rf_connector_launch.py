"""Tests for the SMA end launch pattern.

The offline tests instantiate ``rf_connector_launch_design`` and check each
launch against values worked out here from what the tests read: the
connector's pads, the board outline, the stated launch and cutout inputs, and
the line's structure and fence pattern. The cutout's outline is checked
against a hyperbola solved in the test from its two end widths and its
length. The end width is the line's coplanar slot: the trace and, on each
side, the pair rule's gap plus 0.01 mm, the pour gap the layout-constraints
spike measured (S9: 0.21 for a 0.2 gap).

The tangency square is checked against Duncan's rulings of 2026-11-06: the
tangency comes from a small square of ground copper, and the clearance from
the route to it sets the bend. So the square sits on the inside of the turn,
from the launch point along the axis, with its near side the rule's
clearance off the trace's copper, and nothing is held off the line by a
route keepout ("we don't need the keepout").

The runtime tests (``JITX_PATTERN_RUNTIME=1``, with a runtime started at the
project root) build the design once and measure the captured board: each
exit is a straight section on the centre pad's axis, as a route point on the
axis made it in the code-layout spike (C4); the line holds the axis through
each square's far edge, then bends on an arc centred on the square's corner
whose radius is half the trace plus the rule's clearance, and keeps that
clearance to the square; the computed ground pour on each reference layer
has a void under the centre pad whose edge follows the hyperbola, ending at
the coplanar slot measured on the signal layer; no fence via sits in the
cutout; along the straight run of line each fence row on each side holds a
via at every pitch, with no gap a missing via would leave; and every fence
via's pad clears the signal copper by the sample fabrication constraints'
``min_copper_copper_space``.
"""

from __future__ import annotations

import math
import os
import shutil
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import jitx
import shapely
from jitx.circuit import Route
from jitx.constraints import AtomExpr, BinaryDesignConstraint, Tags
from jitx.controlpoint import RoutePoint
from jitx.copper import Copper, Pour
from jitx.feature import KeepOut
from jitx.inspect import visit
from jitx.landpattern import Pad
from jitx.sample import SampleFabConstraints
from jitx.shapes import Shape
from jitx.shapes.primitive import Arc, Empty
from jitx.test import TestCase
from jitx.transform import Point, Transform
from jitx.via import Via, ViaDiameter
from shapely.geometry.base import BaseGeometry

from jitxexamples.patterns.layout_cpwg_two_row_fence import (
    FENCE_PATTERN,
    FENCE_VIA,
    GAP,
    TRACE_WIDTH,
    RFLineTag,
)
from jitxexamples.components.connectors.wurth_elektronik_60312202114514 import (
    CENTER_PAD_WIDTH,
)
from jitxexamples.patterns.rf_connector_launch import (
    CUTOUT_TAPER_LENGTH,
    LAUNCH_LENGTH,
    PAD_CUTOUT_WIDTH,
    RF_LAYER,
    ConnectorLaunchLine,
    cutout_outline,
    rf_connector_launch_design,
)

POUR_GAP_OFFSET = 0.01
"""The coplanar pour starts this far past the winning clearance (the
layout-constraints spike, S9: a 0.21 mm gap for a 0.2 mm clearance)."""

SLOT_HALF_WIDTH = TRACE_WIDTH / 2 + GAP + POUR_GAP_OFFSET
"""Half the line's coplanar slot: half the trace and the pour gap, in mm."""

MIN_SPACE = SampleFabConstraints.min_copper_copper_space
"""The fab floor for copper to copper on the sample substrate, in mm."""


def _fence_pad_radius() -> float:
    diameter = FENCE_VIA.diameter
    pad = diameter.pad if isinstance(diameter, ViaDiameter) else diameter
    return pad / 2


def _hyperbola(s: float, h0: float, h1: float, length: float) -> float:
    """h = k / (s + s0) through (0, h0) and (length, h1): s0 and k solved from
    the two end points, h0 s0 = h1 (length + s0)."""
    s0 = h1 * length / (h0 - h1)
    k = h0 * s0
    return k / (s + s0)


def _pad_shape(pad: Pad) -> Shape:
    return pad.shape if isinstance(pad.shape, Shape) else pad.shape.shape


def _world(t: Transform | None, shape: Shape) -> BaseGeometry:
    return (t * shape if t is not None else shape).to_shapely().g


def _pad_world(t: Transform | None, pad: Pad) -> BaseGeometry:
    """A pad's copper in the board's frame; ``t`` is the trace transform
    ``visit`` gives for it."""
    assert t is not None and pad.transform is not None
    return _world(t * pad.transform, _pad_shape(pad))


@dataclass(frozen=True)
class Exit:
    """One launch's centre pad and launch point, in the board's frame."""

    centre: Point
    axis: Point
    """Unit vector along the pad, pointing into the board."""
    pad_length: float
    launch_point: Point

    @property
    def inner_end(self) -> Point:
        return (
            self.centre[0] + self.axis[0] * self.pad_length / 2,
            self.centre[1] + self.axis[1] * self.pad_length / 2,
        )

    def at(self, s: float, across: float = 0.0) -> Point:
        """``s`` along the axis from the pad's inner end, ``across`` to its
        left."""
        x, y = self.inner_end
        ax, ay = self.axis
        return (x + ax * s - ay * across, y + ay * s + ax * across)


def _launch_paths(root: ConnectorLaunchLine) -> list[str]:
    return [f"launches[{i}]" for i in range(len(root.launches))]


def _exits(root: ConnectorLaunchLine) -> list[Exit]:
    """Each launch's centre pad (its long axis, pointing at the board's
    centre) and its launch point, read from the placed objects."""
    pads: dict[str, BaseGeometry] = {}
    for trace, pad in visit(root, Pad):
        path = str(trace.path)
        if path.endswith(".sig"):
            pads[path.split(".")[0]] = _pad_world(trace.transform, pad)
    points: dict[str, Point] = {}
    for trace, rp in visit(root, RoutePoint):
        assert trace.transform is not None and rp.transform is not None
        points[str(trace.path).split(".")[0]] = (
            trace.transform
            * rp.transform
            * (
                0.0,
                0.0,
            )
        )
    exits = []
    for name in _launch_paths(root):
        box = pads[name].minimum_rotated_rectangle
        assert isinstance(box, shapely.Polygon)
        corners = list(box.exterior.coords)[:4]
        sides = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
        a, b = max(sides, key=lambda e: math.dist(*e))
        length = math.dist(a, b)
        c = pads[name].centroid
        axis = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
        if axis[0] * -c.x + axis[1] * -c.y < 0:
            axis = (-axis[0], -axis[1])
        exits.append(Exit((c.x, c.y), axis, length, points[name]))
    return exits


def _keepouts(root: ConnectorLaunchLine, name: str) -> list[tuple[str, KeepOut]]:
    return [
        (str(t.path), k)
        for t, k in visit(root, KeepOut)
        if str(t.path).startswith(name)
    ]


def _keepout_geometry(root: ConnectorLaunchLine, path: str) -> BaseGeometry:
    for t, k in visit(root, KeepOut):
        if str(t.path) == path:
            return _world(t.transform, k.shape)
    raise AssertionError(f"no keepout at {path}")


def _squares(root: ConnectorLaunchLine) -> list[shapely.Polygon]:
    """Each launch's copper drawn in code (not its pours), in the board's
    frame, in launch order."""
    out = []
    for name in _launch_paths(root):
        drawn = [
            _world(t.transform, c.shape)
            for t, c in visit(root, Copper)
            if not isinstance(c, Pour) and str(t.path).startswith(name + ".")
        ]
        assert len(drawn) == 1, (name, len(drawn))
        assert isinstance(drawn[0], shapely.Polygon)
        out.append(drawn[0])
    return out


def _axis_frame(e: Exit, p: Point) -> tuple[float, float]:
    """``p`` as (along, across): along the axis from the pad's inner end, and
    across it to the axis's left."""
    x, y = p[0] - e.inner_end[0], p[1] - e.inner_end[1]
    return (x * e.axis[0] + y * e.axis[1], -x * e.axis[1] + y * e.axis[0])


def _turn_side(e: Exit, other: Exit) -> int:
    """The side of ``e``'s axis (1 left, -1 right) the other launch point is
    on: the inside of the turn the line makes past ``e``'s launch point."""
    _, across = _axis_frame(e, other.launch_point)
    return 1 if across > 0 else -1


def _tangency_rule(root: ConnectorLaunchLine, square: Copper) -> BinaryDesignConstraint:
    """The one clearance rule between a tag on ``square`` and ``RFLineTag``."""
    tags = Tags.get(square)
    mine = {type(t) for t in tags.tags} if tags else set()
    rules = []
    for _, rule in visit(root, BinaryDesignConstraint):
        atoms = [rule.first, rule.second]
        if not all(isinstance(a, AtomExpr) for a in atoms):
            continue
        kinds = {type(a.atom) for a in atoms if isinstance(a, AtomExpr)}
        if RFLineTag in kinds and kinds - {RFLineTag} <= mine and kinds & mine:
            rules.append(rule)
    assert len(rules) == 1, rules
    return rules[0]


def _clearance(rule: BinaryDesignConstraint) -> float:
    assert rule.clearance_constraint is not None
    return rule.clearance_constraint.clearance


def _half_width_at(void_or_cut: BaseGeometry, e: Exit, s: float) -> float:
    """Half the width of ``void_or_cut`` across the axis at ``s`` along it."""
    cut = shapely.LineString([e.at(s, -5.0), e.at(s, 5.0)])
    return void_or_cut.intersection(cut).length / 2


class TestEdgeLaunch(TestCase):
    def setUp(self) -> None:
        design = rf_connector_launch_design()
        root = design.circuit
        assert isinstance(root, ConnectorLaunchLine)
        self.root = root
        self.board = design.board.shape.to_shapely().g
        self.exits = _exits(root)

    def test_each_connector_sits_on_a_board_edge_pointing_in(self) -> None:
        # The connector's docstring: origin on the board edge, +x into the
        # board along the centre pad, which starts at the body face.
        self.assertEqual(len(self.exits), 2)
        assert isinstance(self.board, shapely.Polygon)
        edge = self.board.exterior
        for e in self.exits:
            outer = (
                e.centre[0] - e.axis[0] * e.pad_length / 2,
                e.centre[1] - e.axis[1] * e.pad_length / 2,
            )
            self.assertLess(edge.distance(shapely.Point(outer)), 1e-9)
            self.assertTrue(self.board.contains(shapely.Point(e.inner_end)))

    def test_launch_point_is_on_the_pad_axis_past_the_pad(self) -> None:
        for e in self.exits:
            expected = e.at(LAUNCH_LENGTH)
            self.assertAlmostEqual(e.launch_point[0], expected[0], places=9)
            self.assertAlmostEqual(e.launch_point[1], expected[1], places=9)

    def test_cutout_outline_follows_the_hyperbola(self) -> None:
        h0 = PAD_CUTOUT_WIDTH / 2
        for name, e in zip(_launch_paths(self.root), self.exits, strict=True):
            cutout = _keepout_geometry(self.root, f"{name}.cutout")
            with self.subTest(name):
                # Under the pad, the full cutout width.
                for s in (-e.pad_length + 0.01, -e.pad_length / 2, -0.01):
                    self.assertAlmostEqual(_half_width_at(cutout, e, s), h0, places=6)
                # Along the taper, the hyperbola. The outline is drawn with
                # straight segments, so allow a chord's sag (under 1e-3 mm
                # for this curve and step).
                n = 50
                for i in range(1, n):
                    s = CUTOUT_TAPER_LENGTH * i / n
                    want = _hyperbola(s, h0, SLOT_HALF_WIDTH, CUTOUT_TAPER_LENGTH)
                    got = _half_width_at(cutout, e, s)
                    self.assertAlmostEqual(got, want, delta=1e-3, msg=f"s {s}")
                # The taper ends at the slot and the cutout ends there.
                end = _half_width_at(cutout, e, CUTOUT_TAPER_LENGTH - 1e-6)
                self.assertAlmostEqual(end, SLOT_HALF_WIDTH, places=5)
                self.assertEqual(
                    _half_width_at(cutout, e, CUTOUT_TAPER_LENGTH + 0.01), 0.0
                )

    def test_cutout_covers_the_centre_pad_and_clears_the_ground_pads(self) -> None:
        for name in _launch_paths(self.root):
            cutout = _keepout_geometry(self.root, f"{name}.cutout")
            with self.subTest(name):
                for trace, pad in visit(self.root, Pad):
                    path = str(trace.path)
                    if not path.startswith(name + "."):
                        continue
                    copper = _pad_world(trace.transform, pad)
                    if path.endswith(".sig"):
                        self.assertLess(copper.difference(cutout).area, 1e-9)
                    else:
                        # The plane has to reach the bottom ground pads.
                        self.assertFalse(copper.intersects(cutout), path)

    def test_cutout_voids_pours_and_vias_on_every_ground_layer_under_the_line(
        self,
    ) -> None:
        under = {p.layer for _, p in visit(self.root, Pour) if p.layer != RF_LAYER}
        self.assertTrue(under)
        for name in _launch_paths(self.root):
            ((_, cutout),) = [
                (p, k) for p, k in _keepouts(self.root, name) if p.endswith(".cutout")
            ]
            with self.subTest(name):
                self.assertTrue(cutout.pour)
                self.assertTrue(cutout.via)
                layers = {
                    i for lo, hi in cutout.layers.ranges for i in range(lo, hi + 1)
                }
                self.assertEqual(layers, under)

    def test_taper_stays_on_the_straight_exit(self) -> None:
        # The taper assumes a straight trace over it, so it ends at or before
        # the launch point; the outline refuses one that runs past.
        for name, e in zip(_launch_paths(self.root), self.exits, strict=True):
            cutout = _keepout_geometry(self.root, f"{name}.cutout")
            assert isinstance(cutout, shapely.Polygon)
            reach = max(
                (x - e.inner_end[0]) * e.axis[0] + (y - e.inner_end[1]) * e.axis[1]
                for x, y in cutout.exterior.coords
            )
            self.assertLessEqual(reach, LAUNCH_LENGTH + 1e-9)
        with self.assertRaisesRegex(ValueError, "runs past"):
            cutout_outline(taper_length=LAUNCH_LENGTH + 0.1)

    def test_cutout_refuses_a_width_that_leaves_fence_row_one_by_the_pad(
        self,
    ) -> None:
        # For a cutout width, the first point along row 1 where the cutout, by
        # the hyperbola solved here, no longer reaches a row-1 via pad, and how
        # far a pad there would sit from the placed centre pad. A width whose
        # pad sits under the fab floor has to be refused, and one whose pad
        # clears it accepted. 0.751 and 0.752 mm are wider than row 1's pad
        # edges, so the cutout covers the first sites beside the pad and only
        # the taper's narrowing leaves a site too close.
        e = self.exits[0]
        (pad,) = [
            _pad_world(t.transform, p)
            for t, p in visit(self.root, Pad)
            if str(t.path).startswith("launches[0].") and str(t.path).endswith(".sig")
        ]
        radius = _fence_pad_radius()
        edge = _row_centre(1) - radius

        def first_site_gap(width: float) -> float:
            h0, h1 = width / 2, SLOT_HALF_WIDTH
            # h(s) = k / (s + s0) falls to the pad edge at s = k / edge - s0.
            s0 = h1 * CUTOUT_TAPER_LENGTH / (h0 - h1)
            s = max(0.0, h0 * s0 / edge - s0)
            site = shapely.Point(e.at(s, _row_centre(1)))
            return site.distance(pad) - radius

        for width in (0.751, 0.752):
            with self.subTest(width):
                self.assertGreater(width / 2, edge)
                self.assertLess(first_site_gap(width), MIN_SPACE)
                with self.assertRaisesRegex(ValueError, "fence row 1"):
                    cutout_outline(pad_cutout_width=width)
        # The narrowest width whose first uncovered site clears the floor,
        # by bisection on the gap, which grows with the width.
        lo, hi = 0.752, 1.0
        self.assertGreaterEqual(first_site_gap(hi), MIN_SPACE)
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if first_site_gap(mid) < MIN_SPACE else (lo, mid)
        accepted = hi + 1e-3
        self.assertLess(accepted, PAD_CUTOUT_WIDTH)
        cutout_outline(pad_cutout_width=accepted)

    def test_cutout_refuses_a_taper_that_ends_beside_row_one(self) -> None:
        # Past the taper's end the cutout stops, so a taper that ends where
        # a row-1 via pad would still come under the fab floor of the centre
        # pad's corner leaves that pad unguarded at any width. The reach is
        # worked out here from the row's centre, the via pad and the pad.
        radius = _fence_pad_radius()
        across = _row_centre(1) - CENTER_PAD_WIDTH / 2
        reach = math.sqrt((radius + MIN_SPACE) ** 2 - across**2)
        for taper in (0.0, -1.0, reach / 2, reach):
            with (
                self.subTest(taper),
                self.assertRaisesRegex(
                    ValueError, "taper (must have a length|ends within)"
                ),
            ):
                cutout_outline(taper_length=taper)

    def test_cutout_refuses_a_width_inside_the_slot_and_too_few_steps(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "coplanar slot"):
            cutout_outline(pad_cutout_width=2 * SLOT_HALF_WIDTH - 0.02)
        for steps in (0, -1):
            with self.subTest(steps), self.assertRaisesRegex(ValueError, "steps"):
                cutout_outline(steps=steps)

    def test_tangency_square_sits_inside_each_turn_at_the_rule_clearance(
        self,
    ) -> None:
        # Duncan, 2026-11-06: a small square, whose clearance to the route
        # sets the bend. The line holds the axis to the launch point, so the
        # square starts there and its near side stands the rule's clearance
        # off the trace's copper: nearer, the route cannot keep the
        # clearance on the axis. It goes on the inside of the turn, the side
        # the other launch point is on.
        squares = _squares(self.root)
        for i, (e, square) in enumerate(zip(self.exits, squares, strict=True)):
            other = self.exits[1 - i]
            launch = self.root.launches[i]
            rule = _tangency_rule(self.root, launch.square)
            clearance = _clearance(rule)
            with self.subTest(i):
                self.assertGreater(clearance, GAP)
                along = [
                    _axis_frame(e, (p[0], p[1]))[0] for p in square.exterior.coords
                ]
                across = [
                    _axis_frame(e, (p[0], p[1]))[1] for p in square.exterior.coords
                ]
                side = _turn_side(e, other)
                near = min(side * a for a in across)
                self.assertAlmostEqual(near, TRACE_WIDTH / 2 + clearance, places=9)
                self.assertTrue(all(side * a > 0 for a in across))
                self.assertAlmostEqual(min(along), LAUNCH_LENGTH, places=9)
                # A square: as long along the axis as it is across.
                self.assertAlmostEqual(
                    max(along) - min(along), max(side * a for a in across) - near
                )
                self.assertAlmostEqual(square.area, (max(along) - min(along)) ** 2)

    def test_tangency_rule_wins_over_the_ground_gap_rule(self) -> None:
        # The square is ground copper, so the gap rule between RFLineTag and
        # GroundTag also matches it. Built with the tangency rule at the
        # default priority, the gap rule won and the line took no bend
        # around the square (PR lane, 2026-11-06), so the tangency rule
        # needs the higher priority.
        gap = self.root.gap_rule
        assert isinstance(gap, BinaryDesignConstraint)
        for launch in self.root.launches:
            rule = _tangency_rule(self.root, launch.square)
            self.assertGreater(rule.priority, gap.priority)

    def test_no_route_keepout_holds_the_line(self) -> None:
        # Duncan, 2026-11-06: other copper is held off the line by a tag and
        # a clearance rule, not a keepout. The only keepouts are the cutouts,
        # on the ground layers under the line.
        for path, k in _keepouts(self.root, ""):
            with self.subTest(path):
                self.assertTrue(path.endswith(".cutout"))
                self.assertFalse(k.route)
                self.assertNotIn(RF_LAYER, k.layers)


@dataclass(frozen=True)
class Measured:
    routed: list[tuple[str, bool]]
    unmet: list[str]
    complete: bool
    exits: list[Exit]
    exit_copper: list[BaseGeometry]
    line_copper: BaseGeometry
    centre_lines: list[tuple[shapely.LineString, float]]
    """Each realized trace's centre line, arcs sampled every degree, with
    its width."""
    line_arcs: list[tuple[Point, float]]
    """Centre and radius of each arc of the line between the launch points."""
    squares: list[shapely.Polygon]
    clearances: list[float]
    coplanar: BaseGeometry
    reference: dict[int, BaseGeometry]
    cutouts: list[BaseGeometry]
    signal_pads: list[BaseGeometry]
    vias: list[tuple[Point, str | None]]


def _pour_world(t: Transform | None, pour: Pour) -> BaseGeometry:
    shape = pour.shape
    geometry = shape.geometry if isinstance(shape, Shape) else shape
    if isinstance(geometry, Empty):
        return shapely.Polygon()
    return _world(t, shape)


def _arc_point(arc: Arc, frac: float) -> Point:
    a = math.radians(float(arc.start) + float(arc.arc or 0.0) * frac)
    r = float(arc.radius)
    return (
        float(arc.center[0]) + r * math.cos(a),
        float(arc.center[1]) + r * math.sin(a),
    )


def _centre_line(
    t: Transform | None, shape: Shape, step_deg: float = 1.0
) -> tuple[shapely.LineString, list[tuple[Point, float]], float]:
    """A realized trace shape's centre line in the board's frame, its arcs
    sampled every ``step_deg`` (on the arc, so each chord lies inside it by
    under r (1 - cos(step / 2)), 0.0002 mm at r = 1.15), with each arc's
    centre and radius, and the trace's width."""
    placed = t * shape if t is not None else shape
    xf = placed.transform
    geometry = placed.geometry
    width = getattr(geometry, "width", None)
    assert width is not None, "a trace with no width"
    points: list[Point] = []
    arcs: list[tuple[Point, float]] = []
    for el in getattr(geometry, "elements", []):
        if isinstance(el, Arc):
            n = max(2, math.ceil(abs(float(el.arc or 0.0)) / step_deg))
            points += [xf * _arc_point(el, i / n) for i in range(n + 1)]
            arcs.append(
                (xf * (float(el.center[0]), float(el.center[1])), float(el.radius))
            )
        else:
            points.append(xf * (float(el[0]), float(el[1])))
    return shapely.LineString(points), arcs, float(width)


def _measure() -> Measured:
    design = rf_connector_launch_design
    # A changed design aborts a headless submit at "stabilization" unless its
    # stored state is removed first.
    root_dir = Path(__file__).resolve().parents[1]
    shutil.rmtree(
        root_dir / "designs" / f"{design.__module__}.{design.__qualname__}",
        ignore_errors=True,
    )
    with jitx.runtime as runtime:
        rd = runtime.submit(design)
        rd.capture(wait=120)
        root = rd.root.circuit
        assert isinstance(root, ConnectorLaunchLine)
        routed = []
        copper: dict[str, BaseGeometry] = {}
        centre_lines: list[tuple[shapely.LineString, float]] = []
        line_arcs: list[tuple[Point, float]] = []
        for trace, route in visit(root, Route):
            assert route.status is not None
            routed.append((str(trace.path), route.status.routed))
            shapes = [
                _world(trace.transform, s) for t in route.traces or [] for s in t.shapes
            ]
            copper[str(trace.path)] = shapely.union_all(shapes)
            for t in route.traces or []:
                for s in t.shapes:
                    centre, arcs, width = _centre_line(trace.transform, s)
                    centre_lines.append((centre, width))
                    if str(trace.path) == "line":
                        line_arcs += arcs
        coplanar = shapely.Polygon()
        reference: dict[int, BaseGeometry] = {}
        for trace, pour in visit(root, Pour):
            g = _pour_world(trace.transform, pour)
            if pour.layer == RF_LAYER:
                coplanar = g
            else:
                reference[pour.layer] = g
        names = _launch_paths(root)
        signal_pads = [
            _pad_world(trace.transform, pad)
            for trace, pad in visit(root, Pad)
            if str(trace.path).endswith(".sig")
        ]
        cutouts = [_keepout_geometry(root, f"{n}.cutout") for n in names]
        # rd.query(Via) yields every via; the ones placed in code (none here)
        # are left out by identity, leaving the computed fence vias.
        placed = {id(via) for _, via in visit(rd.root, Via)}
        vias = []
        for trace, via in rd.query(Via):
            if id(via) in placed:
                continue
            assert trace.transform is not None and via.transform is not None
            x, y = (trace.transform * via.transform).translation
            net = rd.nets.find(via)
            vias.append(((float(x), float(y)), net.name if net else None))
        report = rd.issues(satisfied=True, wait=60)
        return Measured(
            routed=routed,
            unmet=[g.text for g in report.groups() if not g.satisfied],
            complete=report.complete,
            exits=_exits(root),
            exit_copper=[copper[f"{n}.exit"] for n in names],
            line_copper=copper["line"],
            centre_lines=centre_lines,
            line_arcs=line_arcs,
            squares=_squares(root),
            clearances=[
                _clearance(_tangency_rule(root, launch.square))
                for launch in root.launches
            ],
            coplanar=coplanar,
            reference=reference,
            cutouts=cutouts,
            signal_pads=signal_pads,
            vias=vias,
        )


def _straight_run(m: Measured) -> tuple[Point, Point]:
    """The line's straight run between its two bends: its centre line's
    longest segment."""
    line = [c for c, _ in m.centre_lines if c.distance(shapely.Point(0, 0)) < 1]
    assert len(line) == 1
    coords = [(float(x), float(y)) for x, y in shapely.get_coordinates(line[0])]
    return max(zip(coords, coords[1:], strict=False), key=lambda pq: math.dist(*pq))


def _row_centre(k: int) -> float:
    """Row k's distance from the centreline: half the trace, the first row's
    offset from the trace edge, then the row spacing (layout-constraints S9)."""
    assert FENCE_PATTERN.initial_offset is not None
    return (
        TRACE_WIDTH / 2 + FENCE_PATTERN.initial_offset + (k - 1) * FENCE_PATTERN.offset
    )


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestEdgeLaunchBuild(TestCase):
    measured: ClassVar[Measured]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.measured = _measure()

    def test_every_route_routes_with_no_open_issue(self) -> None:
        m = self.measured
        self.assertEqual(len(m.routed), 3)
        self.assertEqual([n for n, ok in m.routed if not ok], [])
        self.assertTrue(m.complete, "issue report incomplete: raise wait")
        self.assertEqual(m.unmet, [])

    def test_each_exit_is_straight_on_the_pad_axis(self) -> None:
        # Spike C4: a route point on the axis gives an exact straight section
        # on the axis. The copper covers the axis from the pad's inner end
        # to the launch point at the trace's full width, and nothing of it
        # leaves the axis by more than half the trace.
        exits = zip(self.measured.exits, self.measured.exit_copper, strict=True)
        for e, copper in exits:
            with self.subTest(e.launch_point):
                self.assertFalse(copper.is_empty)
                axis = shapely.LineString([e.centre, e.launch_point])
                self.assertLess(
                    copper.difference(
                        axis.buffer(TRACE_WIDTH / 2 + 1e-3, cap_style="square")
                    ).area,
                    1e-6,
                )
                launch = shapely.LineString([e.inner_end, e.launch_point]).buffer(
                    TRACE_WIDTH / 2 - 1e-3, cap_style="flat"
                )
                self.assertLess(launch.difference(copper).area, 1e-6)
                # Angle and drift of the copper's own long axis.
                box = copper.minimum_rotated_rectangle
                assert isinstance(box, shapely.Polygon)
                corners = list(box.exterior.coords)[:4]
                sides = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
                a, b = max(sides, key=lambda s: math.dist(*s))
                angle = math.degrees(
                    math.asin(
                        abs((b[0] - a[0]) * e.axis[1] - (b[1] - a[1]) * e.axis[0])
                        / math.dist(a, b)
                    )
                )
                self.assertLess(angle, 0.01)
                short = min(math.dist(*s) for s in sides)
                self.assertAlmostEqual(short, TRACE_WIDTH, delta=1e-3)
                centre = box.centroid
                drift = abs(
                    -(centre.x - e.centre[0]) * e.axis[1]
                    + (centre.y - e.centre[1]) * e.axis[0]
                )
                self.assertLess(drift, 1e-3)

    def test_line_holds_the_axis_through_each_square(self) -> None:
        # Past the launch point the line stays on the axis until it has
        # passed the square's far edge, where its bend can start.
        m = self.measured
        line = [c for c, _ in m.centre_lines if c.distance(shapely.Point(0, 0)) < 1]
        self.assertEqual(len(line), 1)
        for e, square in zip(m.exits, m.squares, strict=True):
            with self.subTest(e.launch_point):
                far = max(
                    _axis_frame(e, (p[0], p[1]))[0] for p in square.exterior.coords
                )
                slab = shapely.Polygon(
                    [
                        e.at(LAUNCH_LENGTH, -3),
                        e.at(far, -3),
                        e.at(far, 3),
                        e.at(LAUNCH_LENGTH, 3),
                    ]
                )
                held = line[0].intersection(slab)
                self.assertAlmostEqual(held.length, far - LAUNCH_LENGTH, delta=1e-3)
                for p in shapely.get_coordinates(held):
                    self.assertLess(abs(_axis_frame(e, (p[0], p[1]))[1]), 1e-3)

    def test_line_bends_around_each_square_corner(self) -> None:
        # Duncan, 2026-11-06: the clearance from the route to the square sets
        # the bend. The line keeps the clearance to the square's inner far
        # corner, so it turns on an arc centred there, of half the trace plus
        # the clearance.
        m = self.measured
        for e, square, clearance in zip(m.exits, m.squares, m.clearances, strict=True):
            frame = [_axis_frame(e, (p[0], p[1])) for p in square.exterior.coords]
            far = max(a for a, _ in frame)
            near = min(abs(c) for _, c in frame)
            side = 1 if frame[0][1] > 0 else -1
            corner = e.at(far, side * near)
            with self.subTest(e.launch_point):
                bends = [
                    (centre, r)
                    for centre, r in m.line_arcs
                    if math.dist(centre, corner) < 1e-3
                ]
                self.assertEqual(len(bends), 1, m.line_arcs)
                self.assertAlmostEqual(
                    bends[0][1], TRACE_WIDTH / 2 + clearance, delta=1e-3
                )

    def test_routed_copper_keeps_the_rule_clearance_to_each_square(self) -> None:
        # The gap from each trace's centre line, less half its width.
        m = self.measured
        for square, clearance in zip(m.squares, m.clearances, strict=True):
            gap = min(c.distance(square) - w / 2 for c, w in m.centre_lines)
            self.assertGreaterEqual(gap, clearance - 1e-3)
            self.assertLess(gap, clearance + 1e-3)

    def test_ground_is_void_under_each_centre_pad(self) -> None:
        h0 = PAD_CUTOUT_WIDTH / 2
        for layer, pour in self.measured.reference.items():
            for e in self.measured.exits:
                with self.subTest((layer, e.launch_point)):
                    self.assertFalse(pour.is_empty)
                    pad = shapely.LineString(
                        [e.at(-e.pad_length + 0.5), e.inner_end]
                    ).buffer(h0 - 1e-3, cap_style="flat")
                    self.assertLess(pour.intersection(pad).area, 1e-6)
                    # Ground just past the cutout's edge on both sides.
                    for side in (1, -1):
                        p = shapely.Point(e.at(-e.pad_length / 2, side * (h0 + 0.05)))
                        self.assertTrue(pour.contains(p))

    def test_void_edge_follows_the_hyperbola_to_the_coplanar_slot(self) -> None:
        m = self.measured
        # The end width comes from the build: the coplanar slot on the signal
        # layer, measured square across the middle of the line.
        a, b = _straight_run(m)
        ux, uy = (b[0] - a[0]) / math.dist(a, b), (b[1] - a[1]) / math.dist(a, b)
        mid = shapely.LineString([(5.0 * uy, -5.0 * ux), (-5.0 * uy, 5.0 * ux)])
        slot = mid.difference(m.coplanar)
        (gap,) = [
            g
            for g in getattr(slot, "geoms", [slot])
            if g.distance(shapely.Point(0, 0)) < 1e-9
        ]
        h1 = gap.length / 2
        h0 = PAD_CUTOUT_WIDTH / 2
        for layer, pour in m.reference.items():
            for e in m.exits:
                with self.subTest((layer, e.launch_point)):
                    for i in range(1, 25):
                        s = CUTOUT_TAPER_LENGTH * i / 25
                        cut = shapely.LineString([e.at(s, -2.0), e.at(s, 2.0)])
                        void = cut.difference(pour)
                        (hole,) = [
                            g
                            for g in getattr(void, "geoms", [void])
                            if g.distance(shapely.Point(e.at(s))) < 1e-9
                        ]
                        want = _hyperbola(s, h0, h1, CUTOUT_TAPER_LENGTH)
                        self.assertAlmostEqual(
                            hole.length / 2, want, delta=2e-3, msg=f"s {s}"
                        )
                    past = shapely.Point(e.at(CUTOUT_TAPER_LENGTH + 0.05))
                    self.assertTrue(pour.contains(past))

    def test_no_fence_via_in_the_cutout(self) -> None:
        # KeepOut(via=True): no auto-placed via in the area. The fence vias
        # take the ground net.
        m = self.measured
        pad = 2 * _fence_pad_radius()
        self.assertTrue(m.vias)
        self.assertEqual({net for _, net in m.vias}, {"GND"})
        for (x, y), _ in m.vias:
            disc = shapely.Point(x, y).buffer(pad / 2)
            for cutout in m.cutouts:
                self.assertFalse(disc.intersects(cutout), (x, y))

    def test_every_fence_via_clears_the_signal_copper(self) -> None:
        # The fab floor between the fence and the signal copper: no fence via
        # pad nearer the centre pads or the signal routes than
        # min_copper_copper_space.
        m = self.measured
        radius = _fence_pad_radius()
        self.assertEqual(len(m.signal_pads), 2)
        signal = shapely.union_all([*m.signal_pads, *m.exit_copper, m.line_copper])
        self.assertTrue(m.vias)
        for (x, y), _ in m.vias:
            gap = shapely.Point(x, y).distance(signal) - radius
            self.assertGreaterEqual(gap, MIN_SPACE - 1e-6, (x, y))

    def test_two_fence_rows_along_the_line(self) -> None:
        # Along the straight run between the bends, each row on each side
        # holds a via every pitch. A missing via leaves a gap of two
        # pitches, so no gap may pass the pitch by half of one, at either
        # end of the run or between neighbours.
        m = self.measured
        a, b = _straight_run(m)
        length = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        rows: dict[tuple[int, int], list[float]] = {}
        for (x, y), _ in m.vias:
            s = (x - a[0]) * ux + (y - a[1]) * uy
            t = -(x - a[0]) * uy + (y - a[1]) * ux
            if not 0 <= s <= length:
                continue
            (k,) = [k for k in (1, 2) if abs(abs(t) - _row_centre(k)) < 0.01]
            rows.setdefault((k, 1 if t > 0 else -1), []).append(s)
        limit = 1.5 * FENCE_PATTERN.pitch
        self.assertEqual(len(rows), 4, sorted(rows))
        for key, along in sorted(rows.items()):
            stops = [0.0, *sorted(along), length]
            gaps = [q - p for p, q in zip(stops, stops[1:], strict=False)]
            self.assertLessEqual(max(gaps), limit, key)

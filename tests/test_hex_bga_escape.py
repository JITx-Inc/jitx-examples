"""Tests for the hex BGA escape example.

The offline tests check the layout the example declares. The ball centres
come from the hex grid ``HexBGADecorated`` documents (columns
``pitch * sqrt(3) / 2`` apart, odd columns half a pitch lower, centred on
the part), the channel width from those centres and the via pad, and the
structure and fabrication figures from the substrate. From those, the full
pair does not fit the channel and the neck does, the transition clears the
last ground vias, a ground via sits at every ground ball, and every
structure and via stays inside the substrate's fabrication limits.

The runtime tests submit the design, capture it and measure the realized
copper: each section's width and gap against the structure it should take,
the change of width within 0.1 mm of the ``PairPoint``, every route made,
the ground vias in the built layout, and the copper's widths and clearances
against the fabrication limits. They need a JITX runtime started
from the repository root and ``JITX_PATTERN_RUNTIME=1``.
"""

from __future__ import annotations

import math
import os
import unittest
from typing import ClassVar

import jitx
import shapely
from jitx.circuit import Route
from jitx.constraints import Tag, Tags
from jitx.controlpoint import PairInsertion, PairPoint
from jitx.inspect import decompose
from jitx.net import Net
from jitx.shapes import Shape
from jitx.shapes.primitive import ArcPolyline
from jitx.shapes.shapely import ShapelyGeometry
from jitx.si import DifferentialRoutingStructure, RoutingStructure
from jitx.substrate import FabricationConstraints
from jitx.test import TestCase
from jitx.toleranced import Toleranced
from jitx.transform import Transform
from jitx.units import ohm
from jitx.via import Via, ViaDiameter
from jitxlib.protocols.displayport import DisplayPort
from jitxlib.protocols.ethernet.mdi.e10gbase_kr import E10GBaseKR
from jitxlib.protocols.ethernet.mdi.mdi100base_tx import MDI100BaseTX
from jitxlib.protocols.ethernet.mdi.mdi1000base_t import MDI1000BaseT
from jitxlib.protocols.usb import USB
from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry

from jitxexamples.demos.si_bga_optimization.generic_bga import (
    BGA_BALL_DIAMETER,
    BGA_HPITCH,
)
from jitxexamples.patterns.hex_bga_escape import (
    BGA_COLS,
    BGA_ORIGIN,
    BGA_ROWS,
    ESCAPE_LAYER,
    PAIR_BALLS,
    HexBgaEscape,
    HexEscapeSubstrate,
    hex_bga_escape_design,
)
from jitxexamples.patterns.layout_routing_structure_by_tag import (
    EscapeNeckTag,
    SignalTag,
)

RUNTIME = os.environ.get("JITX_PATTERN_RUNTIME") == "1"

TRANSITION_BAND = 0.1
"""How far from its ``PairPoint`` a tag split's change of structure may sit,
in mm. The point's own copper, centred on it, changes from the neck's trace
width to the full pair's, so the routes on either side end within about
0.1 mm of it."""


def ball_centres() -> dict[tuple[int, int], tuple[float, float]]:
    """Every ball centre in the circuit's frame, keyed (row from 0 at the
    top, column from 1 at the left): the hex grid ``HexBGADecorated``
    documents, centred on the part's origin."""
    column_pitch = BGA_HPITCH * math.sqrt(3) / 2
    centres = {}
    for r in range(BGA_ROWS):
        for c in range(1, BGA_COLS + 1):
            x = (c - 1 - (BGA_COLS - 1) / 2) * column_pitch
            y = ((BGA_ROWS - 1) / 2 - r) * BGA_HPITCH
            if (c - 1) % 2:
                y -= BGA_HPITCH / 2
            centres[(r, c)] = (BGA_ORIGIN[0] + x, BGA_ORIGIN[1] + y)
    return centres


def ground_balls() -> set[tuple[float, float]]:
    signal = {ball for pair in PAIR_BALLS for ball in pair}
    return {_key(xy) for rc, xy in ball_centres().items() if rc not in signal}


def field_bottom() -> float:
    return min(y for _, y in ball_centres().values()) - BGA_BALL_DIAMETER / 2


def _key(xy: tuple[float, float]) -> tuple[float, float]:
    return (round(xy[0], 4), round(xy[1], 4))


def _xy(obj: Via | PairPoint | PairInsertion) -> tuple[float, float]:
    assert obj.transform is not None
    x, y = obj.transform.translation
    return float(x), float(y)


def _pad_radius(via: type[Via]) -> float:
    diameter = via().diameter
    pad = diameter.pad if isinstance(diameter, ViaDiameter) else diameter
    return pad / 2


def _pair_layer(
    structure: DifferentialRoutingStructure,
) -> DifferentialRoutingStructure.Layer:
    layer = structure.layers[ESCAPE_LAYER]
    assert isinstance(layer, DifferentialRoutingStructure.Layer)
    return layer


def _clearance(layer: RoutingStructure.Layer) -> float:
    assert layer.clearance is not None
    return layer.clearance


def _half_span(layer: DifferentialRoutingStructure.Layer) -> float:
    """Centre of a pair to the edge of its clearance."""
    return layer.trace_width + layer.pair_spacing / 2 + _clearance(layer)


def _channel_clearance(c: HexBgaEscape, i: int) -> float:
    """The smallest distance from pair ``i``'s channel centreline, from its
    insertion down to the field's bottom edge, to a ground via pad."""
    p, n = (ball_centres()[ball] for ball in PAIR_BALLS[i])
    x = (p[0] + n[0]) / 2
    _, top = _xy(c.insertions[i])
    centreline = LineString([(x, top), (x, field_bottom())])
    radius = _pad_radius(HexEscapeSubstrate.GroundVia)
    return min(centreline.distance(Point(_xy(v))) for v in c.ground_vias) - radius


def _tagged(obj: Route | Net, tag: type[Tag]) -> bool:
    tags = Tags.get(obj)
    return tags is not None and any(isinstance(t, tag) for t in tags.tags)


class TestHexBgaEscape(TestCase):
    def setUp(self) -> None:
        design = hex_bga_escape_design()
        circuit = design.circuit
        assert isinstance(circuit, HexBgaEscape)
        self.c = circuit
        self.fab: FabricationConstraints = design.substrate.constraints
        self.full = _pair_layer(HexEscapeSubstrate.FULL_PAIR)
        self.neck = _pair_layer(HexEscapeSubstrate.NECK_PAIR)

    def test_full_pair_does_not_fit_the_channel_and_the_neck_does(self) -> None:
        for i in range(len(PAIR_BALLS)):
            with self.subTest(pair=i):
                room = _channel_clearance(self.c, i)
                self.assertGreater(_half_span(self.full), room)
                self.assertLessEqual(_half_span(self.neck), room)

    def test_a_neck_at_the_sample_floors_would_not_fit(self) -> None:
        # The docstring's reason for the HDI limits: a pair with traces, gap
        # and clearance all at the sample substrate's 0.127 mm floors.
        from jitx.sample import SampleFabConstraints

        floor = SampleFabConstraints.min_copper_width
        space = SampleFabConstraints.min_copper_copper_space
        for i in range(len(PAIR_BALLS)):
            with self.subTest(pair=i):
                room = _channel_clearance(self.c, i)
                self.assertGreater(floor + space / 2 + space, room)

    def test_structures_and_vias_stay_inside_the_fabrication_limits(self) -> None:
        width, space = self.fab.min_copper_width, self.fab.min_copper_copper_space
        for structure in (HexEscapeSubstrate.FULL_PAIR, HexEscapeSubstrate.NECK_PAIR):
            with self.subTest(structure.name):
                pair = _pair_layer(structure)
                self.assertGreaterEqual(pair.trace_width, width)
                self.assertGreaterEqual(pair.pair_spacing, space)
                self.assertGreaterEqual(_clearance(pair), space)
                uncoupled = structure.uncoupled_region
                assert uncoupled is not None
                leg = uncoupled.layers[ESCAPE_LAYER]
                self.assertGreaterEqual(leg.trace_width, width)
                self.assertGreaterEqual(_clearance(leg), space)
        for via in (HexEscapeSubstrate.GroundVia, HexEscapeSubstrate.SignalVia):
            with self.subTest(via.__name__):
                hole = via().hole_diameter
                hole = hole.pad if isinstance(hole, ViaDiameter) else hole
                self.assertGreaterEqual(hole, self.fab.min_drill_diameter)
                ring = _pad_radius(via) - hole / 2
                self.assertGreaterEqual(ring + 1e-9, self.fab.min_annular_ring)

    def test_transition_clears_the_field_and_its_last_vias(self) -> None:
        # The full section may start up to TRANSITION_BAND above the point;
        # from there down, the full pair keeps its clearance to every ground
        # via pad.
        radius = _pad_radius(HexEscapeSubstrate.GroundVia)
        half = self.full.trace_width + self.full.pair_spacing / 2
        for i, point in enumerate(self.c.transitions):
            with self.subTest(pair=i):
                x, y = _xy(point)
                self.assertLess(y + TRANSITION_BAND, field_bottom())
                full_pair = shapely.box(
                    x - half, y - 1.0, x + half, y + TRANSITION_BAND
                )
                gap = min(
                    full_pair.distance(Point(_xy(v))) - radius
                    for v in self.c.ground_vias
                )
                self.assertGreaterEqual(gap, _clearance(self.full))

    def test_a_ground_via_sits_at_every_ground_ball(self) -> None:
        placed = [_key(_xy(v)) for v in self.c.ground_vias]
        self.assertEqual(len(placed), len(set(placed)))
        self.assertEqual(set(placed), ground_balls())

    def test_a_100_ohm_lookup_returns_the_full_pair(self) -> None:
        # The docstring's rule for the 0 ohm neck label: no lookup for a real
        # impedance returns the neck, so a protocol constraint asking the
        # substrate for the pair's 100 ohm gets the full pair.
        substrate = hex_bga_escape_design().substrate
        found = substrate.differential_routing_structure(100 * ohm)
        self.assertIs(found, HexEscapeSubstrate.FULL_PAIR)

    def test_no_protocol_lookup_returns_another_pair_structure(self) -> None:
        # The lookup above takes the first structure on a tie, so it passes
        # with the neck relabelled 100 ohm while the neck is declared after
        # the full pair. jitxlib's differential protocols each look the
        # substrate up by their own impedance window. No structure but the
        # full pair may fall in any of those windows, whatever the declaration
        # order, and each window that admits the full pair returns it.
        windows: list[tuple[str, Toleranced]] = [
            *((f"USB {u.name}", u.impedance) for u in USB),
            ("DisplayPort", DisplayPort.Standard.impedance),
            ("1000BASE-T", MDI1000BaseT.Standard.impedance),
            ("100BASE-TX", MDI100BaseTX.Standard.impedance),
            ("10GBASE-KR", E10GBaseKR.Standard.impedance),
        ]
        substrate = hex_bga_escape_design().substrate
        full = HexEscapeSubstrate.FULL_PAIR
        others = [
            s
            for s in decompose(substrate, DifferentialRoutingStructure)
            if s is not full
        ]
        self.assertIn(HexEscapeSubstrate.NECK_PAIR, others)
        for name, window in windows:
            with self.subTest(protocol=name):
                for structure in others:
                    impedance = ohm.m_from(structure.impedance, strict=False)
                    self.assertFalse(window.in_range(impedance), structure.name)
                if window.in_range(ohm.m_from(full.impedance, strict=False)):
                    found = substrate.differential_routing_structure(window)
                    self.assertIs(found, full)

    def test_neck_rule_outranks_the_net_rule_on_the_field_sections_only(self) -> None:
        self.assertGreater(self.c.neck_rule.priority, self.c.full_rule.priority)
        for net in self.c.nets:
            self.assertTrue(_tagged(net, SignalTag))
        for route in (*self.c.legs, *self.c.necks):
            self.assertTrue(_tagged(route, EscapeNeckTag))
        for route in (*self.c.fulls, *self.c.chip_legs):
            self.assertFalse(_tagged(route, EscapeNeckTag))


def _shape_widths(route: Route) -> list[float]:
    widths = []
    for trace in route.traces or []:
        for shape in trace.shapes:
            geometry = shape.geometry if isinstance(shape, Shape) else shape
            assert isinstance(geometry, ArcPolyline), type(geometry)
            widths.append(geometry.width)
    return widths


ARC_TOLERANCE = 1e-4
"""How far polygonized copper may stray from its arcs, in mm. The default of
0.01 mm narrows a measured gap on a bend by more than the 1 um this test
reads gaps to."""


def _copper(shape: Shape, placement: Transform | None = None) -> BaseGeometry:
    if placement is not None:
        shape = placement * shape
    return ShapelyGeometry.from_shape(shape, tolerance=ARC_TOLERANCE).g


def _legs(route: Route) -> list[BaseGeometry]:
    """One copper geometry per trace of ``route``: P then N for a pair."""
    return [
        shapely.union_all([_copper(s) for s in trace.shapes])
        for trace in route.traces or []
    ]


def _point_copper(point: PairPoint | PairInsertion) -> list[BaseGeometry]:
    """A control point's own copper, which joins the routes that meet at it,
    in the circuit's frame."""
    return [
        _copper(s, point.transform)
        for trace in point.traces or []
        for s in trace.shapes
    ]


@unittest.skipUnless(RUNTIME, "needs a JITX runtime")
class TestHexBgaEscapeRuntime(TestCase):
    root: ClassVar[HexBgaEscape]
    unmet: ClassVar[list[str]]
    complete: ClassVar[bool]
    ground_vias: ClassVar[list[tuple[float, float]]]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        with jitx.runtime as rt:
            design = rt.submit(hex_bga_escape_design)
            design.capture(wait=120)
            root = design.root.circuit
            assert isinstance(root, HexBgaEscape)
            cls.root = root
            report = design.issues(satisfied=True, wait=40)
            cls.complete = report.complete
            cls.unmet = [g.text for g in report.groups() if not g.satisfied]
            cls.ground_vias = []
            for trace, via in design.query(Via):
                if isinstance(via, HexEscapeSubstrate.GroundVia):
                    x, y = _xy(via)
                    if trace.transform is not None:
                        x, y = trace.transform * (x, y)
                    cls.ground_vias.append(_key((float(x), float(y))))

    def setUp(self) -> None:
        self.c = type(self).root
        substrate = HexEscapeSubstrate()
        self.fab = substrate.constraints
        self.full = _pair_layer(substrate.FULL_PAIR)
        self.neck = _pair_layer(substrate.NECK_PAIR)

    def _routes(self) -> list[Route]:
        return [*self.c.legs, *self.c.necks, *self.c.fulls, *self.c.chip_legs]

    def test_every_route_is_made_with_no_open_issue(self) -> None:
        self.assertTrue(self.complete, "issue report incomplete: raise wait")
        self.assertEqual(self.unmet, [])
        for route in self._routes():
            status = route.status
            assert status is not None
            self.assertTrue(status.routed)
            self.assertTrue(route.traces)

    def test_neck_through_the_field_full_pair_outside(self) -> None:
        for i, neck in enumerate(self.c.necks):
            with self.subTest(pair=i):
                for w in _shape_widths(neck):
                    self.assertAlmostEqual(w, self.neck.trace_width, places=4)
                p, n = _legs(neck)
                # The neck runs straight down its channel, so a horizontal
                # cut crosses each trace square: its width, then the gap.
                x, _ = _xy(self.c.transitions[i])
                _, top = _xy(self.c.insertions[i])
                y = top - 0.25
                while y > field_bottom():
                    cut = LineString([(x - 1, y), (x + 1, y)])
                    (pa, _, pb, _) = p.intersection(cut).bounds
                    (na, _, nb, _) = n.intersection(cut).bounds
                    self.assertAlmostEqual(pb - pa, self.neck.trace_width, places=3)
                    self.assertAlmostEqual(nb - na, self.neck.trace_width, places=3)
                    gap = max(pa, na) - min(pb, nb)
                    self.assertAlmostEqual(gap, self.neck.pair_spacing, places=3)
                    y -= 0.25
                for full in self.c.fulls[2 * i : 2 * i + 2]:
                    for w in _shape_widths(full):
                        self.assertAlmostEqual(w, self.full.trace_width, places=4)
                    fp, fn = _legs(full)
                    self.assertAlmostEqual(
                        fp.distance(fn), self.full.pair_spacing, places=3
                    )
                    self.assertLess(fp.union(fn).bounds[3], field_bottom())

    def test_width_changes_at_the_pair_point(self) -> None:
        # Sort the pair's route copper by the width it was drawn at: the
        # neck-width copper ends, and the full-width copper starts, within
        # TRANSITION_BAND of the PairPoint.
        for i, point in enumerate(self.c.transitions):
            with self.subTest(pair=i):
                _, y = _xy(point)
                routes = [
                    *self.c.legs[2 * i : 2 * i + 2],
                    self.c.necks[i],
                    *self.c.fulls[2 * i : 2 * i + 2],
                ]
                at_width: dict[float, list[BaseGeometry]] = {}
                for route in routes:
                    widths = set(_shape_widths(route))
                    self.assertEqual(
                        len(widths), 1, f"{route} drawn at widths {widths}"
                    )
                    (width,) = widths
                    at_width.setdefault(round(width, 4), []).extend(_legs(route))
                neck = shapely.union_all(at_width[round(self.neck.trace_width, 4)])
                full = shapely.union_all(at_width[round(self.full.trace_width, 4)])
                self.assertLessEqual(abs(neck.bounds[1] - y), TRANSITION_BAND)
                self.assertLessEqual(abs(full.bounds[3] - y), TRANSITION_BAND)

    def test_built_layout_has_a_ground_via_at_every_ground_ball(self) -> None:
        ground = type(self).ground_vias
        self.assertEqual(len(ground), len(set(ground)))
        self.assertEqual(set(ground), ground_balls())

    def test_signal_copper_keeps_the_fabrication_limits(self) -> None:
        radius = _pad_radius(HexEscapeSubstrate.GroundVia)
        ground = [
            Point(_xy(v)).buffer(radius, quad_segs=64) for v in self.c.ground_vias
        ]
        pairs = []
        for i in range(len(PAIR_BALLS)):
            routes = [
                *self.c.legs[2 * i : 2 * i + 2],
                self.c.necks[i],
                *self.c.fulls[2 * i : 2 * i + 2],
                *self.c.chip_legs[2 * i : 2 * i + 2],
            ]
            for route in routes:
                for w in _shape_widths(route):
                    self.assertGreaterEqual(w, self.fab.min_copper_width)
            points = [
                self.c.insertions[i],
                self.c.transitions[i],
                self.c.bends[i],
                self.c.chip_insertions[i],
            ]
            copper = [g for r in routes for g in _legs(r)]
            copper += [g for point in points for g in _point_copper(point)]
            pairs.append(shapely.union_all(copper))
        for i, copper in enumerate(pairs):
            with self.subTest(pair=i):
                gap = min(copper.distance(v) for v in ground)
                self.assertGreaterEqual(gap, self.fab.min_copper_copper_space)
        self.assertGreaterEqual(
            pairs[0].distance(pairs[1]), self.fab.min_copper_copper_space
        )

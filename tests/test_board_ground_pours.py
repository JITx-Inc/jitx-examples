"""Tests for the board ground pours pattern.

Expected values are worked out here from what the tests read: the copper
layer count from the substrate's stackup, the anchor's layer span and pad
from its via class, the board outline from the board, and the edge gap as
the larger of the substrate's ``min_copper_edge_space`` and the board-edge
rule's clearance. A pour with no copper of its own net inside it on its
layer comes back empty (layout-constraints spike, 2026-11-03), so every
pour needs an anchor that reaches its layer.

The runtime tests submit the design, capture it and measure each pour's
realized copper against the board outline. They need a JITX runtime started
from the repository root and ``JITX_PATTERN_RUNTIME=1``.
"""

from __future__ import annotations

import os
import shutil
import unittest
from pathlib import Path
from typing import ClassVar

import jitx
from jitx.copper import Pour
from jitx.shapes import Shape
from jitx.shapes.primitive import Empty
from jitx.shapes.shapely import ShapelyGeometry
from jitx.test import TestCase
from jitx.via import Via
from shapely.geometry import Point, Polygon
from shapely.geometry.base import BaseGeometry

from jitxexamples.patterns.board_ground_pours import (
    BoardGroundPours,
    board_ground_pours_design,
)

RUNTIME = os.environ.get("JITX_PATTERN_RUNTIME") == "1"

GAP_SLACK = 0.05
"""How far past the expected edge gap a pour may stop, in mm. The spike
measured pours 0.01 mm past the edge rule."""

ARC_TOLERANCE = 1e-4
"""How far a polygonized outline may stray from its arcs, in mm. The default
of 0.01 mm puts the board's 3 mm corners 0.009 mm inside their arcs, which
would hide a pour that crowds the corner by less than that."""


def _shapely(shape: Shape) -> BaseGeometry:
    return ShapelyGeometry.from_shape(shape, tolerance=ARC_TOLERANCE).g


def _xy(via: Via) -> tuple[float, float]:
    assert via.transform is not None
    x, y = via.transform.translation
    return float(x), float(y)


def _layer_span(via: Via, layers: int) -> range:
    start = via.start_layer % layers
    stop = via.stop_layer % layers
    return range(min(start, stop), max(start, stop) + 1)


class _Inputs:
    """The design's board, substrate, pours and edge gap."""

    def __init__(self) -> None:
        design = board_ground_pours_design()
        circuit = design.circuit
        assert isinstance(circuit, BoardGroundPours)
        self.c = circuit
        self.layers = len(design.substrate.stackup.conductors)
        board = _shapely(design.board.shape)
        assert isinstance(board, Polygon)
        self.board = board
        clearance = circuit.edge_rule.clearance_constraint
        assert clearance is not None
        self.edge_gap = max(
            design.substrate.constraints.min_copper_edge_space, clearance.clearance
        )
        diameter = circuit.gnd_anchor.diameter
        assert isinstance(diameter, float)
        self.anchor_radius = diameter / 2


class TestBoardGroundPours(TestCase):
    def setUp(self) -> None:
        self.i = _Inputs()

    def test_every_copper_layer_has_a_ground_pour(self) -> None:
        self.assertGreaterEqual(self.i.layers, 4)
        self.assertEqual(
            sorted(p.layer for p in self.i.c.pours), list(range(self.i.layers))
        )
        members = list(self.i.c.GND.connected)
        for pour in self.i.c.pours:
            self.assertIn(pour, members)

    def test_every_pour_has_an_anchor_on_its_layer_inside_its_copper(self) -> None:
        # Inside the board less the edge gap is inside the copper each pour
        # can realize, whatever its authored outline.
        anchor = self.i.c.gnd_anchor
        self.assertIn(anchor, list(self.i.c.GND.connected))
        pad = Point(_xy(anchor)).buffer(self.i.anchor_radius)
        span = _layer_span(anchor, self.i.layers)
        for pour in self.i.c.pours:
            with self.subTest(layer=pour.layer):
                self.assertIn(pour.layer, span)
                outline = pour.shape.to_shapely().g
                self.assertTrue(outline.contains(pad))
                self.assertTrue(self.i.board.buffer(-self.i.edge_gap).contains(pad))

    def test_the_anchor_via_meets_the_drill_and_annular_ring_floors(self) -> None:
        fab = board_ground_pours_design().substrate.constraints
        via = self.i.c.gnd_anchor
        ring = self.i.anchor_radius - via.hole_diameter / 2
        self.assertGreaterEqual(via.hole_diameter, fab.min_drill_diameter)
        self.assertGreaterEqual(ring, fab.min_annular_ring)

    def test_every_pour_reaches_past_the_board(self) -> None:
        # Drawn larger than the board, a pour's edge is the edge rule's,
        # not its own outline's.
        for pour in self.i.c.pours:
            self.assertTrue(pour.shape.to_shapely().g.contains(self.i.board))


@unittest.skipUnless(RUNTIME, "needs a JITX runtime")
class TestBoardGroundPoursRuntime(TestCase):
    pours: ClassVar[list[Pour]]
    unmet: ClassVar[list[str]]
    complete: ClassVar[bool]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        design = board_ground_pours_design
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
            rd.capture(wait=60)
            root = rd.root.circuit
            assert isinstance(root, BoardGroundPours)
            cls.pours = list(root.pours)
            report = rd.issues(satisfied=True, wait=30)
            cls.complete = report.complete
            cls.unmet = [g.text for g in report.groups() if not g.satisfied]

    def setUp(self) -> None:
        self.i = _Inputs()

    def test_no_open_issue(self) -> None:
        self.assertTrue(self.complete, "issue report incomplete: raise wait")
        self.assertEqual(self.unmet, [])

    def test_every_pour_comes_back_with_copper(self) -> None:
        self.assertEqual(len(self.pours), self.i.layers)
        for pour in self.pours:
            with self.subTest(layer=pour.layer):
                self.assertNotIsInstance(pour.shape, Empty)
                self.assertNotIsInstance(getattr(pour.shape, "geometry", None), Empty)
                self.assertGreater(pour.shape.to_shapely().g.area, 0.0)

    def test_every_pour_stops_the_edge_gap_from_the_board_edge(self) -> None:
        edge = self.i.board.exterior
        band = self.i.edge_gap + GAP_SLACK
        for pour in self.pours:
            with self.subTest(layer=pour.layer):
                copper = _shapely(pour.shape)
                self.assertTrue(self.i.board.contains(copper))
                # Both outlines are polygonized at ARC_TOLERANCE: the board's
                # corners sit up to that inside its arcs, and the pour's
                # chords up to half of it outside, toward the edge.
                self.assertGreaterEqual(
                    edge.distance(copper), self.i.edge_gap - 1.5 * ARC_TOLERANCE
                )
                # And no further back than the band: the pour fills the board
                # up to it.
                self.assertLess(
                    self.i.board.buffer(-band).difference(copper).area, 1e-3
                )

"""Tests for the board edge and cutout pattern.

The offline tests check what each rule is keyed on and that each widens the
fab floor it overrides. The runtime test, gated by ``JITX_PATTERN_RUNTIME=1``,
measures the computed pour's pullback from the outer edge, the outline slot,
the circuit cutout and another net's via drill. Its expected values are the
rule values with the offsets measured on jitx 4.6: the outer edge takes the
rule plus 0.01 mm, holes and cutouts the rule within a few microns.
"""

import os
import shutil
import unittest
from pathlib import Path

import jitx
import shapely
from jitx.constraints import AtomExpr, IsBoardEdge, IsHole
from jitx.test import TestCase
from shapely.geometry import Point, box

from jitxexamples.patterns.layout_edge_and_cutout import (
    EdgeAndCutout,
    layout_edge_and_cutout_design,
)

EDGE_OFFSET = 0.01
"""The outer edge pullback is the rule, or the fab floor, plus this (measured
on jitx 4.6)."""


class TestEdgeAndCutoutRules(TestCase):
    def setUp(self) -> None:
        self.design = layout_edge_and_cutout_design()
        circuit = self.design.circuit
        assert isinstance(circuit, EdgeAndCutout)
        self.circuit: EdgeAndCutout = circuit
        self.fab = self.design.substrate.constraints

    def test_rules_are_keyed_on_the_builtin_opening_tags(self) -> None:
        for rule, tag in (
            (self.circuit.edge_rule, IsBoardEdge),
            (self.circuit.hole_rule, IsHole),
        ):
            assert isinstance(rule.first, AtomExpr)
            self.assertIs(rule.first.atom, tag)

    def test_each_rule_widens_the_fab_floor(self) -> None:
        edge = self.circuit.edge_rule.clearance_constraint
        hole = self.circuit.hole_rule.clearance_constraint
        assert edge is not None and hole is not None
        self.assertGreater(edge.clearance, self.fab.min_copper_edge_space)
        self.assertGreater(hole.clearance, self.fab.min_copper_hole_space)


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestEdgeAndCutoutRuntime(TestCase):
    def test_pour_pulls_back_from_each_opening_by_its_rule(self) -> None:
        design = layout_edge_and_cutout_design
        root = Path(__file__).resolve().parents[1]
        shutil.rmtree(
            root / "designs" / f"{design.__module__}.{design.__qualname__}",
            ignore_errors=True,
        )
        with jitx.runtime as rt:
            rd = rt.submit(design)
            rd.capture(wait=30)
            circuit = rd.root.circuit
            assert isinstance(circuit, EdgeAndCutout)
            board = rd.root.board.shape.to_shapely().g
            pour = circuit.gnd_pour.shape.to_shapely().g
            cutout = circuit.cutout.shape.to_shapely().g
            via = circuit.other_via
            assert via.transform is not None
            drill = Point(via.transform.translation).buffer(
                via.hole_diameter / 2, quad_segs=64
            )
            anchor = circuit.gnd_anchor
            assert anchor.transform is not None
            anchor_drill = Point(anchor.transform.translation).buffer(
                anchor.hole_diameter / 2, quad_segs=64
            )
            edge_rule = circuit.edge_rule.clearance_constraint
            hole_rule = circuit.hole_rule.clearance_constraint
            assert edge_rule is not None and hole_rule is not None
            edge, hole = edge_rule.clearance, hole_rule.clearance

        outer = box(*board.bounds).exterior
        assert isinstance(board, shapely.Polygon)
        (slot,) = [shapely.Polygon(ring) for ring in board.interiors]
        for name, feature, expected in (
            ("outer edge", outer, edge + EDGE_OFFSET),
            ("outline slot", slot, hole),
            ("circuit cutout", cutout, hole),
            ("other net's via drill", drill, hole),
        ):
            with self.subTest(name):
                self.assertAlmostEqual(pour.distance(feature), expected, delta=0.005)
        # The hole rule acts between nets: the pour's own via stays joined,
        # though its drill is a hole as well.
        self.assertEqual(pour.distance(anchor_drill), 0)

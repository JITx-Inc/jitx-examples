"""Tests for the SI BGA optimization demo.

Nothing else in the suite imports ``jitxexamples.demos.*``, so without this the
demo package's imports are never exercised in CI and a bad move or a broken
relative import would go unnoticed. Every module in the package is imported
explicitly for that reason. The instantiation test then builds the design and
asserts on the per-lane structure.
"""

import unittest

from jitx.sample import SampleDesign
from jitx.test import TestCase

from jitxexamples.demos.si_bga_optimization import (
    bga_escape,
    constraints,
    deskew,
    generic_bga,
    si_geometry,
    substrate,
)


def _n_lanes() -> int:
    return sum(
        len(generic_bga.signal_cols_for_pair(i))
        for i in range(len(generic_bga.SIGNAL_ROW_PAIRS))
    )


class TestBGAOptimizationDemoImports(unittest.TestCase):
    def test_every_module_imports(self):
        for module in (
            bga_escape,
            constraints,
            deskew,
            generic_bga,
            si_geometry,
            substrate,
        ):
            self.assertTrue(module.__name__.startswith("jitxexamples.demos."))

    def test_build_target_is_a_sample_design(self):
        self.assertTrue(issubclass(bga_escape.bga_optimization_design, SampleDesign))

    def test_lane_geometry_constants_are_consistent(self):
        # The BGA's signal balls must fit inside the declared grid; this is the
        # invariant the escape lanes are derived from.
        signal_balls = 2 * _n_lanes()
        self.assertLess(signal_balls, generic_bga.BGA_ROWS * generic_bga.BGA_COLS)
        for top_row, bottom_row in generic_bga.SIGNAL_ROW_PAIRS:
            self.assertLess(top_row, bottom_row)
            self.assertLess(bottom_row, generic_bga.BGA_ROWS)


class TestBGAOptimizationDesign(TestCase):
    def test_design_instantiates_with_expected_lane_structure(self):
        design = bga_escape.bga_optimization_design()
        circuit = design.circuit
        assert isinstance(circuit, bga_escape.BGALink)
        n_lanes = _n_lanes()
        self.assertEqual(len(circuit.lanes), n_lanes)
        self.assertEqual(len(circuit.pair_points), n_lanes)
        self.assertEqual(len(circuit.pair_insertions), n_lanes)
        self.assertEqual(len(circuit.routes), n_lanes)
        # One pair-point and one insertion attachment per lane.
        self.assertEqual(len(circuit.control_attachments), 2 * n_lanes)
        # One deskew-copper virtual connection per diff-pair leg.
        self.assertEqual(len(circuit.virtual_connections), 2 * n_lanes)

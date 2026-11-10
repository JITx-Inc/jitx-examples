"""Tests for the Würth Elektronik 60312202114514 end launch.

Each expected value is worked out from the recommended land pattern in the
Würth datasheet drawing, revision 001.001
(https://www.we-online.com/components/products/datasheet/60312202114514.pdf),
retyped here from the drawing, not read from the module: a centre pad
0.61 mm wide and 1.97 mm long from the board end, and ground pads 9.9 mm
outer and 7.1 mm inner overall width and 5.0 mm long, on the top and on the
bottom. The frame (x = 0 at the board end, +x into the board) is the vendor
model's frame, which the module docstring states.
"""

from __future__ import annotations

from jitx.circuit import Circuit
from jitx.container import inline
from jitx.inspect import visit
from jitx.landpattern import Pad
from jitx.layerindex import Side
from jitx.placement import Placement
from jitx.sample import SampleDesign
from jitx.shapes import Shape
from jitx.test import TestCase
from shapely.geometry.base import BaseGeometry

from jitxexamples.components.connectors.wurth_elektronik_60312202114514 import (
    Device,
    Wurth60312202114514,
)

CENTER_PAD_WIDTH = 0.61
"""Datasheet: centre pad 0.61 +/-0.05 wide, in mm."""

CENTER_PAD_LENGTH = 1.97
"""Datasheet: centre pad 1.97 minimum from the PCB end, in mm."""

GROUND_OUTER = 9.9
"""Datasheet: ground pads 9.9 +/-0.05 outer overall width, in mm."""

GROUND_INNER = 7.1
"""Datasheet: ground pads 7.1 +/-0.05 inner overall width, in mm."""

GROUND_LENGTH = 5.0
"""Datasheet: ground pads 5.0 +/-0.05 long, top and bottom, in mm."""


class WurthLaunchDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        launch = Device()


def _copper(pad: Pad) -> BaseGeometry:
    assert pad.transform is not None
    shape = pad.shape if isinstance(pad.shape, Shape) else pad.shape.shape
    return (pad.transform * shape).to_shapely().g


def _side(pad: Pad) -> Side:
    return pad.transform.side if isinstance(pad.transform, Placement) else Side.Top


class TestWurth60312202114514(TestCase):
    def setUp(self) -> None:
        circuit = WurthLaunchDesign().circuit
        launch = circuit.launch
        assert isinstance(launch, Wurth60312202114514)
        self.launch = launch

    def test_centre_pad_runs_from_the_board_end_into_the_board(self) -> None:
        minx, miny, maxx, maxy = _copper(self.launch.landpattern.sig).bounds
        self.assertAlmostEqual(minx, 0.0, places=6)
        self.assertAlmostEqual(maxx - minx, CENTER_PAD_LENGTH, places=6)
        self.assertAlmostEqual(maxy - miny, CENTER_PAD_WIDTH, places=6)
        self.assertAlmostEqual((miny + maxy) / 2, 0.0, places=6)

    def test_ground_pads_on_each_side_match_the_overall_widths(self) -> None:
        pads = self.launch.landpattern.gnd
        for side in (Side.Top, Side.Bottom):
            with self.subTest(side=side):
                here = [p for p in pads if _side(p) == side]
                self.assertEqual(len(here), 2)
                bounds = sorted(_copper(p).bounds for p in here)
                for minx, _, maxx, _ in bounds:
                    # Measured from the board end, which is x = 0.
                    self.assertAlmostEqual(minx, 0.0, places=6)
                    self.assertAlmostEqual(maxx - minx, GROUND_LENGTH, places=6)
                (_, low_bottom, _, low_top), (_, high_bottom, _, high_top) = sorted(
                    bounds, key=lambda b: b[1]
                )
                self.assertAlmostEqual(high_top - low_bottom, GROUND_OUTER, places=6)
                self.assertAlmostEqual(high_bottom - low_top, GROUND_INNER, places=6)

    def test_land_pattern_has_one_centre_pad_and_four_ground_pads(self) -> None:
        pads = [pad for _, pad in visit(self.launch.landpattern, Pad)]
        self.assertEqual(len(pads), 5)

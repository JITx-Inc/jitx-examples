"""Tests for the BGA power escape pattern.

The expected values are worked out here from the placed BGA's ball pads and
the sample fab constraints, not read from the module's derivation: the room
beside the escape is the distance from a line running out of the power ball
in -x to the nearest other pad, and the floors come from
``SampleFabConstraints``. The rule values come from the translated design,
which is what the layout engine receives. With ``JITX_PATTERN_RUNTIME=1``
and a runtime started at the project root, the runtime test builds the
design and measures each segment's width and the escape copper's distance to
the other balls.
"""

from __future__ import annotations

import os
import shutil
import unittest
from pathlib import Path

import jitx

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_js1_hdi_stackup.py
# uses it for the same reason).
from jitx._translate.design import package_design
from jitx.circuit import Route
from jitx.inspect import visit
from jitx.landpattern import Pad, PadShape
from jitx.sample import SampleFabConstraints
from jitx.substrate import FabricationConstraints
from jitx.shapes.shapely import ShapelyGeometry
from jitx.test import TestCase
from jitx.transform import Transform
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from jitxexamples.demos.si_bga_optimization.generic_bga import HexBGA
from jitxexamples.patterns.layout_bga_escape import (
    BgaEscapeTag,
    BgaPowerEscape,
    PlaceholderHexBGA,
    PowerTag,
    derive_escape,
    layout_bga_escape_design,
)

FAB = SampleFabConstraints


def _name(tag: type) -> str:
    return f"{tag.__module__}.{tag.__qualname__}"


def _pad_copper(pad: Pad, frame: Transform | None = None) -> BaseGeometry:
    """The pad's copper in its landpattern's frame, or in ``frame`` above it.
    Circles are polygonized to 0.1 um so the polygon edge is not what the
    margins below measure."""
    shape = pad.shape
    if isinstance(shape, PadShape):
        shape = shape.shape
    assert pad.transform is not None
    placed = pad.transform * shape
    if frame is not None:
        placed = frame * placed
    return ShapelyGeometry.from_shape(placed, tolerance=1e-4).g


def _vdd_pad(circuit: BgaPowerEscape) -> Pad:
    """The pad the part maps its ``VDD`` port to."""
    (mapping,) = circuit.u1.mappings
    pad = mapping[circuit.u1.VDD]
    assert isinstance(pad, Pad)
    return pad


class _FineFab(FabricationConstraints):
    """Floors low enough for the skill's worked example: 0.1 spacing."""

    min_copper_width = 0.1
    min_copper_copper_space = 0.1
    min_copper_hole_space = 0.2
    min_copper_edge_space = 0.3
    min_annular_ring = 0.125
    min_drill_diameter = 0.2
    min_hole_to_hole = 0.25


class TestDeriveEscapeWorkedExample(TestCase):
    def _landpattern(self) -> HexBGA:
        circuit = layout_bga_escape_design().circuit
        assert isinstance(circuit, BgaPowerEscape)
        assert isinstance(circuit.u1, PlaceholderHexBGA)
        lp = circuit.u1.landpattern
        assert isinstance(lp, HexBGA)
        return lp

    def test_hex_grid_escape_matches_the_skill_example(self) -> None:
        # The layout-constraints skill works this geometry by hand: 1.0
        # pitch, 0.5 balls, a 0.5 channel and c 0.25, so the escape is 0.3
        # at s_e 0.1 and 0.26 at s_e 0.12. The flanking balls sit at
        # (-0.866, +-0.5), 0.5 off the escape's axis less the 0.25 radius.
        lp = self._landpattern()
        target = lp.get_pad(1, 2)
        for s_e, width in ((0.1, 0.3), (0.12, 0.26)):
            escape = derive_escape(
                lp, target, (-1.0, 0.0), _FineFab(), escape_clearance=s_e
            )
            self.assertAlmostEqual(escape.channel_clearance, 0.25, places=4)
            self.assertAlmostEqual(escape.width, width)

    def test_refuses_an_escape_clearance_below_the_fab_spacing(self) -> None:
        lp = self._landpattern()
        with self.assertRaisesRegex(ValueError, "below min_copper_copper_space"):
            derive_escape(
                lp, lp.get_pad(1, 2), (-1.0, 0.0), FAB(), escape_clearance=0.1
            )


class _Expected:
    """Ball geometry read from the placed BGA, and the rules as translated."""

    def __init__(self) -> None:
        design = layout_bga_escape_design()
        circuit = design.circuit
        assert isinstance(circuit, BgaPowerEscape)
        pads = [p for _, p in visit(circuit.u1.landpattern, Pad)]
        self.pad_count = len(pads)
        target = _vdd_pad(circuit)
        ball = _pad_copper(target)
        cx, cy = ball.centroid.x, ball.centroid.y
        # A line out of the ball in -x, well past the package.
        line = LineString([(cx, cy), (cx - 10.0, cy)])
        self.room = min(line.distance(_pad_copper(p)) for p in pads if p is not target)
        self.widths: dict[str, tuple[int, float]] = {}
        v1 = package_design(design).v1
        for rule in v1.design_rules:
            (effect,) = rule.effects
            if effect.HasField("trace_width"):
                (cond,) = rule.conditions
                self.widths[cond.atom_expr.atom.user.name] = (
                    rule.priority,
                    effect.trace_width.width,
                )
        top = next(m for m in v1.modules if m.id == v1.module)
        self.tagged: dict[str, set[tuple[int, ...]]] = {}
        for apply in top.apply_tags:
            for tag in apply.tags:
                self.tagged.setdefault(tag.name, set()).add(tuple(apply.local.path))
        self.vdd = next(n.id for n in top.nets if n.name == "VDD")


class TestBgaEscapeOffline(TestCase):
    def setUp(self) -> None:
        self.e = _Expected()

    def test_class_width_breaks_the_fab_floor_between_the_balls(self) -> None:
        _, class_width = self.e.widths[_name(PowerTag)]
        self.assertLess(self.e.room - class_width / 2, FAB.min_copper_copper_space)

    def test_escape_width_clears_the_balls_and_meets_the_floor(self) -> None:
        _, width = self.e.widths[_name(BgaEscapeTag)]
        self.assertGreaterEqual(self.e.room - width / 2, FAB.min_copper_copper_space)
        self.assertGreaterEqual(width, FAB.min_copper_width)

    def test_escape_rule_outranks_the_class_rule(self) -> None:
        class_priority, _ = self.e.widths[_name(PowerTag)]
        escape_priority, _ = self.e.widths[_name(BgaEscapeTag)]
        self.assertGreater(escape_priority, class_priority)

    def test_tags_sit_on_the_net_and_on_the_escape_route(self) -> None:
        self.assertEqual(self.e.tagged[_name(PowerTag)], {(self.e.vdd,)})
        (path,) = self.e.tagged[_name(BgaEscapeTag)]
        self.assertNotEqual(path, (self.e.vdd,))
        circuit = layout_bga_escape_design().circuit
        assert isinstance(circuit, BgaPowerEscape)
        self.assertIs(circuit.escape.destination, circuit.u1.VDD)


def _widths(route: Route) -> set[float]:
    return {
        round(s.geometry.width, 4)
        for t in route.traces or []
        for s in t.shapes
        if hasattr(s.geometry, "width")
    }


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestBgaEscapeRuntime(TestCase):
    def test_segments_take_their_widths_and_the_escape_clears_the_balls(
        self,
    ) -> None:
        design = layout_bga_escape_design
        e = _Expected()
        # A changed design aborts a headless submit at "stabilization" unless
        # its stored state is removed first (seen on jitx 4.6).
        root = Path(__file__).resolve().parents[1]
        shutil.rmtree(
            root / "designs" / f"{design.__module__}.{design.__qualname__}",
            ignore_errors=True,
        )
        with jitx.runtime as r:
            rd = r.submit(design)
            rd.capture(wait=40)
            issues = rd.issues(satisfied=True, wait=30).text()
        # The docstring's "issues listed routing as satisfied".
        self.assertIn("Routing:\n  - Satisfied", issues)
        circuit = rd.root.circuit
        assert isinstance(circuit, BgaPowerEscape)
        self.assertEqual(_widths(circuit.trunk), {e.widths[_name(PowerTag)][1]})
        self.assertEqual(_widths(circuit.escape), {e.widths[_name(BgaEscapeTag)][1]})

        escape = unary_union(
            [s.to_shapely().g for t in circuit.escape.traces or [] for s in t.shapes]
        )
        target = _vdd_pad(circuit)
        others = 0
        for trace, pad in visit(circuit.u1, Pad):
            if pad is target:
                continue
            placed = _pad_copper(pad, trace.transform)
            self.assertGreaterEqual(
                escape.distance(placed), FAB.min_copper_copper_space
            )
            others += 1
        # Every ball of the landpattern came back placed.
        self.assertEqual(others, e.pad_count - 1)

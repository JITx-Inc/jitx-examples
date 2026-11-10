"""Tests for the QFN power escape pattern.

The expected values are worked out here from the placed QFN's pad copper and
the sample fab constraints, not read from the module's derivation: the pad
width and the gap to the next pad come from the pad shapes, and the fab
floors from ``SampleFabConstraints``. The rule values come from the
translated design, which is what the layout engine receives. With
``JITX_PATTERN_RUNTIME=1`` and a runtime started at the project root, the
runtime test builds the design and measures each segment's width and the
escape copper's distance to the other QFN pads.
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
from jitx.test import TestCase
from jitx.transform import Transform
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from jitxexamples.patterns.layout_qfn_escape import (
    PowerTag,
    QfnEscapeTag,
    QfnPowerEscape,
    derive_escape,
    escape_width,
    layout_qfn_escape_design,
)

FAB = SampleFabConstraints


def _name(tag: type) -> str:
    return f"{tag.__module__}.{tag.__qualname__}"


def _pad_copper(pad: Pad, frame: Transform | None = None) -> BaseGeometry:
    """The pad's copper in its landpattern's frame, or in ``frame`` above it."""
    shape = pad.shape
    if isinstance(shape, PadShape):
        shape = shape.shape
    assert pad.transform is not None
    placed = pad.transform * shape
    return (placed if frame is None else frame * placed).to_shapely().g


class _Expected:
    """Pad geometry read from the placed QFN, and the rules as translated."""

    def __init__(self) -> None:
        design = layout_qfn_escape_design()
        circuit = design.circuit
        assert isinstance(circuit, QfnPowerEscape)
        pads = [p for _, p in visit(circuit.u1.landpattern, Pad)]
        target = circuit.u1.landpattern.p[1]
        self.target = _pad_copper(target)
        others = [_pad_copper(p) for p in pads if p is not target]
        self.pad_count = len(pads)
        self.gap = min(self.target.distance(g) for g in others)
        # Across the escape: the pad's short side (the escape runs along the
        # long side, out of the body).
        minx, miny, maxx, maxy = self.target.bounds
        self.pad_width = min(maxx - minx, maxy - miny)
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


class _FineFab(FabricationConstraints):
    """Floors low enough for the skill's worked BGA example: 0.1 spacing."""

    min_copper_width = 0.1
    min_copper_copper_space = 0.1
    min_copper_hole_space = 0.2
    min_copper_edge_space = 0.3
    min_annular_ring = 0.125
    min_drill_diameter = 0.2
    min_hole_to_hole = 0.25


class TestEscapeWidth(unittest.TestCase):
    def test_the_neighbouring_pads_bound_the_width(self) -> None:
        # The layout-constraints skill's worked BGA example: 1.0 pitch, 0.5
        # balls, so the channel is 0.5 and c 0.25; the escape is at most
        # 2 * (0.25 - 0.1) = 0.3 at s_e 0.1 and 2 * (0.25 - 0.12) = 0.26 at
        # s_e 0.12.
        self.assertAlmostEqual(escape_width(0.5, 0.25, 0.1, _FineFab()), 0.3)
        self.assertAlmostEqual(escape_width(0.5, 0.25, 0.12, _FineFab()), 0.26)

    def test_the_width_is_strictly_below_the_pad(self) -> None:
        # Far neighbours leave the pad as the only bound.
        self.assertLess(escape_width(0.3, 10.0, 0.1, _FineFab()), 0.3)

    def test_refuses_an_escape_clearance_below_the_fab_spacing(self) -> None:
        with self.assertRaisesRegex(ValueError, "below min_copper_copper_space"):
            escape_width(0.5, 0.25, 0.1, FAB())

    def test_refuses_a_width_below_the_fab_minimum(self) -> None:
        # 2 * (0.25 - 0.2) = 0.1, under the sample floor of 0.127.
        with self.assertRaisesRegex(ValueError, "below min_copper_width"):
            escape_width(0.5, 0.25, 0.2, FAB())


class TestQfnEscapeOffline(TestCase):
    def setUp(self) -> None:
        self.e = _Expected()

    def test_class_width_breaks_the_fab_floor_at_the_pad(self) -> None:
        # A trace centred on the pad clears the next pad by
        # gap + pad_width/2 - width/2.
        _, class_width = self.e.widths[_name(PowerTag)]
        reach = self.e.gap + self.e.pad_width / 2
        self.assertLess(reach - class_width / 2, FAB.min_copper_copper_space)

    def test_escape_width_fits_inside_the_pad_and_above_the_floor(self) -> None:
        self.assertGreaterEqual(self.e.gap, FAB.min_copper_copper_space)
        _, width = self.e.widths[_name(QfnEscapeTag)]
        self.assertLess(width, self.e.pad_width)
        self.assertGreaterEqual(width, FAB.min_copper_width)

    def test_c_is_half_the_pad_plus_the_gap_and_bounds_a_wide_clearance(
        self,
    ) -> None:
        # The escape leaves pad 1 along its long axis, so the nearest other
        # pad to its centreline is the adjacent one: c = pad/2 + gap. At the
        # fab floor the pad bound decides; at s_e 0.35 the neighbours do,
        # 2 * (c - 0.35) rounded down to 0.01.
        circuit = layout_qfn_escape_design().circuit
        assert isinstance(circuit, QfnPowerEscape)
        lp = circuit.u1.landpattern
        target = lp.p[1]
        c = self.e.pad_width / 2 + self.e.gap
        wide = derive_escape(lp, target, FAB(), escape_clearance=0.35)
        self.assertAlmostEqual(wide.centreline_clearance, c, places=6)
        self.assertAlmostEqual(wide.width, int(200 * (c - 0.35) + 1e-9) / 100)
        # The escape's centreline runs out of the pad to the transition and
        # passes no pad closer than c.
        centreline = LineString([wide.pad_center, wide.transition])
        others = [_pad_copper(p) for _, p in visit(lp, Pad) if p is not target]
        self.assertAlmostEqual(min(centreline.distance(g) for g in others), c, places=6)

    def test_escape_rule_outranks_the_class_rule(self) -> None:
        class_priority, _ = self.e.widths[_name(PowerTag)]
        escape_priority, _ = self.e.widths[_name(QfnEscapeTag)]
        self.assertGreater(escape_priority, class_priority)

    def test_tags_sit_on_the_net_and_on_the_escape_route(self) -> None:
        self.assertEqual(self.e.tagged[_name(PowerTag)], {(self.e.vdd,)})
        (path,) = self.e.tagged[_name(QfnEscapeTag)]
        self.assertNotEqual(path, (self.e.vdd,))
        circuit = layout_qfn_escape_design().circuit
        assert isinstance(circuit, QfnPowerEscape)
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
class TestQfnEscapeRuntime(TestCase):
    def test_segments_take_their_widths_and_the_escape_clears_the_pads(self) -> None:
        design = layout_qfn_escape_design
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
        assert isinstance(circuit, QfnPowerEscape)
        self.assertEqual(_widths(circuit.trunk), {e.widths[_name(PowerTag)][1]})
        self.assertEqual(_widths(circuit.escape), {e.widths[_name(QfnEscapeTag)][1]})

        escape = unary_union(
            [s.to_shapely().g for t in circuit.escape.traces or [] for s in t.shapes]
        )
        target = circuit.u1.landpattern.p[1]
        others = 0
        for trace, pad in visit(circuit.u1, Pad):
            if pad is target:
                continue
            placed = _pad_copper(pad, trace.transform)
            # Narrower than the pad and straight out of it, the escape is no
            # closer to a neighbour than the pads are to each other.
            self.assertGreaterEqual(escape.distance(placed), e.gap - 1e-4)
            others += 1
        # Every pad of the landpattern came back placed.
        self.assertEqual(others, e.pad_count - 1)

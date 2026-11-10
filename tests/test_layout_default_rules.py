"""Tests for the default rules pattern.

The offline tests check the rules against the substrate's fab floors, the
tag rules' priority over the defaults, and the default pad relief. The
runtime test, gated by ``JITX_PATTERN_RUNTIME=1``, measures the realized trace
widths, the pour's pullback from each route, and the relief around each GND
pad. Its expected values are the rule values read from the design, with the
0.01 mm trace pullback offset measured on jitx 4.6.
"""

import os
import shutil
import unittest
from pathlib import Path
from typing import Any

import jitx
import shapely
from jitx.constraints import (
    AtomExpr,
    BinaryDesignConstraint,
    BoolExpr,
    IsPad,
    IsTrace,
    OrExpr,
    Tag,
    Tags,
    UnaryDesignConstraint,
)
from jitx.inspect import visit
from jitx.landpattern import Pad, PadShape
from jitx.test import TestCase
from shapely.geometry.base import BaseGeometry

from jitxexamples.patterns.layout_default_rules import (
    DefaultRulesCircuit,
    GroundTag,
    PowerTag,
    check_against_fab,
    layout_default_rules_design,
)


def _atoms(expr: BoolExpr) -> list[Tag]:
    if isinstance(expr, AtomExpr):
        return [expr.atom]
    if isinstance(expr, OrExpr):
        return _atoms(expr.left) + _atoms(expr.right)
    return []


def _unary(rules: list[Any], tag: Tag | type[Tag]) -> UnaryDesignConstraint:
    """The one unary rule whose condition names ``tag`` (a builtin or a class)."""
    found = [
        r
        for r in rules
        if isinstance(r, UnaryDesignConstraint)
        and any(
            t is tag or (isinstance(tag, type) and isinstance(t, tag))
            for t in _atoms(r.condition)
        )
    ]
    (rule,) = found
    return rule


def _relief(pour: BaseGeometry, pad: BaseGeometry) -> tuple[int, float, list[float]]:
    """Voids touching the pad, the widest void gap, and the spoke widths
    crossing a ring 0.02 mm outside the pad."""
    ring = pad.buffer(2.0, join_style="mitre").difference(pad).difference(pour)
    voids = [
        v
        for v in getattr(ring, "geoms", [ring])
        if v.area > 1e-4 and v.distance(pad) < 1e-3
    ]
    gap = max(
        (
            max(pad.distance(shapely.Point(xy)) for xy in v.exterior.coords)
            for v in voids
        ),
        default=0.0,
    )
    cross = pad.buffer(0.02, join_style="mitre").exterior.intersection(pour)
    spokes = [g.length for g in getattr(cross, "geoms", [cross]) if g.length > 1e-4]
    return len(voids), gap, spokes


class TestDefaultRules(TestCase):
    def setUp(self) -> None:
        self.design = layout_default_rules_design()
        self.rules = list(self.design.rules)
        self.fab = self.design.substrate.constraints

    def test_rules_stay_on_or_above_the_fab_floors(self) -> None:
        for rule in self.rules:
            with self.subTest(rule=repr(rule)):
                if (
                    isinstance(rule, BinaryDesignConstraint)
                    and rule.clearance_constraint
                ):
                    self.assertGreaterEqual(
                        rule.clearance_constraint.clearance,
                        self.fab.min_copper_copper_space,
                    )
                if isinstance(rule, UnaryDesignConstraint):
                    if rule.trace_width_constraint:
                        self.assertGreaterEqual(
                            rule.trace_width_constraint.width, self.fab.min_copper_width
                        )
                    if relief := rule.thermal_relief_constraint:
                        self.assertGreaterEqual(
                            relief.gap_distance, self.fab.min_copper_copper_space
                        )
                        self.assertGreaterEqual(
                            relief.spoke_width, self.fab.min_copper_width
                        )

    def test_check_against_fab_refuses_a_width_under_the_floor(self) -> None:
        narrow = UnaryDesignConstraint(IsTrace).trace_width(
            self.fab.min_copper_width / 2
        )
        with self.assertRaisesRegex(ValueError, "trace width .* under the fab floor"):
            check_against_fab([narrow], self.fab)

    def test_tag_rules_outrank_the_defaults(self) -> None:
        default = _unary(self.rules, IsTrace)
        power = _unary(self.rules, PowerTag)
        self.assertIs(power, _unary(self.rules, GroundTag))
        self.assertGreater(power.priority, default.priority)
        assert power.trace_width_constraint and default.trace_width_constraint
        self.assertGreater(
            power.trace_width_constraint.width, default.trace_width_constraint.width
        )

    def test_every_pad_gets_a_relief_and_the_tags_sit_on_nets(self) -> None:
        # A pad no relief rule matches is fully joined to its pour (measured
        # on jitx 4.6), so the IsPad rule must exist.
        relief = _unary(self.rules, IsPad).thermal_relief_constraint
        assert relief is not None
        self.assertGreaterEqual(relief.num_spokes, 2)
        circuit = self.design.circuit
        assert isinstance(circuit, DefaultRulesCircuit)
        for net, tag in ((circuit.VCC, PowerTag), (circuit.GND, GroundTag)):
            tags = Tags.get(net)
            assert tags is not None
            self.assertTrue(any(isinstance(t, tag) for t in tags.tags))


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestDefaultRulesRuntime(TestCase):
    def test_widths_pullbacks_and_pad_relief(self) -> None:
        design = layout_default_rules_design
        root = Path(__file__).resolve().parents[1]
        shutil.rmtree(
            root / "designs" / f"{design.__module__}.{design.__qualname__}",
            ignore_errors=True,
        )
        with jitx.runtime as rt:
            rd = rt.submit(design)
            rd.capture(wait=30)
            circuit = rd.root.circuit
            assert isinstance(circuit, DefaultRulesCircuit)
            rules = list(rd.root.rules)
            pour = circuit.gnd_pour.shape.to_shapely().g
            routes = {}
            for name in ("vcc_route", "sig_route"):
                shapes = [s for t in getattr(circuit, name).traces for s in t.shapes]
                routes[name] = (
                    [s.geometry.width for s in shapes],
                    shapely.union_all([s.to_shapely().g for s in shapes]),
                )
            pads = []
            for trace, pad in visit(rd.root, Pad):
                if trace.transform is None or pad.transform is None:
                    continue
                if "gnd_part" not in str(trace.path):
                    continue
                shape = (
                    pad.shape.shape if isinstance(pad.shape, PadShape) else pad.shape
                )
                pads.append(((trace.transform * pad.transform) * shape).to_shapely().g)

        default_width = _unary(rules, IsTrace).trace_width_constraint
        power = _unary(rules, PowerTag)
        relief = _unary(rules, IsPad).thermal_relief_constraint
        clearances = {
            isinstance(r.first, AtomExpr) and isinstance(r.first.atom, PowerTag): (
                r.clearance_constraint.clearance
            )
            for r in rules
            if isinstance(r, BinaryDesignConstraint) and r.clearance_constraint
        }
        assert default_width and power.trace_width_constraint and relief
        for name, want_width, want_gap in (
            ("sig_route", default_width.width, clearances[False]),
            ("vcc_route", power.trace_width_constraint.width, clearances[True]),
        ):
            widths, copper = routes[name]
            with self.subTest(name):
                self.assertEqual(len(widths), 1)
                self.assertAlmostEqual(widths[0], want_width, delta=0.005)
                self.assertAlmostEqual(
                    pour.distance(copper), want_gap + 0.01, delta=0.005
                )
        self.assertEqual(len(pads), 2)
        for pad in pads:
            voids, gap, spokes = _relief(pour, pad)
            with self.subTest("GND pad relief"):
                self.assertEqual(voids, relief.num_spokes)
                self.assertAlmostEqual(gap, relief.gap_distance, delta=0.005)
                self.assertEqual(len(spokes), relief.num_spokes)
                for spoke in spokes:
                    self.assertAlmostEqual(spoke, relief.spoke_width, delta=0.005)

"""Tests for the sensitive-net clearance pattern.

Offline, the tests read the translated design: one clearance rule with two
conditions, the RF tag on the RF net and the noisy tag on the switch-node
net. With ``JITX_PATTERN_RUNTIME=1`` and a runtime started at the project
root, the runtime test builds the design and measures how far each pour
pulls back from the RF line. The expected pullbacks were measured on jitx
4.6 with other designs: a pour stands a trace's clearance plus 0.01 mm from
the trace (0.51 under a 0.5 rule), and 0.137 mm from a trace with no
clearance rule.
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
from jitx.copper import Pour
from jitx.test import TestCase
from shapely.geometry import LineString, MultiLineString
from shapely.ops import unary_union

from jitxexamples.patterns.layout_sensitive_net_clearance import (
    NoisyTag,
    RFNearSwitchNode,
    RFTag,
    layout_sensitive_net_clearance_design,
)

POUR_OFFSET = 0.01
"""A pour stands this much further from a trace than the winning clearance
(measured on jitx 4.6)."""

UNRULED_PULLBACK = 0.137
"""The pullback from a trace with no clearance rule (measured on jitx 4.6)."""


def _name(tag: type) -> str:
    return f"{tag.__module__}.{tag.__qualname__}"


class _Rules:
    """The clearance rules and tag placements the layout engine receives."""

    def __init__(self) -> None:
        v1 = package_design(layout_sensitive_net_clearance_design()).v1
        self.clearances: list[tuple[list[str], float]] = []
        for rule in v1.design_rules:
            (effect,) = rule.effects
            if effect.HasField("clearance"):
                names = [
                    c.atom_expr.atom.user.name if c.HasField("atom_expr") else "<any>"
                    for c in rule.conditions
                ]
                self.clearances.append((names, effect.clearance.clearance))
        top = next(m for m in v1.modules if m.id == v1.module)
        self.tagged: dict[str, set[tuple[int, ...]]] = {}
        for apply in top.apply_tags:
            for tag in apply.tags:
                self.tagged.setdefault(tag.name, set()).add(tuple(apply.local.path))
        self.nets = {n.name: n.id for n in top.nets if n.name}

    def rf_to_noisy(self) -> float:
        (value,) = (
            v
            for names, v in self.clearances
            if sorted(names) == sorted([_name(RFTag), _name(NoisyTag)])
        )
        return value


class TestSensitiveNetClearanceOffline(TestCase):
    def setUp(self) -> None:
        self.rules = _Rules()

    def test_the_only_clearance_rule_names_both_tags(self) -> None:
        # One rule, two tag conditions: nothing pushes the RF line away from
        # every object.
        self.assertEqual(len(self.rules.clearances), 1)
        self.assertGreater(self.rules.rf_to_noisy(), UNRULED_PULLBACK)

    def test_tags_sit_on_the_rf_and_switch_node_nets(self) -> None:
        self.assertEqual(self.rules.tagged[_name(RFTag)], {(self.rules.nets["RF"],)})
        self.assertEqual(self.rules.tagged[_name(NoisyTag)], {(self.rules.nets["SW"],)})


def _cut(pour: Pour, x: float) -> list[LineString]:
    """The pour's copper along a vertical line at ``x``, one span per piece."""
    g = pour.shape.to_shapely().g
    cut = LineString([(x, -50.0), (x, 50.0)]).intersection(g)
    if isinstance(cut, MultiLineString):
        return list(cut.geoms)
    assert isinstance(cut, LineString)
    return [cut] if not cut.is_empty else []


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestSensitiveNetClearanceRuntime(TestCase):
    def test_switch_node_pour_pulls_back_by_the_rule_and_gnd_does_not(
        self,
    ) -> None:
        design = layout_sensitive_net_clearance_design
        rules = _Rules()
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
        c = rd.root.circuit
        assert isinstance(c, RFNearSwitchNode)
        rf = unary_union(
            [s.to_shapely().g for t in c.route.traces or [] for s in t.shapes]
        )
        _, ymin, _, ymax = rf.bounds
        expected = {
            "sw_pour": rules.rf_to_noisy() + POUR_OFFSET,
            "gnd_pour": UNRULED_PULLBACK,
        }
        for name, gap in expected.items():
            pour = getattr(c, name)
            assert isinstance(pour, Pour)
            # Cut across the pour where the line runs through its middle.
            g = pour.shape.to_shapely().g
            x = g.centroid.x
            spans = _cut(pour, x)
            # Copper on both sides of the line: both halves survived.
            self.assertEqual(len(spans), 2, name)
            above = min(min(p[1] for p in s.coords) for s in spans if s.bounds[1] > 0)
            below = max(max(p[1] for p in s.coords) for s in spans if s.bounds[3] < 0)
            self.assertAlmostEqual(above - ymax, gap, delta=1e-3, msg=name)
            self.assertAlmostEqual(ymin - below, gap, delta=1e-3, msg=name)

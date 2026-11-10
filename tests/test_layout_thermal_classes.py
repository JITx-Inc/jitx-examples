"""Tests for the thermal relief classes pattern.

The offline tests check that each pad's class tag follows its measured size,
that each class's spokes fit its pads, that the direct connect outranks the
classes, and that no relief rule can match the untagged part's pads: every
relief rule is keyed on one user tag, never a builtin such as ``IsPad``, and
none of those tags sits on the untagged part's pads, landpattern, component,
net or the pour. The runtime test, gated by ``JITX_PATTERN_RUNTIME=1``, reads
the void gap, spoke widths and spoke count around every pad from the computed
pour, and expects the values of the rule that tags the pad, or a solid join
where no rule matches (measured on jitx 4.6).
"""

import os
import shutil
import unittest
from pathlib import Path
from typing import Any

import jitx
import shapely
from jitx.constraints import AtomExpr, BuiltinTag, Tag, Tags, UnaryDesignConstraint
from jitx.copper import Pour
from jitx.inspect import extract, visit
from jitx.landpattern import Pad, PadShape
from jitx.net import Net
from jitx.test import TestCase
from shapely.geometry.base import BaseGeometry

from jitxexamples.patterns.layout_thermal_classes import (
    ThermalClasses,
    DirectConnectTag,
    SMALL_PAD_LIMIT,
    LargePadRelief,
    SmallPadRelief,
    layout_thermal_classes_design,
)


def _tag_types(obj: object) -> set[type]:
    tags = Tags.get(obj)
    return {type(t) for t in tags.tags} if tags else set()


def _relief_rules(
    rules: list[Any],
) -> dict[BuiltinTag | type[Tag], UnaryDesignConstraint]:
    """Relief rules keyed by the tag class their single-tag condition names."""
    out: dict[BuiltinTag | type[Tag], UnaryDesignConstraint] = {}
    for rule in rules:
        if isinstance(rule, UnaryDesignConstraint) and rule.thermal_relief_constraint:
            assert isinstance(rule.condition, AtomExpr)
            atom = rule.condition.atom
            out[atom if isinstance(atom, BuiltinTag) else type(atom)] = rule
    return out


def _pad_box(pad: Pad) -> tuple[float, float]:
    shape = pad.shape.shape if isinstance(pad.shape, PadShape) else pad.shape
    x0, y0, x1, y1 = shape.to_shapely().g.bounds
    return x1 - x0, y1 - y0


def _relief(
    pour: BaseGeometry, pad: BaseGeometry
) -> tuple[int, float, list[float], float]:
    """Voids touching the pad, the widest void gap, the spoke widths crossing
    a ring 0.02 mm outside the pad, and that ring's length."""
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
    outside = pad.buffer(0.02, join_style="mitre").exterior
    cross = outside.intersection(pour)
    spokes = [g.length for g in getattr(cross, "geoms", [cross]) if g.length > 1e-4]
    return len(voids), gap, spokes, outside.length


def _winning_rule(
    tags: set[type], rules: dict[BuiltinTag | type[Tag], UnaryDesignConstraint]
) -> UnaryDesignConstraint:
    return max((rules[t] for t in tags if t in rules), key=lambda r: r.priority)


class TestThermalClassRules(TestCase):
    def setUp(self) -> None:
        self.design = layout_thermal_classes_design()
        circuit = self.design.circuit
        assert isinstance(circuit, ThermalClasses)
        self.circuit: ThermalClasses = circuit
        self.rules = _relief_rules(list(self.circuit.rules))
        self.untagged = {id(pad) for _, pad in visit(self.circuit.untagged, Pad)}
        self.pads = [
            pad for _, pad in visit(self.circuit, Pad) if id(pad) not in self.untagged
        ]

    def test_class_tag_follows_the_measured_pad(self) -> None:
        small, large = (
            self.rules[SmallPadRelief].thermal_relief_constraint,
            self.rules[LargePadRelief].thermal_relief_constraint,
        )
        assert small and large
        self.assertTrue(self.pads)
        for pad in self.pads:
            tags = _tag_types(pad)
            narrow = min(_pad_box(pad))
            with self.subTest(narrow=narrow):
                # The module's stated rule: small below the limit, large from
                # it up; and each class's spokes no wider than its pads.
                if narrow < SMALL_PAD_LIMIT:
                    self.assertIn(SmallPadRelief, tags)
                    self.assertNotIn(LargePadRelief, tags)
                    self.assertLessEqual(small.spoke_width, narrow)
                else:
                    self.assertIn(LargePadRelief, tags)
                    self.assertNotIn(SmallPadRelief, tags)
                    self.assertLessEqual(large.spoke_width, narrow)

    def test_direct_connect_closes_the_relief_on_its_pad(self) -> None:
        rule = self.rules[DirectConnectTag]
        relief = rule.thermal_relief_constraint
        assert relief is not None
        (pad,) = [p for p in self.pads if DirectConnectTag in _tag_types(p)]
        width, height = _pad_box(pad)
        # Spokes as wide as the pad's diagonal overlap into solid copper.
        self.assertGreaterEqual(relief.spoke_width, (width**2 + height**2) ** 0.5)
        # The higher priority wins where two relief rules match (measured on
        # jitx 4.6).
        others = [
            r.priority for t, r in self.rules.items() if t is not DirectConnectTag
        ]
        self.assertGreater(rule.priority, max(others))

    def test_no_relief_rule_reaches_the_untagged_part(self) -> None:
        # The untagged part shows the solid join a pad gets with no relief
        # rule, so no relief rule may match its pads. Every relief rule must
        # be keyed on one user tag (a builtin such as IsPad or IsCopper would
        # reach the untagged pads too), and none of those tags may sit on the
        # untagged part, its landpattern, its pads, its net or the pour: a
        # tag on a net reaches every pad on the net.
        relief_tags: set[type] = set()
        for rule in extract(self.design, UnaryDesignConstraint):
            if not rule.thermal_relief_constraint:
                continue
            condition = rule.condition
            self.assertIsInstance(condition, AtomExpr, f"{rule}")
            assert isinstance(condition, AtomExpr)
            self.assertNotIsInstance(condition.atom, BuiltinTag, f"{rule}")
            relief_tags.add(type(condition.atom))
        self.assertTrue(relief_tags)
        part = self.circuit.untagged
        pads = [pad for _, pad in visit(part, Pad)]
        self.assertTrue(pads)
        nets = [
            net
            for net in extract(self.circuit, Net)
            if any(p is part.a or p is part.b for p in net.connected)
        ]
        self.assertTrue(nets)
        pours = list(extract(self.circuit, Pour))
        self.assertTrue(pours)
        for obj in [part, part.landpattern, *pads, *nets, *pours]:
            self.assertEqual(_tag_types(obj) & relief_tags, set())


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestThermalClassesRuntime(TestCase):
    def test_relief_per_pad_matches_its_class(self) -> None:
        design = layout_thermal_classes_design
        root = Path(__file__).resolve().parents[1]
        shutil.rmtree(
            root / "designs" / f"{design.__module__}.{design.__qualname__}",
            ignore_errors=True,
        )
        with jitx.runtime as rt:
            rd = rt.submit(design)
            rd.capture(wait=30)
            circuit = rd.root.circuit
            assert isinstance(circuit, ThermalClasses)
            rules = _relief_rules(list(circuit.rules))
            pour = circuit.gnd_pour.shape.to_shapely().g
            untagged = {id(pad) for _, pad in visit(circuit.untagged, Pad)}
            pads = []
            for trace, pad in visit(rd.root, Pad):
                assert trace.transform is not None and pad.transform is not None
                shape = (
                    pad.shape.shape if isinstance(pad.shape, PadShape) else pad.shape
                )
                world = ((trace.transform * pad.transform) * shape).to_shapely().g
                pads.append(
                    (str(trace.path), _tag_types(pad), id(pad) in untagged, world)
                )

        self.assertEqual(sum(1 for pad in pads if pad[2]), len(untagged))
        # The module's measured list covers a small pad, a large pad, the
        # direct-connect pad and an untagged pad; each kind must be measured.
        seen: set[object] = set()
        for path, tags, bare, world in pads:
            voids, gap, spokes, ring = _relief(pour, world)
            with self.subTest(path):
                if bare or DirectConnectTag in tags:
                    seen.add("bare" if bare else DirectConnectTag)
                    # A pad no relief rule matches joins the pour solidly
                    # (measured on jitx 4.6), and so does the
                    # direct connect, whose spokes overlap. The pour then
                    # crosses the whole ring 0.02 mm outside the pad, so the
                    # crossing is as long as that ring.
                    self.assertEqual(voids, 0)
                    self.assertAlmostEqual(sum(spokes), ring, delta=0.005)
                    continue
                seen.update(tags & {SmallPadRelief, LargePadRelief})
                relief = _winning_rule(tags, rules).thermal_relief_constraint
                assert relief is not None
                self.assertEqual(voids, relief.num_spokes)
                self.assertEqual(len(spokes), relief.num_spokes)
                self.assertAlmostEqual(gap, relief.gap_distance, delta=0.005)
                for spoke in spokes:
                    self.assertAlmostEqual(spoke, relief.spoke_width, delta=0.005)
        self.assertEqual(
            seen, {SmallPadRelief, LargePadRelief, DirectConnectTag, "bare"}
        )

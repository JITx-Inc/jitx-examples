"""Tests for the heavy copper layer pattern.

The offline tests check the helpers against stackups and rules built here:
which conductor is heavy, worked from the test stackup's thicknesses, and
which rules the layout-constraints skill's ladder calls for on that layer.
The runtime test, gated by ``JITX_PATTERN_RUNTIME=1``, measures the realized
width and the mid-span pour pullback of every route. Its expected values are
worked from the design's input values by the ladder (the higher priority
wins; the copy at 3 holds the floor for the power net, the floor holds it
for the untagged net), with the 0.01 mm pullback offset measured on jitx 4.6.
"""

import os
import shutil
import unittest
from pathlib import Path

import jitx
import shapely
from jitx.constraints import (
    AndExpr,
    AnyObject,
    AtomExpr,
    BinaryDesignConstraint,
    BoolExpr,
    BuiltinTag,
    DesignConstraint,
    IsPour,
    NotExpr,
    OnLayer,
    Tag,
    UnaryDesignConstraint,
    design_constraint,
)
from jitx.sample import Copper, Core, SampleFabConstraints
from jitx.stackup import Stackup
from jitx.substrate import Substrate
from jitx.test import TestCase
from shapely.geometry import LineString

from jitxexamples.patterns import layout_heavy_copper_layer as heavy
from jitxexamples.patterns.layout_heavy_copper_layer import (
    HeavyCopperLayer,
    heavy_layer_index,
    heavy_layer_rules,
    layout_heavy_copper_layer_design,
)


class _ThreeOzThirdStackup(Stackup):
    """Four conductors, top to bottom 35, 35, 105 and 35 um."""

    l0 = Copper(thickness=0.035)
    d0 = Core(thickness=0.4)
    l1 = Copper(thickness=0.035)
    d1 = Core(thickness=0.4)
    l2 = Copper(thickness=0.105)
    d2 = Core(thickness=0.4)
    l3 = Copper(thickness=0.035)


class _ThreeOzThird(Substrate):
    stackup = _ThreeOzThirdStackup()
    constraints = SampleFabConstraints()


class _EvenStackup(Stackup):
    l0 = Copper(thickness=0.035)
    d0 = Core(thickness=0.4)
    l1 = Copper(thickness=0.035)


class _Even(Substrate):
    stackup = _EvenStackup()
    constraints = SampleFabConstraints()


class _PowerTag(Tag):
    pass


class _HighCurrentTag(_PowerTag):
    pass


class _SenseTag(Tag):
    pass


def _atoms(expr: BoolExpr) -> list[Tag]:
    if isinstance(expr, AtomExpr):
        return [expr.atom]
    if isinstance(expr, AndExpr):
        return _atoms(expr.left) + _atoms(expr.right)
    return []


def _negated(expr: BoolExpr) -> list[Tag]:
    if isinstance(expr, NotExpr):
        return _atoms(expr.expr)
    if isinstance(expr, AndExpr):
        return _negated(expr.left) + _negated(expr.right)
    return []


def _shape(rule: DesignConstraint) -> tuple[int, frozenset[str], float]:
    """Priority, the names of the first condition's tags, and the value."""
    if isinstance(rule, UnaryDesignConstraint):
        assert rule.trace_width_constraint is not None
        cond, value = rule.condition, rule.trace_width_constraint.width
    else:
        assert isinstance(rule, BinaryDesignConstraint)
        assert rule.clearance_constraint is not None
        cond, value = rule.first, rule.clearance_constraint.clearance
    names = frozenset(
        f"{t.name}" if isinstance(t, BuiltinTag) else type(t).__name__
        for t in _atoms(cond)
    )
    return rule.priority, names, value


class TestHeavyLayerIndex(TestCase):
    def test_finds_the_thickest_conductor(self) -> None:
        # 105 um is the third conductor from the top: index 2.
        self.assertEqual(heavy_layer_index(_ThreeOzThird()), 2)

    def test_finds_a_named_thickness(self) -> None:
        self.assertEqual(heavy_layer_index(_ThreeOzThird(), 0.105), 2)

    def test_refuses_a_stackup_with_no_heavy_layer(self) -> None:
        with self.assertRaisesRegex(ValueError, "models no heavy layer"):
            heavy_layer_index(_Even())

    def test_refuses_a_thickness_shared_by_several_conductors(self) -> None:
        with self.assertRaisesRegex(ValueError, "3 conductors"):
            heavy_layer_index(_ThreeOzThird(), 0.035)


class TestHeavyLayerRules(TestCase):
    """Floors 0.5 wide and 0.35 apart on layer 1, a 0.2 trace-to-pour rule,
    and power rules 0.4 wide and 0.3 apart at 2, both under the floors."""

    def _rules(self) -> list[DesignConstraint]:
        width = design_constraint(_PowerTag(), priority=2).trace_width(0.4)
        clearance = design_constraint(_PowerTag(), AnyObject, priority=2).clearance(0.3)
        return heavy_layer_rules(1, 0.5, 0.35, 0.2, [width, clearance])

    def test_floors_layer_form_and_copies_follow_the_ladder(self) -> None:
        rules = self._rules()
        for rule in rules:
            if isinstance(rule, UnaryDesignConstraint):
                cond = rule.condition
            else:
                assert isinstance(rule, BinaryDesignConstraint)
                cond = rule.first
            self.assertIn(1, [t.index for t in _atoms(cond) if isinstance(t, OnLayer)])
        self.assertEqual(
            sorted(_shape(r) for r in rules),
            sorted(
                [
                    (1, frozenset({"IsTrace", "OnLayer"}), 0.5),
                    (1, frozenset({"IsCopper", "OnLayer"}), 0.35),
                    # The layer form takes the larger of 0.2 and the 0.35 floor.
                    (1, frozenset({"IsTrace", "OnLayer"}), 0.35),
                    (3, frozenset({"_PowerTag", "OnLayer"}), 0.5),
                    (3, frozenset({"_PowerTag", "OnLayer"}), 0.35),
                ]
            ),
        )
        (layer_form,) = [
            r
            for r in rules
            if isinstance(r, BinaryDesignConstraint)
            and isinstance(r.second, AtomExpr)
            and r.second.atom is IsPour
        ]
        self.assertEqual(layer_form.priority, 1)

    def test_a_rule_at_or_above_the_floor_gets_no_copy(self) -> None:
        wide = design_constraint(_PowerTag(), priority=2).trace_width(0.6)
        rules = heavy_layer_rules(1, 0.5, 0.35, 0.2, [wide])
        self.assertEqual([r.priority for r in rules], [1, 1, 1])

    def test_copies_exclude_route_tags_but_not_their_own(self) -> None:
        sense = design_constraint(_SenseTag(), priority=3).trace_width(0.3)
        rules = heavy_layer_rules(
            1,
            0.5,
            0.35,
            0.2,
            [design_constraint(_PowerTag(), priority=2).trace_width(0.4), sense],
            exclude=[_SenseTag()],
        )
        copies = [r for r in rules if r.priority == 3]
        assert all(isinstance(r, UnaryDesignConstraint) for r in copies)
        excluded = {
            type(_atoms(r.condition)[0]).__name__: [
                type(t).__name__ for t in _negated(r.condition)
            ]
            for r in copies
            if isinstance(r, UnaryDesignConstraint)
        }
        self.assertEqual(excluded, {"_PowerTag": ["_SenseTag"], "_SenseTag": []})

    def test_an_excluded_route_still_holds_the_clearance_floor(self) -> None:
        # The clearance copy is the only rule at 3 that keeps the power
        # rule's 0.3 at 2 off a sense route on the heavy layer, so it must
        # still match sense routes; only the width copy leaves them out.
        rules = heavy_layer_rules(
            1,
            0.5,
            0.35,
            0.2,
            [
                design_constraint(_PowerTag(), priority=2).trace_width(0.4),
                design_constraint(_PowerTag(), AnyObject, priority=2).clearance(0.3),
            ],
            exclude=[_SenseTag()],
        )
        excluded: dict[str, list[str]] = {}
        for rule in rules:
            if rule.priority != 3:
                continue
            if isinstance(rule, UnaryDesignConstraint):
                kind, cond = "width", rule.condition
            else:
                assert isinstance(rule, BinaryDesignConstraint)
                kind, cond = "clearance", rule.first
            excluded[kind] = [type(t).__name__ for t in _negated(cond)]
        self.assertEqual(excluded, {"width": ["_SenseTag"], "clearance": []})

    def test_refuses_shapes_the_skill_does_not_teach(self) -> None:
        cases: list[tuple[DesignConstraint, str]] = [
            (design_constraint(_PowerTag()).trace_width(0.4), "priority 0"),
            (
                design_constraint(_PowerTag(), priority=2).thermal_relief(0.2, 0.2, 4),
                "only a width",
            ),
            (
                design_constraint(
                    _PowerTag() & _HighCurrentTag(), priority=2
                ).trace_width(0.4),
                "condition is one tag",
            ),
            (
                design_constraint(OnLayer(0), AnyObject, priority=2).clearance(0.2),
                "condition is one tag",
            ),
        ]
        for rule, message in cases:
            with (
                self.subTest(message=message),
                self.assertRaisesRegex(ValueError, message),
            ):
                heavy_layer_rules(1, 0.5, 0.35, 0.2, [rule])


class TestHeavyCopperDesign(TestCase):
    def test_design_names_the_heavy_conductor(self) -> None:
        # The stackup's 70 um conductor is the second from the top.
        design = layout_heavy_copper_layer_design()
        circuit = design.circuit
        assert isinstance(circuit, HeavyCopperLayer)
        self.assertEqual(circuit.heavy_layer, 1)

    def test_requested_widths_fit_the_end_pads(self) -> None:
        # A width over the end pads comes back as the pads' hull (measured on
        # jitx 4.6).
        circuit = layout_heavy_copper_layer_design().circuit
        assert isinstance(circuit, HeavyCopperLayer)
        widths = [
            r.trace_width_constraint.width
            for r in circuit.rules
            if isinstance(r, UnaryDesignConstraint) and r.trace_width_constraint
        ]
        for width in widths:
            for end in circuit.ends:
                self.assertLessEqual(width, float(end.diameter))


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestHeavyCopperRuntime(TestCase):
    def test_width_and_pullback_per_route(self) -> None:
        design = layout_heavy_copper_layer_design
        root = Path(__file__).resolve().parents[1]
        shutil.rmtree(
            root / "designs" / f"{design.__module__}.{design.__qualname__}",
            ignore_errors=True,
        )
        with jitx.runtime as rt:
            rd = rt.submit(design)
            rd.capture(wait=30)
            circuit = rd.root.circuit
            assert isinstance(circuit, HeavyCopperLayer)
            measured: dict[tuple[str, int], tuple[int, float, float]] = {}
            for name, routes in (
                ("PWR", circuit.routes),
                ("SIG", circuit.signal_routes),
            ):
                for layer, route in routes.items():
                    shapes = [s for t in route.traces or [] for s in t.shapes]
                    copper = shapely.union_all([s.to_shapely().g for s in shapes])
                    pour = circuit.pours[layer].shape.to_shapely().g
                    y = copper.centroid.y
                    cut = LineString([(0, y - 5), (0, y + 5)])
                    width = copper.intersection(cut).length
                    above = pour.intersection(LineString([(0, y), (0, y + 5)]))
                    pullback = above.bounds[1] - y - width / 2
                    measured[(name, layer)] = (len(shapes), width, pullback)

        # Worked from the inputs by the ladder: on the heavy layer the floor
        # (or the larger value) holds for both nets; elsewhere the power rule
        # at 2 beats the board rules, and the untagged route takes the board
        # width and the trace-to-pour clearance.
        floor_w, floor_c = heavy.HEAVY_MIN_WIDTH, heavy.HEAVY_MIN_CLEARANCE
        expected = {
            ("PWR", 0): (heavy.POWER_WIDTH, heavy.POWER_CLEARANCE),
            ("PWR", 1): (
                max(heavy.POWER_WIDTH, floor_w),
                max(heavy.POWER_CLEARANCE, floor_c),
            ),
            ("PWR", 2): (heavy.POWER_WIDTH, heavy.POWER_CLEARANCE),
            ("SIG", 0): (heavy.BOARD_WIDTH, heavy.TRACE_TO_POUR),
            ("SIG", 1): (
                max(heavy.BOARD_WIDTH, floor_w),
                max(heavy.TRACE_TO_POUR, floor_c),
            ),
        }
        self.assertEqual(set(measured), set(expected))
        for key, (want_width, want_clearance) in expected.items():
            count, width, pullback = measured[key]
            with self.subTest(route=key):
                self.assertGreater(count, 0)
                self.assertAlmostEqual(width, want_width, delta=0.005)
                self.assertAlmostEqual(pullback, want_clearance + 0.01, delta=0.005)

"""Tests for the fenced grounded coplanar line pattern.

The offline tests read the translated design, which is what the layout
engine receives, and check the relations the module docstring states, worked
from the structure's numbers, the fence via's pad and drill, and the sample
fab constraints. The runtime tests build both designs and measure the fence
vias and the computed coplanar pour; they need ``JITX_PATTERN_RUNTIME=1`` and
a runtime started at the project root. The expected positions come from the
relations measured on jitx 4.6: the pour
gap is the winning clearance plus 0.01, row k sits at w/2 + o1 + (k-1)·o
from the centreline, and a via around a route end sits on a row's distance
from the end point.
"""

from __future__ import annotations

import math
import os
import shutil
import unittest
from dataclasses import dataclass
from pathlib import Path

import jitx

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_js1_hdi_stackup.py
# uses it for the same reason).
from jitx._translate.design import package_design
from jitx.design import Design
from jitx.inspect import visit
from jitx.constraints import ViaFencePattern
from jitx.run.runtime import RuntimeDesign
from jitx.sample import SampleSubstrate
from jitx.test import TestCase
from jitx.via import Via
from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry

from jitxexamples.patterns.layout_cpwg_two_row_fence import (
    CPWGLine,
    GroundTag,
    RFLineTag,
    checked_fence_pattern,
    coplanar_gap,
    fence_row_centre,
    layout_cpwg_two_row_fence_design,
    layout_cpwg_two_row_fence_failure_design,
    rows_in_coplanar_pour,
    straight_run_fence_sites,
)

TAG_NAME = f"{RFLineTag.__module__}.{RFLineTag.__qualname__}"
GROUND_TAG_NAME = f"{GroundTag.__module__}.{GroundTag.__qualname__}"
POUR_OFFSET = 0.01  # jitx 4.6: the pour gap is the winning clearance plus 0.01


class _Translated:
    """The numbers the layout engine receives for one design."""

    def __init__(self, design: Design) -> None:
        v1 = package_design(design).v1
        (structure,) = v1.routings
        (layer,) = structure.layers
        self.layer_index = layer.layer.index
        self.width = layer.trace_width
        self.gap = layer.clearance
        self.pattern = layer.fence.pattern
        (via,) = [v for v in v1.vias if v.name == layer.fence.definition]
        self.pad = via.diameter
        self.drill = via.hole_diameter
        self.structure_rules = [
            r for r in v1.design_rules if r.effects[0].HasField("routing_structure")
        ]
        # Clearance rules whose first condition is the RF tag and whose second
        # matches anything: these move the coplanar pour.
        self.rf_to_anything = [
            r.effects[0].clearance.clearance
            for r in v1.design_rules
            if r.effects[0].HasField("clearance")
            and r.conditions[0].atom_expr.atom.user.name == TAG_NAME
            and r.conditions[1].HasField("true_expr")
        ]
        # Clearance rules between the RF tag and the ground tag, in either
        # order: (GroundTag(), RFLineTag()) is the same rule.
        self.rf_to_ground = [
            r.effects[0].clearance.clearance
            for r in v1.design_rules
            if r.effects[0].HasField("clearance")
            and sorted(
                c.atom_expr.atom.user.name if c.HasField("atom_expr") else ""
                for c in r.conditions
            )
            == sorted([TAG_NAME, GROUND_TAG_NAME])
        ]
        top = {m.id: m for m in v1.modules}[v1.module]
        self.ground_tagged = {
            n.name
            for n in top.nets
            for a in top.apply_tags
            if tuple(a.local.path) == (n.id,)
            and GROUND_TAG_NAME in {t.name for t in a.tags}
        }

    @property
    def winning_clearance(self) -> float:
        # C: the structure's clearance is a floor. A pair rule at priority 2
        # wins over a keep-away at the default priority (measured on jitx
        # 4.6), so the keep-away counts only without the pair rule.
        rules = self.rf_to_ground or self.rf_to_anything
        return max([self.gap, *rules])

    def row_centre(self, k: int) -> float:
        """From the centreline to row k's via centres: w/2 + o1 + (k-1)·o."""
        p = self.pattern
        return self.width / 2 + p.initial_offset + (k - 1) * p.offset

    def row_reach(self, k: int) -> float:
        """From the trace edge to the outer edge of row k's via pads."""
        p = self.pattern
        return p.initial_offset + (k - 1) * p.offset + self.pad / 2


# Measured on jitx 4.6 with a 0.5 trace, a 0.45 pad through via and
# ``initial_offset`` and ``offset`` 0.6: rows at 0.851 and 1.451 from the
# centreline; with ``initial_offset`` 0.3, at 0.551 and 1.151.
_MEASURED_PATTERN = ViaFencePattern(
    pitch=1.0, offset=0.6, initial_offset=0.6, num_rows=2
)
_THVIA = SampleSubstrate.THVia


class TestFenceArithmetic(unittest.TestCase):
    def test_coplanar_gap_is_the_wider_clearance_plus_a_hundredth(self) -> None:
        # Measured on jitx 4.6: 0.51 for a 0.2 structure under a 0.5 rule
        # and for a 0.5 structure under a 0.2 rule; 0.31 for a 0.3 structure
        # with no rule.
        for structure, rule, measured in ((0.2, 0.5, 0.51), (0.5, 0.2, 0.51)):
            self.assertAlmostEqual(coplanar_gap(structure, rule), measured, delta=0.005)
        self.assertAlmostEqual(coplanar_gap(0.3), 0.31, delta=0.005)

    def test_row_centres_count_from_the_trace_edge(self) -> None:
        for row, measured in ((1, 0.851), (2, 1.451)):
            centre = fence_row_centre(0.5, _MEASURED_PATTERN, row)
            self.assertAlmostEqual(centre, measured, delta=0.005)
        close = ViaFencePattern(pitch=1.0, offset=0.6, initial_offset=0.3, num_rows=2)
        self.assertAlmostEqual(fence_row_centre(0.5, close, 1), 0.551, delta=0.005)
        with self.assertRaisesRegex(ValueError, "outside the pattern's rows"):
            fence_row_centre(0.5, _MEASURED_PATTERN, 3)

    def test_first_row_pads_must_clear_the_gap(self) -> None:
        # The pad edge sits initial_offset - 0.225 from the trace edge:
        # 0.225 for 0.45 clears a 0.21 gap, 0.175 for 0.4 does not.
        ok = ViaFencePattern(pitch=1.0, offset=0.6, initial_offset=0.45)
        self.assertIs(checked_fence_pattern(ok, _THVIA, 0.21), ok)
        tight = ViaFencePattern(pitch=1.0, offset=0.6, initial_offset=0.4)
        with self.assertRaisesRegex(ValueError, "inside the 0.21 mm gap"):
            checked_fence_pattern(tight, _THVIA, 0.21)

    def test_a_first_row_exactly_on_the_bound_passes(self) -> None:
        # The docstring's rule is initial_offset - pad / 2 >= pour_gap. At a
        # 0.127 structure clearance the gap is 0.137 (0.127 + 0.01), so 0.362
        # puts the 0.45 pad's edge exactly on it.
        exact = ViaFencePattern(pitch=1.0, offset=0.6, initial_offset=0.362)
        self.assertIs(checked_fence_pattern(exact, _THVIA, coplanar_gap(0.127)), exact)

    def test_a_pair_rule_wider_than_the_structure_widens_what_pads_clear(
        self,
    ) -> None:
        # A structure at a 0.127 fab floor with a 0.3 pair rule: the pour
        # starts 0.31 from the trace edge, by the gap rule measured on jitx
        # 4.6 (this configuration was not built). A 0.4 first
        # row puts the pad edge 0.175 from the trace, inside it; 0.55 puts it
        # at 0.325, outside.
        gap = coplanar_gap(0.127, 0.3)
        tight = ViaFencePattern(pitch=1.0, offset=0.6, initial_offset=0.4)
        with self.assertRaisesRegex(ValueError, "pads start 0.175 mm"):
            checked_fence_pattern(tight, _THVIA, gap)
        ok = ViaFencePattern(pitch=1.0, offset=0.6, initial_offset=0.55)
        self.assertIs(checked_fence_pattern(ok, _THVIA, gap), ok)

    def test_rows_that_reach_the_pour(self) -> None:
        # Measured on jitx 4.6: with the pour 0.91 from the trace edge only
        # row 2's pads reached it, with it at 1.51 neither row did, and at
        # 0.21 both did.
        self.assertEqual(rows_in_coplanar_pour(_MEASURED_PATTERN, _THVIA, 0.91), [2])
        self.assertEqual(rows_in_coplanar_pour(_MEASURED_PATTERN, _THVIA, 1.51), [])
        self.assertEqual(rows_in_coplanar_pour(_MEASURED_PATTERN, _THVIA, 0.21), [1, 2])
        # Row 1's centre is 0.6 from the trace edge and its pad 0.225 wide
        # either side, so its edge reaches 0.825: past a pour at 0.7.
        self.assertEqual(rows_in_coplanar_pour(_MEASURED_PATTERN, _THVIA, 0.7), [1, 2])

    def test_a_row_whose_pad_edge_is_exactly_on_the_pour_does_not_reach_it(
        self,
    ) -> None:
        # The docstring's rule is a strict initial_offset + (k-1)*offset + pad/2
        # > pour_gap. Row 2's far pad edge: 0.3 + 0.5 + 0.225 = 1.025, exactly
        # the gap given, so neither row reaches the pour.
        pattern = ViaFencePattern(pitch=1.0, offset=0.5, initial_offset=0.3, num_rows=2)
        self.assertEqual(rows_in_coplanar_pour(pattern, _THVIA, 1.025), [])

    def test_a_run_shorter_than_one_pitch_holds_no_site(self) -> None:
        # A count of vias cannot be negative: 0.3 mm at pitch 1.0 holds none.
        self.assertEqual(straight_run_fence_sites(0.3, 1.0, 1), (0, 0))

    def test_straight_run_holds_one_site_per_pitch(self) -> None:
        # Measured on jitx 4.6 along 24 mm at pitch 1.0: 24 per side in both
        # rows with the first row 0.6 from the trace and no wider rule on the
        # line; row 2 held 24 in every case.
        self.assertEqual(straight_run_fence_sites(24.0, 1.0, 2), (24, 24))
        low, high = straight_run_fence_sites(24.0, 1.0, 1)
        self.assertTrue(low <= 24 <= high, (low, high))

    def test_row_one_can_drop_one_site(self) -> None:
        # Measured on jitx 4.6 along 24 mm at pitch 1.0: 23 per side in row 1
        # under a 0.5 to 1.5 net-tag rule, a 0.6 pair rule, or a first row
        # 0.3 from the trace; 20 per side in this module's 20 mm failure
        # design.
        low, high = straight_run_fence_sites(24.0, 1.0, 1)
        self.assertTrue(low <= 23 <= high, (low, high))
        low, high = straight_run_fence_sites(20.0, 1.0, 1)
        self.assertTrue(low <= 20 <= high, (low, high))

    def test_refuses_a_row_that_was_not_measured(self) -> None:
        with self.assertRaisesRegex(ValueError, "row 3"):
            straight_run_fence_sites(24.0, 1.0, 3)


class TestCPWGOffline(TestCase):
    def setUp(self) -> None:
        self.good = _Translated(layout_cpwg_two_row_fence_design())
        self.failure = _Translated(layout_cpwg_two_row_fence_failure_design())

    def test_structure_is_applied_by_a_rule_on_the_rf_tag(self) -> None:
        design = layout_cpwg_two_row_fence_design()
        v1 = package_design(design).v1
        (rule,) = self.good.structure_rules
        self.assertEqual(
            [c.atom_expr.atom.user.name for c in rule.conditions], [TAG_NAME]
        )
        # The tag sits on the RF net, which the route joins.
        modules = {m.id: m for m in v1.modules}
        top = modules[v1.module]
        rf_ids = {n.id for n in top.nets if n.name == "RF"}
        self.assertEqual(len(rf_ids), 1)
        tagged = {
            tuple(a.local.path)
            for a in top.apply_tags
            if TAG_NAME in {t.name for t in a.tags}
        }
        self.assertEqual(tagged, {(i,) for i in rf_ids})

    def test_pair_rule_sets_a_gap_no_narrower_than_the_structure(self) -> None:
        # The gap comes from an RF-to-ground pair rule on the GND net's tag,
        # with the structure's clearance at or below it (product owner,
        # 2026-11-05). The failure design leaves the rule out so its
        # keep-away is what moves the pour.
        t = self.good
        self.assertEqual(t.ground_tagged, {"GND"})
        (gap,) = t.rf_to_ground
        self.assertLessEqual(t.gap, gap)
        self.assertEqual(self.failure.rf_to_ground, [])

    def test_fence_is_on_the_layer_the_line_is_routed_on(self) -> None:
        circuit = layout_cpwg_two_row_fence_design().circuit
        assert isinstance(circuit, CPWGLine)
        self.assertEqual(self.good.layer_index, circuit.route.layer)

    def test_first_row_pads_stay_out_of_the_gap(self) -> None:
        # o1 - d/2 clears the coplanar gap. The runtime does not enforce this
        # (measured on jitx 4.6: fence pads under the fab floor were placed
        # with no issue).
        t = self.good
        self.assertGreaterEqual(
            t.pattern.initial_offset - t.pad / 2, t.winning_clearance + POUR_OFFSET
        )

    def test_both_rows_reach_the_coplanar_pour_on_the_good_design(self) -> None:
        t = self.good
        self.assertEqual(t.rf_to_anything, [])
        for k in (1, 2):
            self.assertGreater(t.row_reach(k), t.winning_clearance + POUR_OFFSET)

    def test_rf_keepaway_leaves_row_one_outside_the_pour(self) -> None:
        t = self.failure
        self.assertGreater(t.winning_clearance, t.gap)
        self.assertLess(t.row_reach(1), t.winning_clearance + POUR_OFFSET)
        self.assertGreater(t.row_reach(2), t.winning_clearance + POUR_OFFSET)

    def test_fence_drills_meet_the_fab_hole_spacing(self) -> None:
        fab = layout_cpwg_two_row_fence_design().substrate.constraints
        p = self.good.pattern
        for spacing in (p.pitch, p.offset):
            self.assertGreaterEqual(spacing - self.good.drill, fab.min_hole_to_hole)

    def test_each_side_of_the_line_has_its_own_ground_anchor(self) -> None:
        # A pour region with no same-net object is removed as an island, and
        # fence vias do not count (measured on jitx 4.6).
        circuit = layout_cpwg_two_row_fence_design().circuit
        assert isinstance(circuit, CPWGLine)
        outline = circuit.coplanar.shape.to_shapely().g
        sides = set()
        for anchor in circuit.anchors:
            assert anchor.transform is not None
            x, y = anchor.transform.translation
            self.assertTrue(outline.contains(Point(x, y)))
            sides.add(y > 0)
        self.assertEqual(sides, {True, False})


def _submit(design: type[Design]) -> RuntimeDesign:
    # A changed design aborts a headless submit at "stabilization" unless its
    # stored state is removed first (seen on jitx 4.6).
    root = Path(__file__).resolve().parents[1]
    shutil.rmtree(
        root / "designs" / f"{design.__module__}.{design.__qualname__}",
        ignore_errors=True,
    )
    with jitx.runtime as r:
        rd = r.submit(design)
        rd.capture(wait=40)
        return rd


@dataclass
class _Built:
    """One built design, as the runtime tests read it."""

    t: _Translated
    rows: dict[int, list[tuple[float, float]]]
    """The fence vias between the pad centres, sorted into rows."""
    half: float
    """Half the distance between the pad centres."""
    pour: BaseGeometry
    """The computed coplanar pour."""
    fence_nets: set[str | None]
    every_via: list[tuple[float, float]]
    """Every fence via, around the ends included."""


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestCPWGRuntime(TestCase):
    def _build(self, design: type[Design]) -> _Built:
        t = _Translated(design())
        rd = _submit(design)
        circuit = rd.root.circuit
        assert isinstance(circuit, CPWGLine)
        assert circuit.load.transform is not None
        half = circuit.load.transform.translation[0]
        b = _Built(
            t,
            {1: [], 2: []},
            half,
            circuit.coplanar.shape.to_shapely().g,
            set(),
            [],
        )
        # rd.query(Via) returns the fence vias together with the two anchors
        # the circuit places in code. The anchors are the Via objects in the
        # captured tree, which visit lists and the query yields as themselves,
        # so they are left out by identity.
        placed = {id(via) for _, via in visit(rd.root, Via)}
        for trace, via in rd.query(Via):
            if id(via) in placed:
                continue
            net = rd.nets.find(via)
            b.fence_nets.add(net.name if net else None)
            assert trace.transform is not None and via.transform is not None
            x, y = (trace.transform * via.transform).translation
            b.every_via.append((x, y))
            if abs(x) > half:
                # Around a route end, which is at a pad centre: the via sits
                # on a row's distance from the end point (measured on jitx 4.6).
                r = math.hypot(abs(x) - half, y)
                k = min(b.rows, key=lambda k: abs(r - t.row_centre(k)))
                self.assertAlmostEqual(
                    r, t.row_centre(k), delta=0.01, msg=f"end via at {x, y}"
                )
                continue
            k = min(b.rows, key=lambda k: abs(abs(y) - t.row_centre(k)))
            self.assertAlmostEqual(
                abs(y), t.row_centre(k), delta=0.005, msg=f"via at {x, y}"
            )
            b.rows[k].append((x, y))
        return b

    def _assert_pour_edges(self, pour: BaseGeometry, edge: float) -> None:
        """The pour's copper starts ``edge`` from the centreline on both
        sides, measured across the middle of the line."""
        cut = pour.intersection(LineString([(0, -10), (0, 10)]))
        spans = sorted(
            sorted((s.coords[0][1], s.coords[-1][1]))
            for s in getattr(cut, "geoms", [cut])
            if not s.is_empty
        )
        self.assertEqual(len(spans), 2, "coplanar ground on both sides")
        self.assertAlmostEqual(spans[0][1], -edge, delta=0.005)
        self.assertAlmostEqual(spans[1][0], edge, delta=0.005)

    def _assert_full_rows(
        self, t: _Translated, rows: dict[int, list[tuple[float, float]]], half: float
    ) -> None:
        # A full straight run, in the range straight_run_fence_sites accepts.
        for k, row in rows.items():
            low, high = straight_run_fence_sites(2 * half, t.pattern.pitch, k)
            above = sum(1 for _, y in row if y > 0)
            for side in (above, len(row) - above):
                self.assertTrue(low <= side <= high, (k, side, low, high))

    def test_good_design_fences_both_rows_in_coplanar_ground(self) -> None:
        b = self._build(layout_cpwg_two_row_fence_design)
        t, pour = b.t, b.pour
        # Each claim is its own subtest, so one failure does not hide the rest.
        with self.subTest("every fence via on the pour"):
            # The pour runs past both pads, so the vias around each end of
            # the line, not only the straight rows, land on layer-0 ground.
            self.assertTrue(b.every_via)
            for x, y in b.every_via:
                self.assertTrue(
                    pour.contains(Point(x, y).buffer(t.pad / 2 - 0.01)),
                    f"fence via at {x:.3f}, {y:.3f} is off the coplanar pour",
                )
        with self.subTest("fence net"):
            # The vias take the net of the reference layer's plane.
            self.assertEqual(b.fence_nets, {"GND"})
        with self.subTest("full rows"):
            self._assert_full_rows(t, b.rows, b.half)
        with self.subTest("pour gap"):
            edge = t.width / 2 + t.winning_clearance + POUR_OFFSET
            self._assert_pour_edges(pour, edge)

    def test_rf_keepaway_pushes_the_coplanar_pour_past_row_one(self) -> None:
        b = self._build(layout_cpwg_two_row_fence_failure_design)
        t, rows, pour = b.t, b.rows, b.pour
        # Each claim is its own subtest, so one failure does not hide the rest.
        with self.subTest("fence net"):
            self.assertEqual(b.fence_nets, {"GND"})
        with self.subTest("full rows"):
            self._assert_full_rows(t, rows, b.half)
        with self.subTest("pour gap"):
            edge = t.width / 2 + t.winning_clearance + POUR_OFFSET
            self._assert_pour_edges(pour, edge)
        with self.subTest("row 1 outside the pour"):
            for x, y in rows[1]:
                self.assertFalse(pour.intersects(Point(x, y).buffer(t.pad / 2)))
        with self.subTest("row 2 in the pour"):
            self.assertGreater(t.row_reach(2), t.winning_clearance + POUR_OFFSET)
            for x, y in rows[2]:
                self.assertTrue(pour.intersects(Point(x, y).buffer(t.pad / 2)))

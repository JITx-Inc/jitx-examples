"""Tests for the two-lane diff-pair escape pattern.

The expected values are worked out here from the device's pad copper, the
sample fab constraints and the rules as translated, not read from the
module's constants. With ``JITX_PATTERN_RUNTIME=1`` and a runtime started at
the project root, the runtime test builds the design and measures each
segment's width, the spacing between the lanes' runs, and the spacing
between necks of different nets.

The run spacing is checked against where the module places the run points,
and the measured runs against that spacing.
"""

from __future__ import annotations

import os
import shutil
import unittest
from itertools import combinations
from pathlib import Path

import jitx

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_js1_hdi_stackup.py
# uses it for the same reason).
from jitx._translate.design import package_design
from jitx.circuit import Route
from jitx.landpattern import Pad, PadShape
from jitx.sample import SampleFabConstraints
from jitx.test import TestCase
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from jitxexamples.patterns.layout_diff_pair_escape import (
    DiffPairTag,
    Lane0RunTag,
    Lane1RunTag,
    PairNeckTag,
    TwoLaneLink,
    layout_diff_pair_escape_design,
    layout_diff_pair_escape_failure_design,
)

FAB = SampleFabConstraints


def _name(tag: type) -> str:
    return f"{tag.__module__}.{tag.__qualname__}"


def _pad_copper(pad: Pad) -> BaseGeometry:
    shape = pad.shape
    if isinstance(shape, PadShape):
        shape = shape.shape
    assert pad.transform is not None
    return (pad.transform * shape).to_shapely().g


def _lane(net_name: str | None) -> int:
    # The nets are named L<lane>_<P|N>.
    assert net_name is not None
    return int(net_name[1])


class _Expected:
    """Pad geometry, the rules as translated, and the authored run points."""

    def __init__(
        self, design_class: type[jitx.Design] = layout_diff_pair_escape_design
    ) -> None:
        design = design_class()
        circuit = design.circuit
        assert isinstance(circuit, TwoLaneLink)
        self.circuit = circuit
        lp = circuit.near.landpattern
        (mapping,) = circuit.near.mappings

        def copper(port: jitx.net.Port) -> BaseGeometry:
            pad = mapping[port]
            assert isinstance(pad, Pad)
            return _pad_copper(pad)

        pads = [_pad_copper(p) for p in lp.pads]
        minx, miny, maxx, maxy = pads[0].bounds
        self.pad_width = min(maxx - minx, maxy - miny)
        self.pad_gap = min(a.distance(b) for a, b in combinations(pads, 2))
        # The two lanes' nearest pads at the device.
        self.lane_pad_gap = min(
            copper(a).distance(copper(b))
            for a in (circuit.near.lane0.p, circuit.near.lane0.n)
            for b in (circuit.near.lane1.p, circuit.near.lane1.n)
        )

        v1 = package_design(design).v1
        self.widths: dict[str, tuple[int, float]] = {}
        self.clearances: list[tuple[set[str], float]] = []
        for rule in v1.design_rules:
            (effect,) = rule.effects
            names = {c.atom_expr.atom.user.name for c in rule.conditions}
            if effect.HasField("trace_width"):
                (name,) = names
                self.widths[name] = (rule.priority, effect.trace_width.width)
            elif effect.HasField("clearance"):
                self.clearances.append((names, effect.clearance.clearance))
        top = next(m for m in v1.modules if m.id == v1.module)
        self.tagged: dict[str, set[tuple[int, ...]]] = {}
        for apply in top.apply_tags:
            for tag in apply.tags:
                self.tagged.setdefault(tag.name, set()).add(tuple(apply.local.path))
        self.net_paths = {(n.id,) for n in top.nets if n.name}

    @property
    def run_width(self) -> float:
        return self.widths[_name(DiffPairTag)][1]

    @property
    def neck_width(self) -> float:
        return self.widths[_name(PairNeckTag)][1]

    @property
    def pair_to_pair(self) -> float:
        (value,) = (
            v
            for names, v in self.clearances
            if names == {_name(Lane0RunTag), _name(Lane1RunTag)}
        )
        return value


class TestDiffPairEscapeOffline(TestCase):
    def setUp(self) -> None:
        self.e = _Expected()

    def test_run_width_breaks_the_fab_floor_at_the_device(self) -> None:
        reach = self.e.pad_gap + self.e.pad_width / 2
        self.assertLess(reach - self.e.run_width / 2, FAB.min_copper_copper_space)

    def test_neck_fits_inside_the_pad_and_above_the_floor(self) -> None:
        self.assertGreaterEqual(self.e.pad_gap, FAB.min_copper_copper_space)
        self.assertLess(self.e.neck_width, self.e.pad_width)
        self.assertGreaterEqual(self.e.neck_width, FAB.min_copper_width)

    def test_neck_rule_outranks_the_run_rule(self) -> None:
        run_priority, _ = self.e.widths[_name(DiffPairTag)]
        neck_priority, _ = self.e.widths[_name(PairNeckTag)]
        self.assertGreater(neck_priority, run_priority)

    def test_tags_sit_on_nets_necks_and_runs(self) -> None:
        # Each of the four tags is on something; DiffPairTag is on nets;
        # the neck and run tags are on routes, never on a net, and no route is
        # both a neck and a run.
        tagged = {
            tag: self.e.tagged.get(_name(tag), set())
            for tag in (DiffPairTag, PairNeckTag, Lane0RunTag, Lane1RunTag)
        }
        for tag, paths in tagged.items():
            self.assertTrue(paths, f"nothing carries {tag.__name__}")
        self.assertLessEqual(tagged[DiffPairTag], self.e.net_paths)
        for tag in (PairNeckTag, Lane0RunTag, Lane1RunTag):
            self.assertFalse(tagged[tag] & self.e.net_paths, tag.__name__)
        runs = tagged[Lane0RunTag] | tagged[Lane1RunTag]
        self.assertFalse(tagged[PairNeckTag] & runs)

    def test_failure_design_puts_the_lane_tags_on_the_nets(self) -> None:
        failure = _Expected(layout_diff_pair_escape_failure_design)
        for tag in (Lane0RunTag, Lane1RunTag):
            paths = failure.tagged[_name(tag)]
            self.assertTrue(paths, tag.__name__)
            self.assertLessEqual(paths, failure.net_paths, tag.__name__)

    def test_pair_to_pair_rule_could_not_hold_at_the_device(self) -> None:
        # Why the rule is keyed on the runs, not the nets.
        self.assertLess(self.e.lane_pad_gap, self.e.pair_to_pair)

    def test_authored_runs_keep_the_pair_to_pair_spacing(self) -> None:
        c = self.e.circuit
        ys: dict[int, list[float]] = {0: [], 1: []}
        for net, start in zip(c.nets, c.points[::2], strict=True):
            assert start.transform is not None
            ys[_lane(net.name)].append(start.transform.translation[1])
        centre_gap = min(abs(a - b) for a in ys[0] for b in ys[1])
        self.assertGreaterEqual(
            round(centre_gap - self.e.run_width, 6), self.e.pair_to_pair
        )


def _widths(route: Route) -> set[float]:
    return {
        round(s.geometry.width, 4)
        for t in route.traces or []
        for s in t.shapes
        if hasattr(s.geometry, "width")
    }


def _copper(route: Route) -> BaseGeometry:
    return unary_union([s.to_shapely().g for t in route.traces or [] for s in t.shapes])


def _build(design: type[jitx.Design]) -> tuple[TwoLaneLink, str]:
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
        text = rd.issues(satisfied=True, wait=30).text()
    circuit = rd.root.circuit
    assert isinstance(circuit, TwoLaneLink)
    return circuit, text


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestDiffPairEscapeRuntime(TestCase):
    def test_widths_per_segment_and_spacing(self) -> None:
        e = _Expected()
        c, text = _build(layout_diff_pair_escape_design)
        self.assertNotIn("Unrealizable Route", text)
        self.assertNotIn("Unable to find path", text)
        self.assertIn("Routing:\n  - Satisfied", text)
        for near, run, far in zip(c.near_necks, c.runs, c.far_necks, strict=True):
            self.assertEqual(_widths(near), {e.neck_width})
            self.assertEqual(_widths(far), {e.neck_width})
            self.assertEqual(_widths(run), {e.run_width})

        lanes = [_lane(n.name) for n in c.nets]
        runs = [_copper(r) for r in c.runs]
        # Each run's two points share a y, and the run came back as the
        # straight line between them: one trace width tall.
        for run in runs:
            _, ymin, _, ymax = run.bounds
            self.assertAlmostEqual(ymax - ymin, e.run_width, delta=1e-6)
        lane_gap = min(
            runs[i].distance(runs[j])
            for i, j in combinations(range(4), 2)
            if lanes[i] != lanes[j]
        )
        self.assertGreaterEqual(round(lane_gap, 6), e.pair_to_pair)
        # The necks are realized by the router; different nets keep the fab
        # floor between them.
        for necks in (c.near_necks, c.far_necks):
            copper = [_copper(r) for r in necks]
            for a, b in combinations(copper, 2):
                self.assertGreaterEqual(a.distance(b), FAB.min_copper_copper_space)

    def test_pair_to_pair_rule_on_the_nets_leaves_a_neck_unrouted(self) -> None:
        c, text = _build(layout_diff_pair_escape_failure_design)
        self.assertIn("Unrealizable Route: Insufficient space", text)
        self.assertIn("Unable to find path for requested route", text)
        empty = [r for r in (*c.near_necks, *c.far_necks) if _copper(r).is_empty]
        self.assertTrue(empty)
        # The runs, placed 0.5 apart by their run points, still realize.
        for run in c.runs:
            self.assertFalse(_copper(run).is_empty)

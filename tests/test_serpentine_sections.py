"""Tests for the serpentine sections pattern.

The offline tests read the translated design, which is what the router
receives, and check what the example needs for its meanders to appear: each
length-matched section runs between two pair points (measured on jitx 4.6.0:
a section ending at 0.6 mm pads like these reported an
``UnsquiggledRoute`` and did not meander, and a length-matched section
between two pair insertions did not route), each section carries its own tag
and rule, the delay window cannot be met by the straight path, the staggered
chips start their pairs out of skew, and neighbouring envelopes stay apart.
Each expected value is worked out from the parts, constraints and structure
the tests read.

The runtime tests submit the design, capture it and measure the realized
sections against the constraints and against each section's rule. They need a
JITX runtime started from the repository root and ``JITX_PATTERN_RUNTIME=1``.
"""

from __future__ import annotations

import math
from itertools import pairwise
import os
import unittest
from typing import Any, ClassVar

import jitx
import shapely

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_js1_hdi_stackup.py
# uses it for the same reason).
from jitx._translate.design import package_design
from jitx.circuit import Route
from jitx.component import Component
from jitx.constraints import UnaryDesignConstraint
from jitx.controlpoint import PairPoint
from jitx.inspect import extract
from jitx.landpattern import Pad
from jitx.sample import SampleSubstrate
from jitx.shapes import Shape
from jitx.shapes.primitive import Arc, ArcPolyline
from jitx.shapes.shapely import ShapelyGeometry
from jitx.test import TestCase
from shapely.geometry import LineString

from jitxexamples.patterns.serpentine_sections import (
    PAIR_DELAY,
    PAIR_SKEW,
    ExampleStaggeredPairChip,
    SerpentineSections,
    serpentine_sections_design,
)

RUNTIME = os.environ.get("JITX_PATTERN_RUNTIME") == "1"

ARC_TOLERANCE = 1e-4
"""How far polygonized copper may stray from its arcs, in mm. The default of
0.01 mm moves a meander's edge by more than the 1 um the envelope test reads
the copper's extent to."""


def _circuit() -> SerpentineSections:
    circuit = serpentine_sections_design().circuit
    assert isinstance(circuit, SerpentineSections)
    return circuit


def _xy(obj: Component | Pad | PairPoint) -> tuple[float, float]:
    assert obj.transform is not None
    x, y = obj.transform.translation
    return float(x), float(y)


def _pad_xs(chip: Component) -> list[float]:
    """x of each of the chip's pads, on the board."""
    return [_xy(chip)[0] + _xy(pad)[0] for pad in extract(chip, Pad)]


def _start_point(circuit: SerpentineSections, section: Route) -> PairPoint:
    """The pair point the section starts at, found from the route itself."""
    (start,) = [
        point
        for points in circuit.controls
        for point in points
        if isinstance(point, PairPoint) and point.front is section.source
    ]
    return start


def _sections_by_row() -> dict[float, tuple[Any, list[tuple[str, Any]]]]:
    """For each length-matched route request in the translated design, keyed
    by the y of its first control point: the request, and the name and effect
    of every design rule keyed on its tags."""
    design = package_design(serpentine_sections_design()).v1
    (top,) = [m for m in design.modules if m.id == design.module]
    points = {getattr(cp, cp.WhichOneof("type")).id: cp for cp in top.control_points}
    tags = {a.local.path[0]: {t.name for t in a.tags} for a in top.apply_tags}
    out: dict[float, tuple[Any, list[tuple[str, Any]]]] = {}
    for request in top.route_requests:
        if not request.config.squiggle_room:
            continue
        names = tags.get(request.id, set())
        effects = [
            (rule.name, effect)
            for rule in design.design_rules
            if {c.atom_expr.atom.user.name for c in rule.conditions} <= names
            for effect in rule.effects
        ]
        start = points[request.src.path[0]]
        y = getattr(start, start.WhichOneof("type")).pose.center.y
        out[y] = (request, effects)
    return out


class TestSerpentineSections(TestCase):
    def setUp(self) -> None:
        self.c = _circuit()
        self.layer = SampleSubstrate().DRS_100.layers[0]

    def test_sections_are_length_matched_between_pair_points(self) -> None:
        design = package_design(serpentine_sections_design()).v1
        (top,) = [m for m in design.modules if m.id == design.module]
        kinds = {
            getattr(cp, cp.WhichOneof("type")).id: cp.WhichOneof("type")
            for cp in top.control_points
        }
        sections = [r for r in top.route_requests if r.config.squiggle_room > 0]
        self.assertEqual(len(sections), len(self.c.tx))
        for request in sections:
            self.assertEqual(kinds.get(request.src.path[0]), "pair")
            self.assertEqual(kinds.get(request.dst.path[0]), "pair")

    def test_each_section_has_its_own_tag_and_rule(self) -> None:
        sections = _sections_by_row()
        self.assertEqual(len(sections), len(self.c.tx))
        settings = []
        for i, section in enumerate(self.c.sections):
            # The request is found from the route's own start point, so the
            # check holds for any order of rows.
            y = _xy(_start_point(self.c, section))[1]
            with self.subTest(y=y):
                _, effects = sections[y]
                self.assertEqual(len(effects), 1)
                ((name, effect),) = effects
                # The runtime tests read the rule of ``sections[i]`` as
                # ``rules[i]``; the translator names that rule as below.
                self.assertEqual(name, f"circuit.rules[{i}]")
                self.assertIn(
                    effect.WhichOneof("effect"),
                    {"serpentine_params", "coupled_pair_params"},
                )
                settings.append(effect.SerializeToString(deterministic=True))
        self.assertEqual(len(set(settings)), len(settings))

    def test_straight_path_is_too_short_for_the_delay_window(self) -> None:
        for tx, rx in zip(self.c.tx, self.c.rx, strict=True):
            longest = max(_pad_xs(rx)) - min(_pad_xs(tx))
            self.assertLess(longest / self.layer.velocity, PAIR_DELAY.min_value)

    def test_staggered_chips_start_their_pair_out_of_skew(self) -> None:
        staggered = [tx for tx in self.c.tx if isinstance(tx, ExampleStaggeredPairChip)]
        bump_rows = [
            y
            for y, (_, effects) in _sections_by_row().items()
            if any(e.WhichOneof("effect") == "coupled_pair_params" for _, e in effects)
        ]
        self.assertEqual(sorted(_xy(tx)[1] for tx in staggered), sorted(bump_rows))
        for tx in staggered:
            xs = _pad_xs(tx)
            self.assertGreater((max(xs) - min(xs)) / self.layer.velocity, PAIR_SKEW)

    def test_neighbouring_envelopes_stay_apart(self) -> None:
        rows = sorted(_sections_by_row().items())
        pair = 2 * self.layer.trace_width + self.layer.pair_spacing
        clearance = self.layer.clearance
        assert clearance is not None
        for (y0, (r0, _)), (y1, (r1, _)) in pairwise(rows):
            reach = (pair + r0.config.squiggle_room) / 2
            reach += (pair + r1.config.squiggle_room) / 2
            self.assertGreaterEqual(y1 - y0, reach + clearance)


def _arcs(trace: Any) -> list[Arc]:
    arcs: list[Arc] = []
    for shape in trace.shapes:
        line = shape.geometry if isinstance(shape, Shape) else shape
        assert isinstance(line, ArcPolyline), type(line)
        arcs += [e for e in line.elements if isinstance(e, Arc)]
    return arcs


def _centreline(trace: Any) -> LineString:
    points: list[tuple[float, float]] = []
    for shape in trace.shapes:
        line = shape.geometry if isinstance(shape, Shape) else shape
        assert isinstance(line, ArcPolyline)
        for element in line.elements:
            if isinstance(element, Arc):
                cx, cy = element.center
                steps = max(2, math.ceil(abs(element.arc) / 5))
                for i in range(steps + 1):
                    t = math.radians(element.start + element.arc * i / steps)
                    r = element.radius
                    points.append((cx + r * math.cos(t), cy + r * math.sin(t)))
            else:
                points.append((float(element[0]), float(element[1])))
    return LineString(points)


def _bumps(arcs: list[Arc], radius: float) -> list[list[Arc]]:
    """Deskew bumps: runs of consecutive arcs of ``radius``, four arcs to a
    bump."""
    bumps: list[list[Arc]] = []
    run: list[Arc] = []
    for arc in [*arcs, None]:
        if arc is not None and abs(arc.radius - radius) < 1e-3:
            run.append(arc)
            continue
        assert len(run) % 4 == 0, f"{len(run)} bump arcs do not make whole bumps"
        bumps += [run[i : i + 4] for i in range(0, len(run), 4)]
        run = []
    return bumps


@unittest.skipUnless(RUNTIME, "needs a JITX runtime")
class TestSerpentineSectionsRuntime(TestCase):
    root: ClassVar[SerpentineSections]
    unmet: ClassVar[list[str]]
    complete: ClassVar[bool]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        with jitx.runtime as rt:
            design = rt.submit(serpentine_sections_design)
            design.capture(wait=60)
            root = design.root.circuit
            assert isinstance(root, SerpentineSections)
            cls.root = root
            report = design.issues(satisfied=True, wait=40)
            cls.complete = report.complete
            cls.unmet = [g.text for g in report.groups() if not g.satisfied]

    def setUp(self) -> None:
        self.c = type(self).root
        self.layer = SampleSubstrate().DRS_100.layers[0]

    def _rows(self) -> list[tuple[float, Route, UnaryDesignConstraint]]:
        """Each section with the y of its axis and the rule meant for it
        (``rules[i]`` for ``sections[i]``, checked offline)."""
        rows = []
        for section, rule in zip(self.c.sections, self.c.rules, strict=True):
            self.assertEqual(len(section.traces or []), 2)
            rows.append((_xy(_start_point(self.c, section))[1], section, rule))
        return rows

    def test_every_delay_and_skew_is_met(self) -> None:
        self.assertTrue(self.complete, "issue report incomplete: raise wait")
        self.assertEqual(self.unmet, [])

    def test_meander_fills_but_stays_inside_the_envelope(self) -> None:
        pair = 2 * self.layer.trace_width + self.layer.pair_spacing
        for y, section, _ in self._rows():
            with self.subTest(y=y):
                config = section.config
                assert config is not None and config.envelope_overhead is not None
                copper = shapely.union_all(
                    [
                        ShapelyGeometry.from_shape(s, tolerance=ARC_TOLERANCE).g
                        for t in section.traces or []
                        for s in t.shapes
                    ]
                )
                _, low, _, high = copper.bounds
                self.assertGreater(high - low, pair + 1e-3)
                self.assertLessEqual(high - low, pair + config.envelope_overhead + 1e-3)

    def test_min_pitch_spaces_the_meander_segments(self) -> None:
        rows = [r for r in self._rows() if r[2].serpentine_params_constraint]
        self.assertTrue(rows)
        for y, section, rule in rows:
            params = rule.serpentine_params_constraint
            assert params is not None and params.min_pitch is not None
            min_pitch = params.min_pitch
            for trace in section.traces or []:
                with self.subTest(y=y):
                    axis = LineString([(-100, y), (100, y)])
                    crossing = _centreline(trace).intersection(axis)
                    xs = sorted(p.x for p in getattr(crossing, "geoms", [crossing]))
                    gaps = [b - a for a, b in pairwise(xs)]
                    self.assertGreaterEqual(len(gaps), 2)
                    # One trace of a pair sits on the inside of each turn, so
                    # its gaps alternate short and long around the pair's
                    # pitch; each neighbouring two average to it.
                    pitches = [(a + b) / 2 for a, b in pairwise(gaps)]
                    self.assertGreaterEqual(min(pitches), min_pitch - 1e-3)

    def test_deskew_bumps_follow_their_rule(self) -> None:
        rows = [r for r in self._rows() if r[2].coupled_pair_params_constraint]
        self.assertTrue(rows)
        for y, section, rule in rows:
            params = rule.coupled_pair_params_constraint
            assert params is not None
            with self.subTest(y=y):
                traces = section.traces or []
                if params.deskew_bump_radius is not None:
                    radius = params.deskew_bump_radius
                else:
                    # Default radius: the smallest arc on the pair.
                    radius = min(a.radius for t in traces for a in _arcs(t))
                per_trace = [_bumps(_arcs(t), radius) for t in traces]
                # The bumps lengthen the shorter trace only.
                self.assertEqual(sorted(len(b) > 0 for b in per_trace), [False, True])
                (bumps,) = [b for b in per_trace if b]
                if params.min_bump_spacing is not None:
                    # A bump starts at its first arc's centre x and ends at its last
                    # arc's, so the gap between bumps is centre to centre on x.
                    gaps = [
                        nxt[0].center[0] - prev[-1].center[0]
                        for prev, nxt in pairwise(bumps)
                    ]
                    self.assertTrue(gaps)
                    self.assertGreaterEqual(min(gaps), params.min_bump_spacing - 1e-3)

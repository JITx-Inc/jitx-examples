"""Tests for applying routing structures by tag, with a neck on the escape.

Offline, the tests read the translated design: the main rule is keyed on the
net's tag, the neck rule on a tag that sits on the escape ``Route`` only, at
a higher priority. With ``JITX_PATTERN_RUNTIME=1`` and a runtime started at
the project root, the runtime test builds the design and measures each
segment against its structure's width: the higher-priority rule wins on the
segment both match (jitx ``design_constraint`` docstring: "higher priority
numbers take precedence"; measured on jitx 4.6).
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
from jitx.sample import SampleFabConstraints
from jitx.test import TestCase

from jitxexamples.patterns.layout_routing_structure_by_tag import (
    EscapeNeckTag,
    NeckedLine,
    SignalTag,
    layout_routing_structure_by_tag_design,
)


def _name(tag: type) -> str:
    return f"{tag.__module__}.{tag.__qualname__}"


class _Rules:
    """The structure rules and structure widths the layout engine receives."""

    def __init__(self) -> None:
        v1 = package_design(layout_routing_structure_by_tag_design()).v1
        widths = {s.id: s.layers[0].trace_width for s in v1.routings}
        self.by_tag = {}
        for rule in v1.design_rules:
            (effect,) = rule.effects
            if not effect.HasField("routing_structure"):
                continue
            (cond,) = rule.conditions
            self.by_tag[cond.atom_expr.atom.user.name] = (
                rule.priority,
                widths[effect.routing_structure.routing_structure],
            )
        top = next(m for m in v1.modules if m.id == v1.module)
        self.tagged = {}
        for apply in top.apply_tags:
            for tag in apply.tags:
                self.tagged.setdefault(tag.name, set()).add(tuple(apply.local.path))
        self.nets = {n.name: n.id for n in top.nets if n.name}


class TestStructureByTagOffline(TestCase):
    def setUp(self) -> None:
        self.rules = _Rules()

    def test_main_structure_is_keyed_on_the_net_tag(self) -> None:
        self.assertIn(_name(SignalTag), self.rules.by_tag)
        self.assertEqual(
            self.rules.tagged[_name(SignalTag)], {(self.rules.nets["SIG"],)}
        )

    def test_neck_rule_outranks_the_net_rule(self) -> None:
        main_priority, main_width = self.rules.by_tag[_name(SignalTag)]
        neck_priority, neck_width = self.rules.by_tag[_name(EscapeNeckTag)]
        self.assertGreater(neck_priority, main_priority)
        self.assertLess(neck_width, main_width)
        self.assertGreaterEqual(neck_width, SampleFabConstraints.min_copper_width)

    def test_neck_tag_sits_on_the_escape_route_only(self) -> None:
        tagged = self.rules.tagged[_name(EscapeNeckTag)]
        self.assertEqual(len(tagged), 1)
        (path,) = tagged
        self.assertNotIn(path, {(i,) for i in self.rules.nets.values()})
        circuit = layout_routing_structure_by_tag_design().circuit
        assert isinstance(circuit, NeckedLine)
        # The escape starts at the device pad.
        self.assertIs(circuit.escape.source, circuit.device.io)


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestStructureByTagRuntime(TestCase):
    def test_each_segment_takes_its_structure_and_none_is_missing(self) -> None:
        design = layout_routing_structure_by_tag_design
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
            text = rd.issues(satisfied=True, wait=30).text()
        # The timing constraint bound to the path, and found a structure on
        # every segment.
        self.assertIn("Time:", text)
        self.assertIn("from device.io to far.io", text)
        self.assertNotIn("Missing routing structure", text)
        circuit = rd.root.circuit
        assert isinstance(circuit, NeckedLine)

        def widths(route: jitx.circuit.Route) -> set[float]:
            return {
                round(s.geometry.width, 4)
                for t in route.traces or []
                for s in t.shapes
                if hasattr(s.geometry, "width")
            }

        self.assertEqual(
            widths(circuit.escape), {rules.by_tag[_name(EscapeNeckTag)][1]}
        )
        self.assertEqual(widths(circuit.run), {rules.by_tag[_name(SignalTag)][1]})

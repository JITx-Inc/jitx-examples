"""Tests for the fenced pour outline pattern.

The pattern needs a fence-via rule keyed on the tag and a pour that carries
the tag and is on the board's ground net. The pattern module,
``fenced_pour_outline``, also follows two conventions the tests pin: the pour
sits within the fence via's layer span, and a KeepOut, optional in the
pattern, covers the same outline. The tests read the translated design,
because that is what the layout engine receives; the isolate test also reads
the module source, for the one case the translated design cannot show.
"""

from __future__ import annotations

import ast
from pathlib import Path

from jitx import Net, Pour

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_js1_hdi_stackup.py
# uses it for the same reason).
from jitx._translate.design import package_design
from jitx.circuit import Circuit
from jitx.design import Design
from jitx.shapes.composites import rectangle
from jitx.test import TestCase

from jitxexamples.patterns import fenced_pour_outline
from jitxexamples.patterns.fenced_pour_outline import (
    FENCE_LAYER,
    FENCE_PATTERN,
    FenceOutlineTag,
    FencedOutline,
    FencedOutlineBoard,
    FencedOutlineSubstrate,
    fenced_pour_outline_design,
)

TAG_NAME = f"{FenceOutlineTag.__module__}.{FenceOutlineTag.__qualname__}"


class _BoardWithGround(Circuit):
    """A circuit that reuses the pattern and owns its own ground net."""

    def __init__(self) -> None:
        self.outline = FencedOutline()
        self.plane = Pour(rectangle(10, 10), layer=4)
        self.GND = Net([self.plane, self.outline.GND], name="GND")


class _BoardWithGroundDesign(Design):
    board = FencedOutlineBoard()
    substrate = FencedOutlineSubstrate()
    circuit = _BoardWithGround()


class TestFencedPourOutline(TestCase):
    def setUp(self) -> None:
        self.design = package_design(fenced_pour_outline_design()).v1
        modules = [m for m in self.design.modules if m.id == self.design.module]
        self.assertEqual(len(modules), 1)
        self.module = modules[0]
        pours = [g for g in self.module.net_geoms if g.geom.HasField("pour")]
        self.assertEqual(len(pours), 1, "the pattern draws exactly one pour")
        self.pour = pours[0].geom.pour
        rules = [
            r
            for r in self.design.design_rules
            if any(e.HasField("fence_via") for e in r.effects)
        ]
        self.assertEqual(len(rules), 1)
        self.rule = rules[0]
        (self.fence,) = [
            e.fence_via for e in self.rule.effects if e.HasField("fence_via")
        ]
        (self.via,) = [v for v in self.design.vias if v.name == self.fence.definition]

    def test_fence_rule_is_keyed_on_the_tag_with_the_declared_pattern(self) -> None:
        self.assertEqual(
            [c.atom_expr.atom.user.name for c in self.rule.conditions], [TAG_NAME]
        )
        self.assertEqual(
            self.fence.definition, FencedOutlineSubstrate.uGnd_L1_L3.__name__
        )
        pattern = self.fence.pattern
        self.assertEqual(
            (pattern.pitch, pattern.offset, pattern.num_rows),
            (FENCE_PATTERN.pitch, FENCE_PATTERN.offset, FENCE_PATTERN.num_rows),
        )
        # Unset, so offset is also the outline-to-first-row distance and the
        # rule fences the outline as drawn.
        self.assertFalse(pattern.HasField("initial_offset"))
        self.assertFalse(pattern.HasField("input_shape_only"))

    def test_first_row_pads_clear_the_outline(self) -> None:
        self.assertGreater(self.fence.pattern.offset - self.via.diameter / 2, 0)

    def test_pour_carries_the_tag(self) -> None:
        tagged = {
            tag.name
            for apply in self.module.apply_tags
            if list(apply.local.path) == [self.pour.id]
            for tag in apply.tags
        }
        self.assertIn(TAG_NAME, tagged)

    def test_pour_is_within_the_fence_via_layer_span(self) -> None:
        self.assertEqual(self.pour.layer.index, FENCE_LAYER)
        self.assertLessEqual(self.via.start.index, FENCE_LAYER)
        self.assertLessEqual(FENCE_LAYER, self.via.stop.index)

    def test_keepout_covers_the_pour_outline_for_pours_and_vias(self) -> None:
        copper = [k for k in self.module.layers if k.layer.HasField("forbid_copper")]
        vias = [
            k
            for k in self.module.layers
            if k.layer.HasField("forbid_region") and k.layer.forbid_region.forbid_vias
        ]
        self.assertEqual(len(copper), 1)
        self.assertEqual(len(vias), 1)
        for keepout, span in (
            (copper[0], copper[0].layer.forbid_copper),
            (vias[0], vias[0].layer.forbid_region),
        ):
            self.assertEqual((span.start.index, span.end.index), (FENCE_LAYER,) * 2)
            self.assertEqual(keepout.shape, self.pour.shape)

    def test_net_names_do_not_reuse_port_names(self) -> None:
        # The runtime rejects a module whose net reuses a port's name ("Public
        # name GND already in use"); a dry translation does not.
        ports = {p.name for p in self.module.ports}
        nets = {n.name for n in self.module.nets if n.name}
        self.assertEqual(ports & nets, set())

    def test_pour_sets_no_isolate(self) -> None:
        self.assertEqual(self.pour.isolate, 0)
        # ``isolate=0.0`` translates the same as leaving it out, so the
        # deprecated argument is also looked for in the module source.
        tree = ast.parse(Path(fenced_pour_outline.__file__).read_text())
        isolate_calls = [
            node.lineno
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and any(k.arg == "isolate" for k in node.keywords)
        ]
        self.assertEqual(isolate_calls, [])


class TestFencedOutlineJoinsBoardGround(TestCase):
    def test_parent_ground_net_reaches_the_fence_pour(self) -> None:
        design = package_design(_BoardWithGroundDesign()).v1
        modules = {m.id: m for m in design.modules}
        top = modules[design.module]
        (instance,) = [i for i in top.instances if i.name == "outline"]
        child = modules[instance.instantiable]
        (port,) = [p for p in child.ports if p.name == "GND"]

        # Inside the pattern, the fence pour is on the net that holds the port.
        port_nets = {
            n.id for n in child.nets if [port.id] in [list(r.path) for r in n.refs]
        }
        pour_nets = {g.ref.path[0] for g in child.net_geoms if g.geom.HasField("pour")}
        self.assertEqual(len(pour_nets), 1)
        self.assertLessEqual(pour_nets, port_nets)

        # In the parent, one net holds both its own ground plane and the port.
        reaching = [
            n.id
            for n in top.nets
            if [instance.id, port.id] in [list(r.path) for r in n.refs]
        ]
        plane_nets = [g.ref.path[0] for g in top.net_geoms if g.geom.HasField("pour")]
        self.assertEqual(len(reaching), 1)
        self.assertEqual(plane_nets, reaching)

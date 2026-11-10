"""Tests for the fenced pour outline pattern.

The pattern needs a fence-via rule keyed on the tag and a pour that carries
the tag and is on the board's ground net. The pattern module,
``fenced_pour_outline``, also follows two conventions the tests pin: the pour
sits within the fence via's layer span, and a KeepOut, optional in the
pattern, covers the same outline. The tests read the translated design,
because that is what the layout engine receives; the isolate test also reads
the module source, for the one case the translated design cannot show.

The cavity ring tests check the ring rule, its pitch against the fab and its
same-net anchor. The runtime tests, gated by ``JITX_PATTERN_RUNTIME=1``, read
the generated vias of both rings and check them against the drawn outline:
each centre sits the pattern's offset from it, on the side the offset's sign
gives (measured on jitx 4.6), no stretch of the offset outline is left
wider than one pitch, so the ring is closed, and the count falls in the
range ``fence_count_range`` accepts.
"""

from __future__ import annotations

import ast
import os
import shutil
import unittest
from pathlib import Path

import jitx
import shapely
from jitx import Net, Pour

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_js1_hdi_stackup.py
# uses it for the same reason).
from jitx._translate.design import package_design
from jitx.circuit import Circuit
from jitx.constraints import AtomExpr, Tags
from jitx.design import Design
from jitx.inspect import visit
from jitx.run.runtime import RuntimeDesign
from jitx.sample import SampleSubstrate
from jitx.shapes import Shape
from jitx.shapes.composites import rectangle
from jitx.shapes.shapely import ShapelyGeometry
from jitx.test import TestCase
from jitx.via import Via
from shapely.geometry.base import BaseGeometry

from jitxexamples.patterns import fenced_pour_outline
from jitxexamples.patterns.fenced_pour_outline import (
    CAVITY_LAYER,
    CAVITY_VIA,
    FENCE_LAYER,
    CavityRing,
    CavityRingTag,
    FenceOutlineTag,
    FencedOutline,
    FencedOutlineBoard,
    FencedOutlineSubstrate,
    cavity_ring_design,
    fence_count_range,
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

    def test_fence_rule_is_keyed_on_the_tag_with_a_pitch_that_keeps_the_fab(
        self,
    ) -> None:
        self.assertEqual(
            [c.atom_expr.atom.user.name for c in self.rule.conditions], [TAG_NAME]
        )
        self.assertEqual(
            self.fence.definition, FencedOutlineSubstrate.uGnd_L1_L3.__name__
        )
        pattern = self.fence.pattern
        # A pitch below the via pad is thinned to every other site with no
        # issue (measured on jitx 4.6), so the pitch has to be at least one
        # pad. The fence vias are all on GND, and clearance is not enforced
        # between copper of the same net, so the pads need no copper spacing.
        fab = FencedOutlineSubstrate.constraints
        self.assertGreaterEqual(pattern.pitch, self.via.diameter)
        # The fab sheet's drill-to-drill floor, edge to edge.
        self.assertGreaterEqual(
            pattern.pitch - self.via.hole_diameter, fab.min_hole_to_hole
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


class TestFenceCountRange(unittest.TestCase):
    """L is the offset outline's length; the counts are worked from it. The
    0.45 pad through via the counts were measured with, on this module's fab:
    its pitch floor is 0.6."""

    square = shapely.box(-4, -4, 4, 4)
    fab = FencedOutlineSubstrate.constraints

    def _range(
        self, outline: BaseGeometry, offset: float, pitch: float
    ) -> tuple[int, int]:
        return fence_count_range(
            outline, offset, pitch, SampleSubstrate.THVia, self.fab
        )

    def test_outward_offset_of_a_square_is_exact(self) -> None:
        # Offset 0.5 outward with square corners: a 9 by 9 outline, L = 36,
        # and 36 vias measured on jitx 4.6.
        self.assertEqual(self._range(self.square, 0.5, 1.0), (36, 36))

    def test_unmeasured_outward_offsets_take_the_wide_range(self) -> None:
        # Only the whole-pitch square was measured exact. A 9 by 7 outline
        # (L 32) and the 9 by 9 one at pitch 0.7 (L / pitch 51.4) take
        # floor - 1 to ceil.
        self.assertEqual(self._range(shapely.box(-4, -3, 4, 3), 0.5, 1.0), (31, 32))
        self.assertEqual(self._range(self.square, 0.5, 0.7), (50, 52))

    def test_inward_offset_accepts_one_under_to_one_over(self) -> None:
        # 0.6 inward: a 6.8 by 6.8 outline, L = 27.2, so 26 to 28; 26 vias
        # measured on jitx 4.6.
        self.assertEqual(self._range(self.square, -0.6, 1.0), (26, 28))

    def test_curved_outline_accepts_one_under_to_one_over(self) -> None:
        # A 2.5 radius circle offset 0.5 outward: L = 2 * pi * 3 = 18.85, so
        # 17 to 19; 19 vias measured on jitx 4.6.
        circle = shapely.Point(0, 0).buffer(2.5, quad_segs=64)
        self.assertEqual(self._range(circle, 0.5, 1.0), (17, 19))

    def test_a_count_is_never_negative(self) -> None:
        # A 0.2 box 0.05 in: L = 0.4, a fraction of the 0.7 pitch, so 0 or 1.
        self.assertEqual(self._range(shapely.box(0, 0, 0.2, 0.2), -0.05, 0.7), (0, 1))

    def test_refuses_a_pitch_the_runtime_thins(self) -> None:
        # Measured on jitx 4.6: at pitch 0.3 the 0.45 pad via was placed at
        # every other site.
        with self.assertRaisesRegex(ValueError, "fence pitch 0.3 mm is below"):
            self._range(self.square, 0.5, 0.3)

    def test_the_module_rings_measured_counts_fall_in_range(self) -> None:
        # Measured on jitx 4.6: 13 vias around the capsule at offset 0.2,
        # pitch 0.4; 24 inside the cavity at offset -0.5, pitch 1.0.
        capsule = shapely.LineString([(-0.4, 0), (0.4, 0)]).buffer(0.4, quad_segs=64)
        low, high = fence_count_range(
            capsule, 0.2, 0.4, FencedOutlineSubstrate.uGnd_L1_L3, self.fab
        )
        self.assertTrue(low <= 13 <= high, (low, high))
        low, high = fence_count_range(
            shapely.box(-4, -3, 4, 3), -0.5, 1.0, CAVITY_VIA, self.fab
        )
        self.assertTrue(low <= 24 <= high, (low, high))


def _exact(shape: Shape) -> BaseGeometry:
    """``shape`` with arcs split finely enough (0.1 um) to measure 5 um offsets;
    the default 10 um tolerance moves a capsule's flank by that much."""
    return ShapelyGeometry.from_shape(shape, tolerance=1e-4).g


def _generated_via_centres(rd: RuntimeDesign) -> list[tuple[float, float]]:
    """Centres of the vias the runtime generated.

    ``rd.query(Via)`` returns the generated vias together with the vias the
    design places in code (the cavity's anchor). The code-placed ones are the
    ``Via`` objects in the captured tree, which ``visit`` lists and the query
    yields as themselves, so they are left out by identity.
    """
    placed = {id(via) for _, via in visit(rd.root, Via)}
    centres = []
    for trace, via in rd.query(Via):
        if id(via) in placed:
            continue
        assert trace.transform is not None and via.transform is not None
        x, y = (trace.transform * via.transform).translation
        centres.append((x, y))
    return centres


def _ring_checks(
    case: TestCase,
    vias: list[tuple[float, float]],
    outline: BaseGeometry,
    offset: float,
    pitch: float,
) -> None:
    """Each via centre sits ``offset`` from ``outline`` (outside when positive,
    inside when negative), and every point of the offset outline is within
    half a gap of a via. A closed ring of whole vias around a ring of length
    L cannot keep the pitch exactly, so a gap may stretch to fit: rounding
    L / pitch to the nearest whole count gives at most pitch * L / (L - pitch
    / 2). Measured on jitx 4.6: 19 vias at 0.987 mm chords on an 18.85 mm
    ring at pitch 1.0."""
    case.assertGreater(len(vias), 0)
    boundary = outline.boundary
    for x, y in vias:
        point = shapely.Point(x, y)
        with case.subTest(via=(round(x, 3), round(y, 3))):
            case.assertAlmostEqual(point.distance(boundary), abs(offset), delta=0.005)
            case.assertEqual(outline.contains(point), offset < 0)
    ring = outline.buffer(offset, join_style="mitre").boundary
    centres = shapely.MultiPoint(vias)
    steps = 1000
    worst = max(
        ring.interpolate(i / steps, normalized=True).distance(centres)
        for i in range(steps)
    )
    stretched = pitch * ring.length / (ring.length - pitch / 2)
    case.assertLessEqual(worst, stretched / 2 + 0.005)


class TestCavityRing(TestCase):
    def setUp(self) -> None:
        self.design = cavity_ring_design()
        circuit = self.design.circuit
        assert isinstance(circuit, CavityRing)
        self.circuit: CavityRing = circuit
        translated = package_design(self.design).v1
        fence = self.circuit.ring_rule.fence_via_constraint
        assert fence is not None and isinstance(fence.definition, type)
        self.pattern = fence.pattern
        self.ring_via = fence.definition
        (self.via,) = [
            v for v in translated.vias if v.name == fence.definition.__name__
        ]
        self.conductors = len(self.design.substrate.stackup.conductors)

    def test_ring_rule_selects_the_cavity_pour_only(self) -> None:
        condition = self.circuit.ring_rule.condition
        assert isinstance(condition, AtomExpr)
        self.assertIsInstance(condition.atom, CavityRingTag)
        for pour, tagged in (
            (self.circuit.cavity_pour, True),
            (self.circuit.plane, False),
        ):
            tags = Tags.get(pour)
            names = {type(t) for t in tags.tags} if tags else set()
            self.assertEqual(CavityRingTag in names, tagged)

    def test_ring_sits_inside_the_outline_and_reaches_the_plane(self) -> None:
        pattern = self.pattern
        assert pattern.initial_offset is not None
        # Negative offsets put the row inside the outline (measured on jitx
        # 4.6); the pad must clear the outline to sit wholly in the cavity
        # copper.
        self.assertLess(pattern.offset, 0)
        self.assertGreaterEqual(-pattern.initial_offset, self.via.diameter / 2)
        # Via layers count from the top when non-negative and from the bottom
        # when negative (``Side.Bottom`` is -1).
        span = [
            i if i >= 0 else self.conductors + i
            for i in (int(self.ring_via.start_layer), int(self.ring_via.stop_layer))
        ]
        for layer in (CAVITY_LAYER, self.circuit.plane.layer):
            self.assertLessEqual(min(span), layer)
            self.assertLessEqual(layer, max(span))

    def test_pitch_keeps_the_fab_spacings(self) -> None:
        pitch = self.pattern.pitch
        fab = self.design.substrate.constraints
        self.assertGreaterEqual(pitch, self.via.diameter)
        self.assertGreaterEqual(pitch - self.via.hole_diameter, fab.min_hole_to_hole)

    def test_cavity_has_a_same_net_anchor_inside_it(self) -> None:
        # Generated vias do not anchor a pour (measured on jitx 4.6).
        anchor = self.circuit.anchor
        assert anchor.transform is not None
        point = shapely.Point(anchor.transform.translation)
        for pour in (self.circuit.cavity_pour, self.circuit.plane):
            self.assertTrue(pour.shape.to_shapely().g.contains(point))
        self.assertIn(anchor, self.circuit.cavity_net)


@unittest.skipUnless(
    os.environ.get("JITX_PATTERN_RUNTIME") == "1", "needs a JITX runtime"
)
class TestFenceRingsRuntime(TestCase):
    def _submit(self, design: type[Design]) -> list[tuple[float, float]]:
        root = Path(__file__).resolve().parents[1]
        shutil.rmtree(
            root / "designs" / f"{design.__module__}.{design.__qualname__}",
            ignore_errors=True,
        )
        with jitx.runtime as rt:
            rd = rt.submit(design)
            rd.capture(wait=30)
            vias = _generated_via_centres(rd)
            circuit = rd.root.circuit
            if isinstance(circuit, CavityRing):
                self.cavity_copper = circuit.cavity_pour.shape.to_shapely().g
        return vias

    def test_outline_fence_rings_the_opening_from_outside(self) -> None:
        circuit = fenced_pour_outline_design().circuit
        assert isinstance(circuit, FencedOutline)
        outline = _exact(circuit.fence_pour.shape)
        fence = FencedOutlineSubstrate.outline_fence.fence_via_constraint
        assert fence is not None
        vias = self._submit(fenced_pour_outline_design)
        _ring_checks(self, vias, outline, fence.pattern.offset, fence.pattern.pitch)
        low, high = fence_count_range(
            outline,
            fence.pattern.offset,
            fence.pattern.pitch,
            FencedOutlineSubstrate.uGnd_L1_L3,
            FencedOutlineSubstrate.constraints,
        )
        self.assertTrue(low <= len(vias) <= high, (len(vias), low, high))

    def test_cavity_ring_is_closed_inside_the_cavity_copper(self) -> None:
        circuit = cavity_ring_design().circuit
        assert isinstance(circuit, CavityRing)
        outline = _exact(circuit.cavity_pour.shape)
        fence = circuit.ring_rule.fence_via_constraint
        assert fence is not None and isinstance(fence.definition, type)
        pattern = fence.pattern
        assert pattern.initial_offset is not None
        vias = self._submit(cavity_ring_design)
        _ring_checks(self, vias, outline, pattern.initial_offset, pattern.pitch)
        low, high = fence_count_range(
            outline,
            pattern.initial_offset,
            pattern.pitch,
            fence.definition,
            FencedOutlineSubstrate.constraints,
        )
        self.assertTrue(low <= len(vias) <= high, (len(vias), low, high))
        # The ring joins the cavity copper only where each pad lies in it; a
        # cavity pour with no same-net anchor comes back empty (measured on
        # jitx 4.6).
        pad = float(fence.definition.diameter) / 2
        for x, y in vias:
            with self.subTest(pad=(round(x, 3), round(y, 3))):
                self.assertTrue(
                    self.cavity_copper.contains(shapely.Point(x, y).buffer(pad - 0.001))
                )

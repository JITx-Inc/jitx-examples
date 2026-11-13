"""The 18-layer reference substrate against the fabrication drawing it is
transcribed from.

Expected values come from the drawing's stackup table, drill charts and
backdrill charts, retyped here as the drawing gives them, and from the rules
the substrate's docstring states (IPC-2221B's 0.050 mm minimum annular ring,
the backdrill charts' "drill + 6 mil"), from the substrate-modeler
skill's rule that an uncoupled region keeps its pair's geometry, and from
the design's drilling rule, as its maintainers decided it: every blind via
is laser drilled, and every via that spans the board, backdrilled or not,
is mechanically drilled.
"""

from __future__ import annotations

from jitx.inspect import decompose
from jitx.layerindex import Side

# `_RefLayer` is private, and JITX has no public path to the planes a built
# structure layer carries from `.reference()`: they sit in a private list on
# the layer, so the plane test reads them this way.
from jitx.si import DifferentialRoutingStructure, RoutingStructure, _RefLayer
from jitx.stackup import Conductor, Dielectric, Material
from jitx.test import TestCase
from jitx.via import BackdrillSet, Via, ViaDiameter, ViaType

from jitxexamples.substrates.reference_18layer import (
    Reference18Stackup,
    Reference18Substrate,
    nearest_plane_height,
)

MM_PER_MIL = 0.0254

DRAWING_LAYERS = (
    "TOP",
    "L2_GND",
    "L3_SIG1",
    "L4_GND",
    "L5_SIG2",
    "L6_GND",
    "L7_SIG3",
    "L8_GND_1OZ",
    "L9_PWR1_2OZ",
    "L10_PWR2_2OZ",
    "L11_GND_1OZ",
    "L12_SIG4",
    "L13_GND",
    "L14_SIG5",
    "L15_GND",
    "L16_SIG6",
    "L17_GND",
    "BOTTOM",
)
"The drawing's copper layer names, layers 1 to 18, top to bottom."

TOTAL_THICKNESS_MIL = 65.83
"The stackup table's TOTAL THICKNESS. The drawing gives it no tolerance."

DRILL_CHARTS: dict[str, tuple[str, str, float]] = {
    "MicroVia_TOP_L2": ("TOP", "L2_GND", 6.0),
    "MicroVia_L17_BOTTOM": ("L17_GND", "BOTTOM", 6.0),
    "BlindVia_TOP_L3_6p9": ("TOP", "L3_SIG1", 6.9),
    "BlindVia_TOP_L3_8p0": ("TOP", "L3_SIG1", 8.0),
    "BlindVia_TOP_L3_10p0": ("TOP", "L3_SIG1", 10.0),
    "BlindVia_L16_BOTTOM_6p9": ("L16_SIG6", "BOTTOM", 6.9),
    "BlindVia_L16_BOTTOM_10p0": ("L16_SIG6", "BOTTOM", 10.0),
    "THVia_6p0": ("TOP", "BOTTOM", 6.0),
    "THVia_10p0": ("TOP", "BOTTOM", 10.0),
}
"""Drill charts TOP to L2, L17 to BOTTOM, TOP to L3, L16_SIG6 to BOTTOM and
TOP to BOTTOM: each via's span and finished drill in mils."""

BACKDRILL_CHARTS: dict[str, tuple[str, str]] = {
    "BackdrilledVia_TOP_L3": ("BOTTOM", "L3_SIG1"),
    "BackdrilledVia_TOP_L5": ("BOTTOM", "L5_SIG2"),
    "BackdrilledVia_TOP_L7": ("BOTTOM", "L7_SIG3"),
    "BackdrilledVia_TOP_L12": ("BOTTOM", "L12_SIG4"),
    "BackdrilledVia_TOP_L14": ("BOTTOM", "L14_SIG5"),
    "BackdrilledVia_L3_BOTTOM": ("TOP", "L3_SIG1"),
    "BackdrilledVia_L5_BOTTOM": ("TOP", "L5_SIG2"),
    "BackdrilledVia_L7_BOTTOM": ("TOP", "L7_SIG3"),
    "BackdrilledVia_L12_BOTTOM": ("TOP", "L12_SIG4"),
}
"""Backdrill charts: the side each backdrill starts from and its must-not-cut
layer. A via backdrilled from BOTTOM connects TOP to the must-not-cut layer;
one backdrilled from TOP connects the must-not-cut layer to BOTTOM."""

BACKDRILL_OVERSIZE_MM = 6.0 * MM_PER_MIL
"Backdrill charts' note: BACKDRILL SIZE IS DRILL+6 MIL."

IPC_MIN_ANNULAR_RING_MM = 0.050
"IPC-2221B section 9.1.1, the pad rule the substrate's docstring states."

INNER_CORE_MIL = 2.5
"""The stackup table's 1078 core: 2.50 mil, on one side of every inner signal
layer, with 1078 RC63% prepreg of 2.62 to 2.75 mil on the other."""

FPGA_BALL_PITCH_MM = 0.92
"AMD AM013, package dimensions for NFVI1369: ball pitch e = 0.92 BASIC."


def layer_number(index: int | Side) -> int:
    """A via or plane layer index as a 0-based position in DRAWING_LAYERS."""
    if isinstance(index, Side):
        return 0 if index == Side.Top else len(DRAWING_LAYERS) - 1
    return index if index >= 0 else len(DRAWING_LAYERS) + index


def via_classes() -> dict[str, type[Via]]:
    return {
        name: value
        for name, value in vars(Reference18Substrate).items()
        if isinstance(value, type) and issubclass(value, Via)
    }


class TestStackup(TestCase):
    def test_layer_count_and_order(self) -> None:
        layers = list(decompose(Reference18Stackup(), Material))
        # Soldermask, then copper and dielectric alternating, then soldermask.
        self.assertEqual(len(layers), 2 * len(DRAWING_LAYERS) + 1)
        for i, layer in enumerate(layers):
            with self.subTest(entry=i):
                expect_copper = i % 2 == 1
                self.assertEqual(isinstance(layer, Conductor), expect_copper)
                self.assertEqual(isinstance(layer, Dielectric), not expect_copper)
        copper = [layer.name for layer in layers if isinstance(layer, Conductor)]
        self.assertEqual(copper, list(DRAWING_LAYERS))

    def test_total_thickness(self) -> None:
        """The table's rows sum to its total exactly, so the tolerance is
        floating-point rounding only."""
        layers = decompose(Reference18Stackup(), Material)
        total = sum(layer.thickness or 0.0 for layer in layers)
        self.assertAlmostEqual(total, TOTAL_THICKNESS_MIL * MM_PER_MIL, delta=1e-9)


class TestVias(TestCase):
    def test_every_via_has_a_chart(self) -> None:
        self.assertEqual(set(via_classes()), {*DRILL_CHARTS, *BACKDRILL_CHARTS})

    def test_drill_chart_spans_and_sizes(self) -> None:
        vias = via_classes()
        for name, (start, stop, drill) in DRILL_CHARTS.items():
            via = vias[name]
            with self.subTest(via=name):
                self.assertEqual(DRAWING_LAYERS[layer_number(via.start_layer)], start)
                self.assertEqual(DRAWING_LAYERS[layer_number(via.stop_layer)], stop)
                self.assertAlmostEqual(
                    via.hole_diameter, drill * MM_PER_MIL, delta=1e-9
                )
                self.assertIsNone(via.backdrill)

    def test_blind_vias_laser_drilled_the_rest_mechanical(self) -> None:
        """The drilling rule: a via whose drill chart span stops short of
        the far outer layer is blind and laser drilled; every via that
        spans TOP to BOTTOM, and every backdrilled via, is mechanical."""
        vias = via_classes()
        for name, (start, stop, _) in DRILL_CHARTS.items():
            blind = {start, stop} != {"TOP", "BOTTOM"}
            expected = ViaType.LaserDrill if blind else ViaType.MechanicalDrill
            with self.subTest(via=name):
                self.assertEqual(vias[name].type, expected)
        for name in BACKDRILL_CHARTS:
            with self.subTest(via=name):
                self.assertEqual(vias[name].type, ViaType.MechanicalDrill)

    def test_every_layer_pair_a_via_joins_has_a_delay_model(self) -> None:
        """A pair with no model takes JITX's placeholder and leaves any timed
        route through the via unresolved, so the substrate models them all."""
        for name, via in via_classes().items():
            a = layer_number(via.start_layer)
            b = layer_number(via.stop_layer)
            pairs = {(i, j) for i in range(a, b + 1) for j in range(i + 1, b + 1)}
            with self.subTest(via=name):
                self.assertEqual(set(via.models), pairs)
                for model in via.models.values():
                    self.assertGreater(model.delay.typ, 0.0)

    def test_backdrill_chart_spans_and_sides(self) -> None:
        vias = via_classes()
        for name, (side, keep) in BACKDRILL_CHARTS.items():
            via = vias[name]
            with self.subTest(via=name):
                span = (
                    DRAWING_LAYERS[layer_number(via.start_layer)],
                    DRAWING_LAYERS[layer_number(via.stop_layer)],
                )
                expected = ("TOP", keep) if side == "BOTTOM" else (keep, "BOTTOM")
                self.assertEqual(span, expected)
                bd = via.backdrill
                assert isinstance(bd, BackdrillSet)
                drilled, untouched = (
                    (bd.bottom, bd.top) if side == "BOTTOM" else (bd.top, bd.bottom)
                )
                self.assertIsNotNone(drilled)
                self.assertIsNone(untouched)

    def test_backdrilled_signal_layer_keeps_its_pad(self) -> None:
        """The must-not-cut layer is where the signal leaves a backdrilled
        via, so its pad is not a removable unused pad (note 9): it is set as
        a plain pad of at least the IPC minimum ring, with no ``nfp``."""
        vias = via_classes()
        for name, (_side, keep) in BACKDRILL_CHARTS.items():
            via = vias[name]
            index = DRAWING_LAYERS.index(keep)
            with self.subTest(via=name):
                pads = {
                    layer_number(k): v
                    for k, v in via.diameters.items()
                    if isinstance(k, int)
                }
                pad = pads.get(index)
                assert isinstance(pad, float)
                self.assertGreaterEqual(
                    (pad - via.hole_diameter) / 2, IPC_MIN_ANNULAR_RING_MM - 1e-9
                )

    def test_backdrill_is_drill_plus_6_mil(self) -> None:
        vias = via_classes()
        for name in BACKDRILL_CHARTS:
            via = vias[name]
            bd = via.backdrill
            assert isinstance(bd, BackdrillSet)
            for drill in (bd.top, bd.bottom):
                if drill is None:
                    continue
                with self.subTest(via=name):
                    self.assertAlmostEqual(
                        drill.diameter,
                        via.hole_diameter + BACKDRILL_OVERSIZE_MM,
                        delta=1e-9,
                    )

    def test_annular_ring_meets_the_ipc_minimum(self) -> None:
        for name, via in via_classes().items():
            diameter = via.diameter
            assert isinstance(diameter, ViaDiameter)
            with self.subTest(via=name):
                self.assertGreaterEqual(
                    (diameter.pad - via.hole_diameter) / 2,
                    IPC_MIN_ANNULAR_RING_MM - 1e-9,
                )

    def test_unused_internal_pads_are_removed(self) -> None:
        """Drawing note 9: "REMOVE ALL UNUSED PADS FROM INTERNAL LAYERS".
        Every via's non-functional pad is no larger than its hole: the pad
        is gone, not shrunk."""
        for name, via in via_classes().items():
            diameter = via.diameter
            with self.subTest(via=name):
                assert isinstance(diameter, ViaDiameter)
                assert diameter.nfp is not None
                self.assertLessEqual(diameter.nfp, via.hole_diameter + 1e-9)


class TestReferencePlanes(TestCase):
    def test_planes_are_the_adjacent_ground_layers(self) -> None:
        """Every layer of every built routing structure, coupled and
        uncoupled, references the ground layers next to it in the drawing's
        layer list: one for TOP and BOTTOM, two for an inner layer."""
        substrate = Reference18Substrate()
        pairs = list(decompose(substrate, DifferentialRoutingStructure))
        structures: list[RoutingStructure | DifferentialRoutingStructure] = [
            *decompose(substrate, RoutingStructure),
            *pairs,
            *(p.uncoupled_region for p in pairs if p.uncoupled_region is not None),
        ]
        self.assertTrue(structures)
        for structure in structures:
            for index, layer in structure.layers.items():
                position = layer_number(index)
                expected = {
                    DRAWING_LAYERS[n]
                    for n in (position - 1, position + 1)
                    if 0 <= n < len(DRAWING_LAYERS) and "GND" in DRAWING_LAYERS[n]
                }
                planes = {
                    DRAWING_LAYERS[layer_number(ref.layer)]
                    for ref in decompose(layer, _RefLayer)
                }
                with self.subTest(structure=structure.name, layer=index):
                    self.assertEqual(len(expected), 1 if position in (0, 17) else 2)
                    self.assertEqual(planes, expected)


class TestUncoupledRegions(TestCase):
    def test_uncoupled_region_keeps_the_pair_geometry(self) -> None:
        """A pair's uncoupled region keeps the coupled trace width and the
        differential clearance on every layer the pair has, the
        substrate-modeler skill's rule for an uncoupled region: the geometry
        does not change where the pair splits, and each leg is still spaced
        as half of a pair."""
        substrate = Reference18Substrate()
        pairs = list(decompose(substrate, DifferentialRoutingStructure))
        self.assertTrue(pairs)
        for pair in pairs:
            with self.subTest(structure=pair.name):
                region = pair.uncoupled_region
                assert isinstance(region, RoutingStructure)
                self.assertEqual(set(region.layers), set(pair.layers))
                for index, coupled in pair.layers.items():
                    uncoupled = region.layers[index]
                    self.assertEqual(uncoupled.trace_width, coupled.trace_width)
                    self.assertEqual(uncoupled.clearance, coupled.clearance)


class TestBallField(TestCase):
    def test_nearest_plane_is_the_inner_core(self) -> None:
        """Every inner signal layer's nearest plane is across the 1078 core,
        the thinner of its two dielectrics in the stackup table."""
        for position, name in enumerate(DRAWING_LAYERS):
            if "SIG" not in name:
                continue
            with self.subTest(layer=name):
                self.assertAlmostEqual(
                    nearest_plane_height(position), INNER_CORE_MIL * MM_PER_MIL
                )

    def test_field_pair_fits_between_through_via_pads(self) -> None:
        """Between two adjacent 10.0 mil through vias at the FPGA's ball
        pitch, the ball-field pair structure fits as the reference board
        routes it: one coupled pair, with the structure's clearance to each
        pad. The pad is the drill chart's 10.0 mil hole plus IPC-2221B's
        ring on each side."""
        pad = 10.0 * MM_PER_MIL + 2 * IPC_MIN_ANNULAR_RING_MM
        gap = FPGA_BALL_PITCH_MM - pad
        substrate = Reference18Substrate()
        pair = substrate.DRS_85_FIELD
        self.assertTrue(pair.layers)
        for index, layer in pair.layers.items():
            with self.subTest(structure=pair.name, layer=index):
                assert layer.trace_width is not None
                assert layer.pair_spacing is not None and layer.clearance is not None
                self.assertLessEqual(
                    2 * layer.trace_width + layer.pair_spacing + 2 * layer.clearance,
                    gap,
                )

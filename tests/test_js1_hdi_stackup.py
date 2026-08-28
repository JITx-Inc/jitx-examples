"""Cross-check the substrate against the fab report it was built from.

These tests read the CSV and compare it to the *translated* design, not to
hard-coded copies of the same numbers. If the report is re-issued, the tests
follow it automatically and fail wherever ``board.py`` has not been updated to
match — which is the whole point: the fab report is the ground truth, and the
code is only correct insofar as it agrees with it.

The CSV lives at ``js1-stackup-components/part1-stackup/`` — one copy for the
whole kit, shared with the runbook. It is located by walking up from this file.
"""

from __future__ import annotations

import csv
from functools import cache
from pathlib import Path

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point. Logged under "API
# findings" in internal/kits/js1-stackup-components/TODO.md.
from jitx._translate.design import package_design
from jitx.inspect import decompose

# `_RefLayer` is private; `RoutingStructure.Layer` exposes no public accessor
# for the planes carried by `.reference()`. Logged with the other private-
# surface uses under "API findings" in internal/kits/js1-stackup-components/.
from jitx.si import RoutingStructure, _RefLayer
from jitx.stackup import Conductor, Dielectric, Material
from jitx.substrate import FabricationConstraints
from jitx.test import TestCase
from jitx.units import ohm
from jitx.via import Via, ViaType
from jitxlib.physics import phase_velocity

from jitxexamples.jumpstart_kits.js1_stackup_components.hdi_stackup.board import (
    HDIFabRules,
    HDIStackup,
    HDISubstrate,
    REFERENCE_PLANES,
    REF_PLANE_WIDTH,
)
from jitxexamples.jumpstart_kits.js1_stackup_components.hdi_stackup.main import (
    HDIStackupDesign,
)

CSV_NAME = "JS1_Part1_Fab-Stackup.csv"
N_COPPER = 20

_SIDE_TOP = 0
"""Proto ``Side`` enum value for TOP. Asserted against the descriptor by
:meth:`TestVias.test_side_enum_matches_descriptor` rather than trusted."""

# CSV VIAS.Structure -> the Via subclass name prefix used in board.py.
_VIA_PREFIX = {"Microvia": "MicroVia", "Buried": "BuriedVia", "Through": "THVia"}


def _find_csv() -> Path:
    """Locate the shared fab report by walking up from this file."""
    rel = Path("jumpstart-kits/js1-stackup-components/part1-stackup") / CSV_NAME
    for parent in Path(__file__).resolve().parents:
        candidate = parent / rel
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"{CSV_NAME} not found in any ancestor 'part1-stackup/' directory. These "
        "tests cross-check against the shared fab report at "
        "js1-stackup-components/part1-stackup/ — run them from inside the kit repo."
    )


@cache
def sections() -> dict[str, list[dict[str, str]]]:
    """Parse the CSV into ``{section name: [row dicts]}``."""
    out: dict[str, list[dict[str, str]]] = {}
    name: str | None = None
    header: list[str] | None = None
    with _find_csv().open(newline="", encoding="utf-8") as handle:
        for raw in csv.reader(handle):
            if not raw or not any(cell.strip() for cell in raw):
                continue
            if raw[0] == "SECTION":
                name, header = raw[1], None
                out[name] = []
            elif name is None:
                continue
            elif header is None:
                header = raw
            else:
                out[name].append(dict(zip(header, raw, strict=True)))
    return out


@cache
def document() -> dict[str, str]:
    return {row["Field"]: row["Value"] for row in sections()["DOCUMENT"]}


@cache
def materials() -> dict[str, dict[str, str]]:
    """Material_ID / Copper_ID -> its declaring row."""
    out = {r["Material_ID"]: r for r in sections()["MATERIALS_DIELECTRIC"]}
    out.update({r["Copper_ID"]: r for r in sections()["MATERIALS_COPPER"]})
    return out


@cache
def fab_rules() -> dict[str, float]:
    """JITX attribute name -> value in mm, for rows that map to a JITX field."""
    return {
        r["JITX_attribute"]: float(r["Value_mm"])
        for r in sections()["FAB_RULES"]
        if r["JITX_attribute"]
    }


def capability(rule: str) -> str:
    """A FAB_RULES row that has no JITX field — returned as written."""
    for row in sections()["FAB_RULES"]:
        if row["Rule"] == rule:
            return row["Value_mm"]
    raise KeyError(rule)


@cache
def translated():
    """The design as JITX translates it. Requires an instantiation context."""
    return package_design(HDIStackupDesign()).v1


def layer_number(index: int, side: int) -> int:
    """Proto (index, side) -> 1-based layer number."""
    return index + 1 if side == _SIDE_TOP else N_COPPER - index


def signed_to_layer(index: int) -> int:
    """A signed conductor index as written in board.py -> layer number."""
    return (index if index >= 0 else index + N_COPPER) + 1


def stackup_span_mm(
    from_layer: str, to_layer: str, *, include_end_foils: bool
) -> float:
    """Thickness between two copper layers, summed from the STACKUP rows.

    ``include_end_foils`` picks between the report's two depth conventions,
    which its NOTES spell out: a mechanical drill's depth is the full drilled
    depth including the copper at both ends, a laser microvia's is the ablated
    dielectric alone.
    """
    rows = sections()["STACKUP"]
    position = {row["Layer"]: index for index, row in enumerate(rows) if row["Layer"]}
    first, last = sorted((position[from_layer], position[to_layer]))
    span = rows[first : last + 1] if include_end_foils else rows[first + 1 : last]
    return sum(float(row["Thickness_mm"]) for row in span)


@cache
def csv_reference_planes() -> dict[int, tuple[int, ...]]:
    """Routing layer number -> its plane numbers, per IMPEDANCE ``Ref_layers``.

    The column is written two ways. The microstrip rows name their routing layer
    inline — ``L2 for L1; L19 for L20`` — while the stripline rows are positional
    against the row's own ``Layers`` column, so ``L2+L4; L4+L6; ...`` pairs with
    ``L3;L5;...``.
    """
    out: dict[int, tuple[int, ...]] = {}
    for row in sections()["IMPEDANCE"]:
        if not row["Ref_layers"]:
            continue
        layers = [name.strip() for name in row["Layers"].split(";")]
        for index, group in enumerate(row["Ref_layers"].split(";")):
            planes, separator, target = group.strip().partition(" for ")
            if not separator:
                target = layers[index]
            key = int(target.strip().removeprefix("L"))
            numbers = tuple(
                int(plane.strip().removeprefix("L")) for plane in planes.split("+")
            )
            if out.setdefault(key, numbers) != numbers:
                raise ValueError(
                    f"L{key} is given two different reference sets by the report: "
                    f"{out[key]} and {numbers}"
                )
    return out


class TestStackup(TestCase):
    def test_layer_count_and_order(self):
        layers = list(decompose(HDIStackup(), Material))
        rows = sections()["STACKUP"]
        self.assertEqual(len(layers), len(rows), "one stackup entry per CSV row")
        self.assertEqual(len(rows), 41)

        for row, layer in zip(rows, layers, strict=True):
            with self.subTest(seq=row["Seq"], layer=row["Layer"] or row["Function"]):
                expect_conductor = row["Type"] == "Copper"
                self.assertEqual(isinstance(layer, Conductor), expect_conductor)
                self.assertEqual(isinstance(layer, Dielectric), not expect_conductor)
                self.assertAlmostEqual(
                    layer.thickness or 0.0, float(row["Thickness_mm"]), places=6
                )

    def test_copper_layers_named_by_function(self):
        conductors = [
            layer
            for layer in decompose(HDIStackup(), Material)
            if isinstance(layer, Conductor)
        ]
        self.assertEqual(len(conductors), int(document()["Layer count"]))
        self.assertEqual(len(conductors), N_COPPER)

        copper_rows = [r for r in sections()["STACKUP"] if r["Type"] == "Copper"]
        for row, layer in zip(copper_rows, conductors, strict=True):
            with self.subTest(layer=row["Layer"]):
                # "L3-Signal" / "L2-GND" — the CSV layer id must lead the name so
                # the UI cross-section reads in the report's own terms.
                self.assertIsNotNone(layer.name)
                self.assertTrue(
                    (layer.name or "").startswith(row["Layer"] + "-"),
                    f"{layer.name!r} should start with {row['Layer']!r}",
                )

    def test_thickness_totals_match_document(self):
        layers = list(decompose(HDIStackup(), Material))
        overall = sum(layer.thickness or 0.0 for layer in layers)
        mask = sum(
            layer.thickness or 0.0
            for layer, row in zip(layers, sections()["STACKUP"], strict=True)
            if row["Type"] == "Soldermask"
        )
        # Both totals reconcile exactly, so compare exactly rather than with a
        # tolerance — a tolerance would hide the transcription slip this test
        # exists to catch.
        self.assertAlmostEqual(
            overall, float(document()["Overall thickness"]), places=6
        )
        self.assertAlmostEqual(
            overall - mask, float(document()["Finished thickness"]), places=6
        )

    def test_material_properties_match_csv(self):
        """Dk, Df and roughness per layer, including the unit conversions."""
        proto_layers = translated().stackups[0].layers
        by_id = {m.id: m for m in translated().materials}
        rows = sections()["STACKUP"]
        self.assertEqual(len(proto_layers), len(rows))

        for row, proto in zip(rows, proto_layers, strict=True):
            material = by_id[proto.material]
            declared = materials()[row["Material_ID"]]
            with self.subTest(seq=row["Seq"], material=row["Material_ID"]):
                if row["Type"] == "Copper":
                    # Rz is quoted in um on the matte side; JITX wants mm.
                    self.assertAlmostEqual(
                        material.roughness,
                        float(declared["Rz_matte_um"]) / 1000.0,
                        places=6,
                    )
                    # oz is nominal; the electrical model uses finished thickness.
                    self.assertAlmostEqual(
                        proto.thickness,
                        float(declared["Finished_thickness_mm"]),
                        places=6,
                    )
                else:
                    self.assertAlmostEqual(
                        material.dielectric_coefficient, float(row["Dk"]), places=6
                    )
                    self.assertAlmostEqual(
                        material.loss_tangent, float(row["Df"]), places=6
                    )

    def test_distinct_dielectrics_are_not_collapsed(self):
        """D-BU and D-BOND share a thickness but differ in Dk — one class each.

        This is the row pair a careless transcription merges: same 0.100 mm
        pressed thickness, different glass style, different Dk.
        """
        build_up, bonding = materials()["D-BU"], materials()["D-BOND"]
        self.assertEqual(build_up["Thickness_mm"], bonding["Thickness_mm"])
        self.assertNotEqual(build_up["Dk"], bonding["Dk"])

        declared = sections()["MATERIALS_DIELECTRIC"]
        material_type = translated().materials[0].DESCRIPTOR.fields_by_name["type"]
        assert material_type.enum_type is not None
        dielectric = material_type.enum_type.values_by_name["DIELECTRIC"].number
        built = {
            (round(m.dielectric_coefficient, 6), round(m.loss_tangent, 6))
            for m in translated().materials
            if m.type == dielectric
        }
        # Every declared (Dk, Df) pair survives into the design...
        for row in declared:
            with self.subTest(material=row["Material_ID"]):
                self.assertIn(
                    (round(float(row["Dk"]), 6), round(float(row["Df"]), 6)), built
                )
        # ...and there are exactly as many distinct ones as the report declares,
        # so nothing was merged and nothing was invented.
        self.assertEqual(len(built), len(declared))

    def test_mirror_symmetry(self):
        """Built without `Symmetric`, so symmetry is a property to verify."""
        layers = list(decompose(HDIStackup(), Material))
        inner = layers[1:-1]  # drop the two soldermask entries
        for i, layer in enumerate(inner):
            mirror = inner[len(inner) - 1 - i]
            with self.subTest(index=i):
                self.assertIs(type(layer), type(mirror))
                self.assertAlmostEqual(
                    layer.thickness or 0.0, mirror.thickness or 0.0, places=6
                )


class TestVias(TestCase):
    def via_classes(self) -> dict[str, type[Via]]:
        # vars(), not dir()+getattr(): class-level access to `stackup` and the
        # routing structures resolves through the substrate's magic context and
        # raises ContextMissingException outside a design. The raw __dict__ has
        # the nested Via classes untouched.
        return {
            name: value
            for name, value in vars(HDISubstrate).items()
            if isinstance(value, type) and issubclass(value, Via)
        }

    def test_side_enum_matches_descriptor(self):
        """`layer_number` reads `_SIDE_TOP` as an integer — check that holds."""
        start = translated().vias[0].start
        side = start.DESCRIPTOR.fields_by_name["side"].enum_type
        assert side is not None
        self.assertEqual(side.values_by_name["TOP"].number, _SIDE_TOP)
        self.assertNotEqual(side.values_by_name["BOTTOM"].number, _SIDE_TOP)

    def test_inventory_is_exactly_the_csv_via_table(self):
        rows = sections()["VIAS"]
        expected = {
            f"{_VIA_PREFIX[r['Structure']]}_{r['From_layer']}_{r['To_layer']}"
            for r in rows
        }
        self.assertEqual(set(self.via_classes()), expected)
        # Every Via class on a substrate is auto-registered on the board, so the
        # count in the translated design must match the report exactly — there
        # is no way to define a via "for later".
        self.assertEqual(len(translated().boards[0].vias), len(rows))
        self.assertEqual(len(translated().vias), len(rows))

    def test_geometry_matches_csv(self):
        by_name = {v.name: v for v in translated().vias}
        for row in sections()["VIAS"]:
            name = (
                f"{_VIA_PREFIX[row['Structure']]}_{row['From_layer']}_{row['To_layer']}"
            )
            via = by_name[name]
            with self.subTest(via=row["Via_ID"]):
                self.assertAlmostEqual(
                    via.hole_diameter, float(row["Finished_hole_mm"]), places=6
                )
                self.assertAlmostEqual(via.diameter, float(row["Pad_mm"]), places=6)
                # The translated `type` is a bare protobuf enum number; resolve
                # the expected name through the descriptor rather than hard-
                # coding which integer means which drill.
                drill = via.DESCRIPTOR.fields_by_name["type"].enum_type
                assert drill is not None
                expected = (
                    "LASER_DRILL" if row["Drill"] == "Laser" else "MECHANICAL_DRILL"
                )
                self.assertEqual(via.type, drill.values_by_name[expected].number)
                self.assertEqual(via.filled, row["Fill"] != "")
                self.assertEqual(via.via_in_pad, row["Via_in_pad"] == "Yes")
                # Spans are declared with signed indices; the report names layers.
                self.assertEqual(
                    layer_number(via.start.index, via.start.side),
                    int(row["From_layer"].removeprefix("L")),
                )
                self.assertEqual(
                    layer_number(via.stop.index, via.stop.side),
                    int(row["To_layer"].removeprefix("L")),
                )

    def test_depth_matches_the_stackup_on_its_own_convention(self):
        """``Depth_mm`` against the depth each via's layer span implies.

        The report quotes depth two ways, per its NOTES: dielectric-only for the
        laser microvias, full drilled depth for the mechanical drills. Applying
        either convention to all twelve structures gives wrong aspect ratios for
        the other group, and nothing else in this suite would notice, because
        :meth:`test_annular_ring_and_aspect_ratio_within_capability` takes depth
        from the CSV rather than deriving it.
        """
        for row in sections()["VIAS"]:
            laser = row["Drill"] == "Laser"
            implied = stackup_span_mm(
                row["From_layer"], row["To_layer"], include_end_foils=not laser
            )
            with self.subTest(via=row["Via_ID"]):
                self.assertAlmostEqual(float(row["Depth_mm"]), implied, places=6)

    def test_annular_ring_and_aspect_ratio_within_capability(self):
        """Checks the *built* via geometry, not just the CSV's own cells.

        Depth has no counterpart in the design (JITX doesn't store it), so it
        comes from the report; hole and pad diameters are read back off the
        translated vias so a wrong number in ``board.py`` fails here too.
        """
        min_ring = fab_rules()["min_annular_ring"]
        min_laser_drill = fab_rules()["min_drill_diameter"]
        min_mech_drill = float(capability("Minimum mechanical drill diameter"))
        max_laser_ar = float(
            capability("Maximum laser microvia aspect ratio").split(":")[0]
        )
        max_mech_ar = float(
            capability("Maximum mechanical drill aspect ratio").split(":")[0]
        )
        self.assertGreater(
            min_mech_drill, min_laser_drill, "min_drill_diameter is the laser minimum"
        )

        by_name = {v.name: v for v in translated().vias}
        for row in sections()["VIAS"]:
            name = (
                f"{_VIA_PREFIX[row['Structure']]}_{row['From_layer']}_{row['To_layer']}"
            )
            via = by_name[name]
            laser = row["Drill"] == "Laser"
            ratio = float(row["Depth_mm"]) / via.hole_diameter
            with self.subTest(via=row["Via_ID"]):
                self.assertGreaterEqual(
                    (via.diameter - via.hole_diameter) / 2, min_ring
                )
                self.assertGreaterEqual(
                    via.hole_diameter, min_laser_drill if laser else min_mech_drill
                )
                self.assertLessEqual(ratio, max_laser_ar if laser else max_mech_ar)

    def test_fill_and_capping_match_csv(self):
        """`filled` is a boolean, so fill material and capping are review-only —
        but the boolean itself, and tenting, must still follow the report."""
        by_name = {v.name: v for v in translated().vias}
        tented = by_name["THVia_L1_L20"].DESCRIPTOR.fields_by_name["tented"].enum_type
        assert tented is not None
        for row in sections()["VIAS"]:
            name = (
                f"{_VIA_PREFIX[row['Structure']]}_{row['From_layer']}_{row['To_layer']}"
            )
            via = by_name[name]
            with self.subTest(via=row["Via_ID"]):
                self.assertIn(row["Fill"], ("Copper", "Resin"))
                self.assertTrue(via.filled)
                self.assertEqual(row["Capped"], "Yes")
                self.assertEqual(row["Tented"], "Both")
                self.assertEqual(via.tented, tented.values_by_name["TENT_BOTH"].number)

    def test_microvia_ladder_spans_one_build_up_level(self):
        """Five levels per side, each adjacent-layer, both halves mirrored."""
        classes = self.via_classes()
        laser = {
            name: cls for name, cls in classes.items() if cls.type is ViaType.LaserDrill
        }
        self.assertEqual(len(laser), 10)
        top = {n: c for n, c in laser.items() if c.start_layer >= 0}
        bottom = {n: c for n, c in laser.items() if c.start_layer < 0}
        self.assertEqual(len(top), 5)
        self.assertEqual(len(bottom), 5)
        for name, cls in laser.items():
            with self.subTest(via=name):
                self.assertEqual(abs(cls.stop_layer - cls.start_layer), 1)
                self.assertTrue(cls.via_in_pad)
                self.assertTrue(cls.filled)
        # The bottom half is the exact mirror of the top half.
        self.assertEqual(
            sorted(signed_to_layer(c.start_layer) for c in top.values()),
            [1, 2, 3, 4, 5],
        )
        self.assertEqual(
            sorted(signed_to_layer(c.start_layer) for c in bottom.values()),
            [16, 17, 18, 19, 20],
        )

    def test_no_si_models_declared(self):
        """A fab report has no electrical models; none may be invented here."""
        for name, cls in self.via_classes().items():
            with self.subTest(via=name):
                self.assertEqual(dict(cls.models), {})


class TestFabRules(TestCase):
    def test_all_required_constraints_present_and_match_csv(self):
        expected = fab_rules()
        # Every constraint JITX declares must be covered by the report.
        required = {
            name
            for name, annotation in FabricationConstraints.__annotations__.items()
            if not name.startswith("_")
        }
        self.assertEqual(set(expected), required)
        self.assertEqual(len(expected), 19)

        for attribute, value in expected.items():
            with self.subTest(constraint=attribute):
                self.assertAlmostEqual(getattr(HDIFabRules, attribute), value, places=6)

    def test_translated_rules_carry_every_constraint(self):
        self.assertEqual(len(translated().ruless[0].clearances), 19)

    def test_engine_enforced_rules_do_not_clamp_the_geometry(self):
        """min_copper_* override trace width and clearance, so nothing may sit
        below them — including the neck-down regions."""
        min_width = fab_rules()["min_copper_width"]
        min_space = fab_rules()["min_copper_copper_space"]
        for row in sections()["IMPEDANCE"]:
            widths = [row["Line_width_mm"], row["Neck_width_mm"]]
            spaces = [
                row["Pair_gap_mm"],
                row["Neck_gap_mm"],
                row["Clearance_mm"],
                row["Neck_clearance_mm"],
            ]
            with self.subTest(structure=row["Structure_ID"], geom=row["Geometry"]):
                for value in widths:
                    if value.strip():
                        self.assertGreaterEqual(float(value), min_width)
                for value in spaces:
                    if value.strip():
                        self.assertGreaterEqual(float(value), min_space)


class TestRoutingStructures(TestCase):
    #: CSV Structure_ID -> the substrate attribute holding it.
    STRUCTURES = {
        "SE-DEFAULT": "SE_Default",
        "SE-40": "SE_40",
        "SE-50": "SE_50",
        "DIFF-100": "DRS_100",
    }

    def rows_for(self, structure_id: str) -> list[dict[str, str]]:
        return [r for r in sections()["IMPEDANCE"] if r["Structure_ID"] == structure_id]

    def test_lookup_by_impedance(self):
        substrate = HDISubstrate()
        for structure_id, attribute in self.STRUCTURES.items():
            rows = self.rows_for(structure_id)
            target = float(rows[0]["Target_Z_ohm"])
            with self.subTest(structure=structure_id):
                if rows[0]["Type"] == "Differential":
                    found = substrate.differential_routing_structure(target * ohm)
                else:
                    found = substrate.routing_structure(target * ohm)
                self.assertEqual(found.name, getattr(substrate, attribute).name)
                self.assertAlmostEqual(ohm.m_from(found.impedance), target, places=6)

    def test_layer_coverage(self):
        """Every controlled structure covers L1/L3/L5 and the bottom mirror."""
        substrate = HDISubstrate()
        for structure_id, attribute in self.STRUCTURES.items():
            structure = getattr(substrate, attribute)
            covered = {signed_to_layer(i) for i in structure.layers}
            expected: set[int] = set()
            for row in self.rows_for(structure_id):
                expected |= {
                    int(name.removeprefix("L")) for name in row["Layers"].split(";")
                }
            with self.subTest(structure=structure_id):
                self.assertEqual(covered, expected)
                self.assertEqual(covered, {1, 3, 5, 16, 18, 20})

    def test_geometry_matches_csv(self):
        substrate = HDISubstrate()
        for structure_id, attribute in self.STRUCTURES.items():
            structure = getattr(substrate, attribute)
            for row in self.rows_for(structure_id):
                for name in row["Layers"].split(";"):
                    number = int(name.removeprefix("L"))
                    index = next(
                        i for i in structure.layers if signed_to_layer(i) == number
                    )
                    layer = structure.layers[index]
                    with self.subTest(structure=structure_id, layer=name):
                        self.assertAlmostEqual(
                            layer.trace_width, float(row["Line_width_mm"]), places=6
                        )
                        self.assertAlmostEqual(
                            layer.clearance or 0.0,
                            float(row["Clearance_mm"]),
                            places=6,
                        )
                        self.assertAlmostEqual(
                            layer.insertion_loss,
                            float(row["Loss_dB_per_mm"]),
                            places=6,
                        )
                        # eps_eff comes from the report, not from Dk: the coated
                        # microstrip value folds in the soldermask and varies
                        # with line width.
                        self.assertAlmostEqual(
                            layer.velocity,
                            phase_velocity(float(row["Eps_eff"])),
                            delta=1.0,
                        )
                        if row["Pair_gap_mm"].strip():
                            self.assertAlmostEqual(
                                layer.pair_spacing,
                                float(row["Pair_gap_mm"]),
                                places=6,
                            )
                        self.assert_neck_matches(layer, row)

    def assert_neck_matches(self, layer, row: dict[str, str]) -> None:
        """A blank Neck_* column means no neck-down — not a borrowed one."""
        if not row["Neck_width_mm"].strip():
            self.assertIsNone(
                layer.neck_down,
                f"{row['Structure_ID']} {row['Geometry']}: the report leaves the "
                "Neck_* columns blank, so no neck-down may be declared",
            )
            return
        assert layer.neck_down is not None
        self.assertAlmostEqual(
            layer.neck_down.trace_width or 0.0, float(row["Neck_width_mm"]), places=6
        )
        self.assertAlmostEqual(
            layer.neck_down.clearance or 0.0,
            float(row["Neck_clearance_mm"]),
            places=6,
        )
        if row["Neck_gap_mm"].strip():
            self.assertAlmostEqual(
                getattr(layer.neck_down, "pair_spacing", None) or 0.0,
                float(row["Neck_gap_mm"]),
                places=6,
            )

    def test_microstrip_and_stripline_geometry_actually_differ(self):
        """The reason a per-layer table exists at all."""
        substrate = HDISubstrate()
        for attribute in self.STRUCTURES.values():
            structure = getattr(substrate, attribute)
            surface = structure.layers[0]  # L1, coated microstrip
            inner = structure.layers[2]  # L3, symmetric stripline
            with self.subTest(structure=attribute):
                self.assertNotAlmostEqual(surface.trace_width, inner.trace_width)
                self.assertNotAlmostEqual(surface.velocity, inner.velocity, places=0)

    def test_reference_planes_match_csv_ref_layers(self):
        """``REFERENCE_PLANES`` against the IMPEDANCE ``Ref_layers`` column.

        The test below checks the planes are structurally sensible — adjacent,
        and actually planes. This one checks they are the planes the report
        *named*, which is the column ``REFERENCE_PLANES`` is a transcription of.
        """
        self.assertEqual(
            {
                signed_to_layer(index): tuple(
                    signed_to_layer(plane) for plane in planes
                )
                for index, planes in REFERENCE_PLANES.items()
            },
            csv_reference_planes(),
        )

    def test_reference_planes_are_the_adjacent_planes(self):
        """Microstrip references one plane; stripline references two."""
        plane_layers = {
            int(r["Layer"].removeprefix("L"))
            for r in sections()["STACKUP"]
            if r["Type"] == "Copper" and r["Function"].startswith("Plane")
        }
        for index, planes in REFERENCE_PLANES.items():
            layer = signed_to_layer(index)
            with self.subTest(layer=f"L{layer}"):
                expected = 1 if layer in (1, 20) else 2
                self.assertEqual(len(planes), expected)
                for plane in planes:
                    self.assertIn(signed_to_layer(plane), plane_layers)
                    self.assertEqual(abs(signed_to_layer(plane) - layer), 1)

    def test_reference_plane_widths_are_the_skill_default(self):
        """Every carried plane width is the skill's 3x-dielectric-height default.

        The report's ``Ref_layers`` column names planes and never widths, and a
        ``None`` width is translation-fatal (board.py, ambiguity 3), so board.py
        carries the substrate-modeler skill's labeled default instead. Asserted
        against the default's own formula over the CSV separation — one D-BU
        build-up lamination for every named plane — never against an impedance
        row: the report does not state these widths, so testing them against
        the source would be circular.
        """
        d_bu = next(
            r for r in sections()["MATERIALS_DIELECTRIC"] if r["Material_ID"] == "D-BU"
        )
        self.assertAlmostEqual(
            REF_PLANE_WIDTH, 3 * float(d_bu["Thickness_mm"]), places=6
        )
        substrate = HDISubstrate()
        structures = [(a, getattr(substrate, a)) for a in self.STRUCTURES.values()]
        uncoupled = substrate.DRS_100.uncoupled_region
        assert uncoupled is not None
        structures.append(("DRS_100.uncoupled_region", uncoupled))
        for attribute, structure in structures:
            for index, layer in structure.layers.items():
                with self.subTest(structure=attribute, layer=index):
                    self.assertEqual(
                        {r.layer: r.desired_width for r in decompose(layer, _RefLayer)},
                        dict.fromkeys(REFERENCE_PLANES[index], REF_PLANE_WIDTH),
                    )

    def test_uncoupled_region_matches_csv(self):
        rows = self.rows_for("DIFF-100-UNC")
        uncoupled = HDISubstrate().DRS_100.uncoupled_region
        assert uncoupled is not None
        self.assertAlmostEqual(
            ohm.m_from(uncoupled.impedance), float(rows[0]["Target_Z_ohm"]), places=6
        )
        for row in rows:
            for name in row["Layers"].split(";"):
                number = int(name.removeprefix("L"))
                index = next(
                    i for i in uncoupled.layers if signed_to_layer(i) == number
                )
                layer = uncoupled.layers[index]
                with self.subTest(layer=name):
                    self.assertAlmostEqual(
                        layer.trace_width, float(row["Line_width_mm"]), places=6
                    )
                    self.assertAlmostEqual(
                        layer.clearance or 0.0, float(row["Clearance_mm"]), places=6
                    )
                    self.assertAlmostEqual(
                        layer.insertion_loss, float(row["Loss_dB_per_mm"]), places=6
                    )
                    self.assertAlmostEqual(
                        layer.velocity,
                        phase_velocity(float(row["Eps_eff"])),
                        delta=1.0,
                    )
                    # The report leaves DIFF-100-UNC's Neck_* columns blank.
                    self.assert_neck_matches(layer, row)

    def test_standard_default_is_deliberately_not_modelled(self):
        """It has no single impedance, so it gets no RoutingStructure.

        The report's 0.150 mm default line/space models 41.87 ohm on stripline
        but 60.99 ohm on microstrip. A RoutingStructure carries one impedance,
        so neither value may be declared as if it held across the stack.
        """
        row = next(
            r for r in sections()["IMPEDANCE"] if r["Structure_ID"] == "STANDARD"
        )
        self.assertEqual(row["Controlled"], "No")
        self.assertEqual(row["Target_Z_ohm"], "")

        substrate = HDISubstrate()
        # Enumerate from the substrate, not from STRUCTURES — otherwise a fifth
        # structure modelling this geometry would simply be invisible here.
        found = list(decompose(substrate, RoutingStructure))
        controlled = [
            r
            for r in sections()["IMPEDANCE"]
            if r["Controlled"] == "Yes" and r["Type"] == "Single-ended"
        ]
        self.assertEqual(
            len(found),
            len({r["Structure_ID"] for r in controlled}) - 1,
            "one RoutingStructure per controlled single-ended ID, less the "
            "nested uncoupled region (decompose does not descend into it)",
        )
        self.assertEqual(len(found), 3)
        # Neither impedance that the standard geometry produces is claimed.
        for value in (41.87, 60.99):
            with self.subTest(impedance=value):
                with self.assertRaises(ValueError):
                    substrate.routing_structure(value * ohm)


class TestTranslation(TestCase):
    def test_design_translates(self):
        self.assertTrue(package_design(HDIStackupDesign()))

    @staticmethod
    def half_extent(boundary) -> tuple[float, float]:
        """Half-width and half-height of a rounded-rectangle arc polygon.

        The outline translates to four corner arcs; the furthest point in each
        axis is a corner centre plus its radius.
        """
        arcs = [e.arc for e in boundary.arc_polygon.elements if e.HasField("arc")]
        return (
            max(a.center.x + a.radius for a in arcs),
            max(a.center.y + a.radius for a in arcs),
        )

    def test_board_outline_matches_document(self):
        width, height = (float(part) for part in document()["Board size"].split(" x "))
        self.assertLessEqual(width, fab_rules()["max_board_width"])
        self.assertLessEqual(height, fab_rules()["max_board_height"])

        board = translated().boards[0]
        self.assertTrue(board.HasField("boundary"))
        self.assertTrue(board.HasField("signal_boundary"))

        # The outline is the report's board size.
        out_x, out_y = self.half_extent(board.boundary)
        self.assertAlmostEqual(2 * out_x, width, places=4)
        self.assertAlmostEqual(2 * out_y, height, places=4)

        # signal_area is inset by exactly min_copper_edge_space — the only
        # placement number in the file, and it is derived from a fab rule
        # rather than chosen.
        inset = fab_rules()["min_copper_edge_space"]
        sig_x, sig_y = self.half_extent(board.signal_boundary)
        self.assertAlmostEqual(out_x - sig_x, inset, places=4)
        self.assertAlmostEqual(out_y - sig_y, inset, places=4)

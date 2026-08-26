from jitx.circuit import Circuit
from jitx.container import inline
from jitx.net import Port
from jitx.sample import SampleDesign
from jitx.test import TestCase

from jitxlib.landpatterns.twopin.SMT_table import SMT_CHIP_DEFS

from jitxexamples.jumpstart_kits.js1_stackup_components.parametric_passives.components.samsung_cl import (
    CL_DIMENSIONS,
    SamsungCL,
    format_capacitance_code,
)


class SamsungCLDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        # One parameterized class covers the whole family — no parts-DB query.
        # Live catalog part: 0603, X7R, 100 nF, +/-10%, 50 V.
        c_100n_0603 = SamsungCL(capacitance=100e-9, size="0603")
        c_1u_0805 = SamsungCL(
            capacitance=1e-6,
            size="0805",
            dielectric="X7R",
            tolerance=0.20,
            voltage=16,
        )
        c_22p_0402 = SamsungCL(
            capacitance=22e-12,
            size="0402",
            dielectric="C0G",
            tolerance=0.05,
        )
        c_1p5_0402 = SamsungCL(
            capacitance=1.5e-12,
            size="0402",
            dielectric="C0G",
            tolerance=0.05,
        )

        def __init__(self):
            # Exercise the shared drop-in .insert() placement helper.
            self.extra = SamsungCL(capacitance=10e-9, size="0402").insert(
                self.c_100n_0603.p1, self.c_1u_0805.p1
            )


class TestSamsungCL(TestCase):
    def test_builds_in_design(self):
        design = SamsungCLDesign()
        c = design.circuit.c_100n_0603  # type: ignore
        self.assertIsInstance(c, SamsungCL)
        self.assertEqual(c.manufacturer, "Samsung Electro-Mechanics")
        self.assertEqual(c.reference_designator_prefix, "C")
        self.assertEqual(c.case, "0603")
        self.assertEqual(c.dielectric, "X7R")
        self.assertEqual(c.tolerance, 0.10)
        self.assertEqual(c.voltage, 50)
        self.assertIsInstance(c.p1, Port)
        self.assertIsInstance(c.p2, Port)
        self.assertEqual(len(c.landpattern.p), 2)  # type: ignore
        self.assertIsInstance(design.circuit.extra, SamsungCL)  # type: ignore

    def test_mpn_generation(self):
        design = SamsungCLDesign()
        # Live catalog part number proves the 11-position scheme.
        self.assertEqual(design.circuit.c_100n_0603.mpn, "CL10B104KB8NNNC")  # type: ignore
        # X7R 1 uF +/-20% 16 V in 0805 (thickness default C = 0.85 mm).
        self.assertEqual(design.circuit.c_1u_0805.mpn, "CL21B105MOCNNNC")  # type: ignore
        # C0G in 0402 (dielectric code C, thickness default 5 = 0.50 mm).
        self.assertEqual(design.circuit.c_22p_0402.mpn, "CL05C220JB5NNNC")  # type: ignore
        # Sub-10 pF values use the R decimal form.
        self.assertEqual(design.circuit.c_1p5_0402.mpn, "CL05C1R5JB5NNNC")  # type: ignore

    def test_capacitance_code(self):
        cases = [
            (1.5e-12, "1R5"),
            (4.7e-12, "4R7"),
            (10e-12, "100"),
            (22e-12, "220"),
            (100e-12, "101"),
            (1e-9, "102"),
            (10e-9, "103"),
            (100e-9, "104"),
            (1e-6, "105"),
            (10e-6, "106"),
            (9.96e-9, "103"),  # decade carry: rounds up to 10 nF
            (99.5e-9, "104"),  # decade carry: rounds up to 100 nF
        ]
        for farads, expected in cases:
            with self.subTest(farads=farads):
                self.assertEqual(format_capacitance_code(farads), expected)

    def test_validation(self):
        with self.assertRaises(ValueError):
            SamsungCL(capacitance=100e-9, size="9999")  # unknown size
        with self.assertRaises(ValueError):
            SamsungCL(capacitance=100e-9, dielectric="Y5V")  # unsupported dielectric
        with self.assertRaises(ValueError):
            # C0G is the precision line; +/-20% is an X7R tolerance.
            SamsungCL(capacitance=1e-9, dielectric="C0G", tolerance=0.20)
        with self.assertRaises(ValueError):
            # +/-1% is a C0G tolerance, not offered on X7R.
            SamsungCL(capacitance=100e-9, dielectric="X7R", tolerance=0.01)
        with self.assertRaises(ValueError):
            SamsungCL(capacitance=100e-9, voltage=100)  # out-of-scope voltage
        with self.assertRaises(ValueError):
            # 10 uF is far outside the 0402 X7R envelope.
            SamsungCL(capacitance=10e-6, size="0402")
        with self.assertRaises(ValueError):
            SamsungCL(capacitance=-1e-9)  # non-positive capacitance
        with self.assertRaises(ValueError):
            SamsungCL(capacitance=100e-9, packaging="Z")  # bad packaging

    def test_value_label(self):
        """The BOM value label: no build or type check ever looks at this."""
        design = SamsungCLDesign()
        self.assertEqual(str(design.circuit.c_100n_0603.value), "100.0 nanofarad")  # type: ignore
        self.assertEqual(str(design.circuit.c_22p_0402.value), "22.0 picofarad")  # type: ignore

    def test_standard_table_agrees_with_catalog(self):
        """JITX's standard chip table vs. the catalog, per size.

        This family takes ``dims=None``, so without this nothing would notice a
        wrong entry in the standard table -- which is not hypothetical: the same
        table's 2512 termination band is wrong by 1.4 mm (see
        ``test_js1_vishay_crcw``). None of the three MLCC sizes is affected, and
        this test is what says so.
        """
        for size, dims in CL_DIMENSIONS.items():
            std = SMT_CHIP_DEFS[size]
            with self.subTest(size=size):
                self.assertAlmostEqual(std.length.typ, dims.length.typ, delta=0.10)
                self.assertAlmostEqual(std.width.typ, dims.width.typ, delta=0.10)
                self.assertAlmostEqual(
                    std.lead_length.typ,
                    dims.lead.typ,
                    delta=0.10,
                    msg=f"SMT_CHIP_DEFS[{size!r}].lead_length disagrees with the "
                    f"catalog band width BW",
                )

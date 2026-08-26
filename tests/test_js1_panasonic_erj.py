from jitx.circuit import Circuit
from jitx.container import inline
from jitx.net import Port
from jitx.sample import SampleDesign
from jitx.test import TestCase

from jitxexamples.jumpstart_kits.js1_stackup_components.parametric_passives.components.panasonic_erj import (
    PanasonicERJ,
    format_value_code,
)


class PanasonicERJDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        # One parameterized class covers the whole family — no parts-DB query.
        r_1k_0603 = PanasonicERJ(resistance=1000, size="0603")
        r_1k_0402 = PanasonicERJ(resistance=1000, size="0402")
        r_10k_0805 = PanasonicERJ(resistance=10e3, size="0805")
        r_1m_2512 = PanasonicERJ(resistance=1e6, size="2512")
        # Opt-in E24 grid check accepts a standard value (4.7k) at build time.
        r_eseries = PanasonicERJ(resistance=4700, size="0603", check_eseries=True)

        def __init__(self):
            # Exercise the shared drop-in .insert() placement helper.
            self.extra = PanasonicERJ(resistance=100, size="0402").insert(
                self.r_1k_0603.p1, self.r_1k_0402.p1
            )


class TestPanasonicERJ(TestCase):
    def test_builds_in_design(self):
        design = PanasonicERJDesign()
        r = design.circuit.r_1k_0603  # type: ignore
        self.assertIsInstance(r, PanasonicERJ)
        self.assertEqual(r.manufacturer, "Panasonic")
        self.assertEqual(r.reference_designator_prefix, "R")
        self.assertEqual(r.case, "0603")
        self.assertEqual(r.tolerance, 0.05)
        self.assertEqual(r.power, 0.1)
        self.assertEqual(r.max_voltage, 75)
        self.assertIsInstance(r.p1, Port)
        self.assertIsInstance(r.p2, Port)
        self.assertEqual(len(r.landpattern.p), 2)  # type: ignore
        self.assertIsInstance(design.circuit.extra, PanasonicERJ)  # type: ignore

    def test_mpn_generation(self):
        design = PanasonicERJDesign()
        # Datasheet's own part-number example proves the scheme (0603, 1k, V reel).
        self.assertEqual(design.circuit.r_1k_0603.mpn, "ERJ3GEYJ102V")  # type: ignore
        # 0402 (code 2GE) carries no value-marking "Y".
        self.assertEqual(design.circuit.r_1k_0402.mpn, "ERJ2GEJ102X")  # type: ignore
        self.assertEqual(design.circuit.r_10k_0805.mpn, "ERJ6GEYJ103V")  # type: ignore
        self.assertEqual(design.circuit.r_1m_2512.mpn, "ERJ1TYJ105U")  # type: ignore

    def test_value_code(self):
        cases = [
            (1, "1R0"),
            (2.2, "2R2"),
            (4.7, "4R7"),
            (10, "100"),
            (47, "470"),
            (100, "101"),
            (1000, "102"),
            (2200, "222"),
            (4700, "472"),
            (10_000, "103"),
            (1_000_000, "105"),
            (10_000_000, "106"),
            (9.96, "100"),  # sub-10 carry: rounds up to 10 ohm
        ]
        for ohms, expected in cases:
            with self.subTest(ohms=ohms):
                self.assertEqual(format_value_code(ohms), expected)

    def test_validation(self):
        with self.assertRaises(ValueError):
            PanasonicERJ(resistance=1000, size="9999")  # unknown size
        with self.assertRaises(ValueError):
            PanasonicERJ(resistance=1000, size="0603", tolerance=0.01)  # 5% only
        with self.assertRaises(ValueError):
            PanasonicERJ(resistance=0.5, size="0402")  # below 1 ohm
        with self.assertRaises(ValueError):
            PanasonicERJ(resistance=2e6, size="2512")  # above the size's max (1M)
        with self.assertRaises(ValueError):
            PanasonicERJ(resistance=1000, size="0402", packaging="Z")  # bad packaging

    def test_value_label(self):
        """The BOM value label: no build or type check ever looks at this."""
        design = PanasonicERJDesign()
        self.assertEqual(str(design.circuit.r_1k_0603.value), "1.0 kiloohm")  # type: ignore
        self.assertEqual(str(design.circuit.r_1m_2512.value), "1.0 megaohm")  # type: ignore

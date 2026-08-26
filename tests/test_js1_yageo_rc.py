from jitx.circuit import Circuit
from jitx.container import inline
from jitx.net import Port
from jitx.sample import SampleDesign
from jitx.test import TestCase

from jitxexamples.jumpstart_kits.js1_stackup_components.parametric_passives.components.chip_smt import (
    check_eseries,
)
from jitxexamples.jumpstart_kits.js1_stackup_components.parametric_passives.components.yageo_rc import (
    YageoRC,
    format_resistance_code,
)


class YageoRCDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        # One parameterized class covers the whole family — no parts-DB query.
        r_10k_0603 = YageoRC(resistance=10e3, size="0603", tolerance=0.01)
        r_4k7_0402 = YageoRC(resistance=4700, size="0402", tolerance=0.05)
        r_1m_2512 = YageoRC(resistance=1e6, size="2512", tolerance=0.01)
        # Datasheet ordering example: RC0402, 100K, +/-5%, 7" reel.
        r_100k_0402 = YageoRC(resistance=100e3, size="0402", tolerance=0.05)
        # 2.2M scales to a repeating binary fraction; guards the value label.
        r_2m2_0805 = YageoRC(resistance=2.2e6, size="0805", tolerance=0.05)
        # Opt-in E96 grid check accepts a standard value (4.99k) at build time.
        r_eseries = YageoRC(
            resistance=4990, size="0603", tolerance=0.01, check_eseries=True
        )
        # Ultra-tiny ESD-reel sizes (land pattern keyed to 009005 / 01005).
        r_0075 = YageoRC(resistance=10e3, size="0075", tolerance=0.05)
        r_0100 = YageoRC(resistance=1e3, size="0100", tolerance=0.01)

        def __init__(self):
            # Exercise the drop-in .insert() placement helper.
            self.extra = YageoRC(resistance=1e3, size="0402").insert(
                self.r_10k_0603.p1, self.r_4k7_0402.p1
            )


class TestYageoRC(TestCase):
    def test_builds_in_design(self):
        design = YageoRCDesign()
        r = design.circuit.r_10k_0603  # type: ignore
        self.assertIsInstance(r, YageoRC)
        self.assertEqual(r.manufacturer, "Yageo")
        self.assertEqual(r.reference_designator_prefix, "R")
        self.assertEqual(r.case, "0603")
        self.assertEqual(r.tolerance, 0.01)
        self.assertEqual(r.power, 1 / 10)
        self.assertEqual(r.max_voltage, 75)
        self.assertIsInstance(r.p1, Port)
        self.assertIsInstance(r.p2, Port)
        self.assertEqual(len(r.landpattern.p), 2)  # type: ignore
        # Smallest size builds a valid 2-pad land pattern (via the 009005 key).
        self.assertEqual(len(design.circuit.r_0075.landpattern.p), 2)  # type: ignore
        self.assertIsInstance(design.circuit.extra, YageoRC)  # type: ignore

    def test_mpn_generation(self):
        design = YageoRCDesign()
        # Datasheet's own worked example proves the part-number scheme.
        self.assertEqual(design.circuit.r_100k_0402.mpn, "RC0402JR-07100KL")  # type: ignore
        self.assertEqual(design.circuit.r_10k_0603.mpn, "RC0603FR-0710KL")  # type: ignore
        self.assertEqual(design.circuit.r_4k7_0402.mpn, "RC0402JR-074K7L")  # type: ignore
        self.assertEqual(design.circuit.r_1m_2512.mpn, "RC2512FR-071ML")  # type: ignore
        # Ultra-tiny ESD-reel sizes carry packaging S + reel 7N.
        self.assertEqual(design.circuit.r_0075.mpn, "RC0075JS-7N10KL")  # type: ignore
        self.assertEqual(design.circuit.r_0100.mpn, "RC0100FR-071KL")  # type: ignore

    def test_resistance_code(self):
        cases = [
            (4.7, "4R7"),
            (100, "100R"),
            (97.6, "97R6"),
            (4700, "4K7"),
            (9760, "9K76"),
            (10_000, "10K"),
            (100_000, "100K"),
            (1_000_000, "1M"),
            (10_000_000, "10M"),
            (0.47, "R47"),
            (1000, "1K"),
            (9999, "10K"),  # decade carry: rounds up to 10 k
            (999_500, "1M"),  # decade carry: rounds up to 1 M
        ]
        for ohms, expected in cases:
            with self.subTest(ohms=ohms):
                self.assertEqual(format_resistance_code(ohms), expected)

    def test_validation(self):
        with self.assertRaises(ValueError):
            YageoRC(resistance=10e3, size="9999")  # unknown size
        with self.assertRaises(ValueError):
            YageoRC(resistance=10e3, size="0402", tolerance=0.02)  # bad tolerance
        with self.assertRaises(ValueError):
            YageoRC(resistance=-5, size="0402")  # non-positive resistance
        with self.assertRaises(ValueError):
            # 0201 has no double-power variant for the "7W" reel/power code
            YageoRC(resistance=10e3, size="0201", reel_power_code="7W")
        with self.assertRaises(ValueError):
            YageoRC(resistance=10e3, size="0402", reel_power_code="ZZ")  # bad code
        with self.assertRaises(ValueError):
            YageoRC(resistance=10e3, size="0402", packaging="S")  # S is 0075/0100 only
        with self.assertRaises(ValueError):
            YageoRC(resistance=10e3, size="0075", packaging="R")  # 0075 is ESD-only
        with self.assertRaises(ValueError):
            # ESD reel (7N) pairs only with packaging S
            YageoRC(resistance=10e3, size="0100", packaging="R", reel_power_code="7N")

    def test_eseries_grades(self):
        # Two grades, chosen by tolerance: E24 at +/-5%, E96 for anything
        # tighter. That is the whole ladder these four datasheets need.
        check_eseries(4700, 0.05)  # E24 (5%)
        check_eseries(4990, 0.01)  # E96 (1%)
        check_eseries(4990, 0.001)  # still E96 at 0.1%
        # 4990 is E96 but not E24, so the loose grade rejects it.
        with self.assertRaises(ValueError):
            check_eseries(4990, 0.05)
        # 1010 ohm is on the E192 grid but not E96. Yageo's tightest grade is
        # +/-0.1% (code B) and its datasheet puts that on E24/E96, so no part in
        # this family can be ordered at 1010 ohm -- reaching to E192 for the
        # tight grades would accept a value the vendor does not make.
        with self.assertRaises(ValueError):
            check_eseries(1010, 0.01)
        with self.assertRaises(ValueError):
            check_eseries(1010, 0.001)
        with self.assertRaises(ValueError):
            # 5000 ohms is not on the E96 grid (nearest standard value is 4.99k).
            YageoRC(resistance=5000, size="0402", tolerance=0.01, check_eseries=True)

    def test_value_label(self):
        """The BOM value label: no build or type check ever looks at this."""
        design = YageoRCDesign()
        self.assertEqual(str(design.circuit.r_2m2_0805.value), "2.2 megaohm")  # type: ignore
        self.assertEqual(str(design.circuit.r_10k_0603.value), "10.0 kiloohm")  # type: ignore

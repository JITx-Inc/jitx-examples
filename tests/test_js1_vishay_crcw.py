from jitx.circuit import Circuit
from jitx.container import inline
from jitx.net import Port
from jitx.sample import SampleDesign
from jitx.test import TestCase

from jitxlib.landpatterns.twopin.SMT_table import SMT_CHIP_DEFS

from jitxexamples.jumpstart_kits.js1_stackup_components.parametric_passives.components.vishay_crcw import (
    CRCW_DIMENSIONS,
    VishayCRCW,
    _STANDARD_TABLE_OVERRIDES,
    format_value_code,
)


class VishayCRCWDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        # One parameterized class covers the whole family — no parts-DB query.
        r_562_0603 = VishayCRCW(resistance=562, size="0603", tolerance=0.01)
        r_10k_0402 = VishayCRCW(resistance=10e3, size="0402", tolerance=0.01)
        r_4k7_0805 = VishayCRCW(resistance=4700, size="0805", tolerance=0.05)
        r_1m_1206 = VishayCRCW(resistance=1e6, size="1206", tolerance=0.01)
        # Cover every remaining size so each land pattern is built once.
        r_1210 = VishayCRCW(resistance=100, size="1210")
        r_1218 = VishayCRCW(resistance=100, size="1218")
        r_2010 = VishayCRCW(resistance=100, size="2010")
        r_2512 = VishayCRCW(resistance=100, size="2512")
        # Opt-in E96 grid check accepts a standard value (4.99k) at build time.
        r_eseries = VishayCRCW(resistance=4990, size="0603", check_eseries=True)

        def __init__(self):
            # Exercise the shared drop-in .insert() placement helper.
            self.extra = VishayCRCW(resistance=100, size="0402").insert(
                self.r_562_0603.p1, self.r_10k_0402.p1
            )


class TestVishayCRCW(TestCase):
    def test_builds_in_design(self):
        design = VishayCRCWDesign()
        r = design.circuit.r_562_0603  # type: ignore
        self.assertIsInstance(r, VishayCRCW)
        self.assertEqual(r.manufacturer, "Vishay")
        self.assertEqual(r.reference_designator_prefix, "R")
        self.assertEqual(r.case, "0603")
        self.assertEqual(r.tolerance, 0.01)
        self.assertEqual(r.tcr_ppm, 100)
        self.assertEqual(r.power, 0.125)
        self.assertEqual(r.max_voltage, 75)
        self.assertIsInstance(r.p1, Port)
        self.assertIsInstance(r.p2, Port)
        self.assertEqual(len(r.landpattern.p), 2)  # type: ignore
        # Largest size builds a valid 2-pad land pattern too.
        self.assertEqual(len(design.circuit.r_2512.landpattern.p), 2)  # type: ignore
        self.assertIsInstance(design.circuit.extra, VishayCRCW)  # type: ignore

    def test_mpn_generation(self):
        design = VishayCRCWDesign()
        # Datasheet's own part-number example proves the scheme.
        self.assertEqual(design.circuit.r_562_0603.mpn, "CRCW0603562RFKEA")  # type: ignore
        self.assertEqual(design.circuit.r_10k_0402.mpn, "CRCW040210K0FKED")  # type: ignore
        # +/-5% parts use TCR code N (+/-200 ppm/K).
        self.assertEqual(design.circuit.r_4k7_0805.mpn, "CRCW08054K70JNEA")  # type: ignore
        self.assertEqual(design.circuit.r_1m_1206.mpn, "CRCW12061M00FKEA")  # type: ignore

    def test_value_code(self):
        cases = [
            (1, "1R00"),
            (4.7, "4R70"),
            (10, "10R0"),
            (100, "100R"),
            (562, "562R"),
            (1000, "1K00"),
            (4700, "4K70"),
            (10_000, "10K0"),
            (49_900, "49K9"),
            (100_000, "100K"),
            (1_000_000, "1M00"),
            (10_000_000, "10M0"),
            (9999, "10K0"),  # decade carry: rounds up to 10 k
            (999.5, "1K00"),  # decade carry: rounds up to 1 k
        ]
        for ohms, expected in cases:
            with self.subTest(ohms=ohms):
                self.assertEqual(format_value_code(ohms), expected)

    def test_validation(self):
        with self.assertRaises(ValueError):
            VishayCRCW(resistance=1000, size="9999")  # unknown size
        with self.assertRaises(ValueError):
            VishayCRCW(resistance=1000, size="0603", tolerance=0.02)  # bad tolerance
        with self.assertRaises(ValueError):
            VishayCRCW(resistance=0.5, size="0402")  # below 1 ohm
        with self.assertRaises(ValueError):
            VishayCRCW(resistance=3e6, size="1218")  # above the size's max (2.2M)
        with self.assertRaises(ValueError):
            VishayCRCW(resistance=1000, size="0402", packaging="ZZ")  # bad packaging
        with self.assertRaises(ValueError):
            # +/-5% is +/-200 ppm/K only; 100 ppm/K is not offered.
            VishayCRCW(resistance=1000, size="0402", tolerance=0.05, tcr_ppm=100)

    def test_effective_dimensions_agree_with_datasheet(self):
        """What the land pattern is actually built from vs. the datasheet, per size.

        This family takes ``dims=None`` for most sizes, so nothing else here would
        notice a wrong entry in the standard table. Transcribing the datasheet's
        DIMENSIONS AND MASS table (doc page 11) and asserting the two against each
        other is what turns "we took the defaults" into "we took the defaults and
        checked them" -- it is how the 2512 termination band was caught.

        The subject is the *effective* dimensions: the datasheet override where the
        family passes one, otherwise the standard table. That is what reaches the
        generator, and unlike the table alone it does not depend on which jitx
        version resolved -- the 2512 entry is wrong on 4.2.2 and corrected on later
        builds, and this passes on both.
        """
        for size, dims in CRCW_DIMENSIONS.items():
            # Pull the three effective numbers out per branch rather than unioning
            # the two record types: ChipDims spells the termination `lead` and
            # SMTChipDef spells it `lead_length`, so a `ChipDims | SMTChipDef`
            # local cannot be narrowed by a membership test and every attribute
            # access on it is a type error.
            if size in _STANDARD_TABLE_OVERRIDES:
                eff_length, eff_width, lead = (
                    dims.length.typ,
                    dims.width.typ,
                    dims.lead.typ,
                )
            else:
                std = SMT_CHIP_DEFS[size]
                eff_length, eff_width, lead = (
                    std.length.typ,
                    std.width.typ,
                    std.lead_length.typ,
                )
            with self.subTest(size=size):
                # Body L and W: the case is standard, so these must line up.
                self.assertAlmostEqual(eff_length, dims.length.typ, delta=0.10)
                self.assertAlmostEqual(eff_width, dims.width.typ, delta=0.10)
                self.assertLessEqual(
                    abs(lead - dims.lead.typ),
                    0.20,
                    f"the termination length used for {size!r} ({lead}) disagrees "
                    f"with datasheet T1 ({dims.lead.typ}); either the transcription "
                    f"drifted or this size needs an override",
                )

    def test_overridden_size_uses_datasheet_dimensions(self):
        """The overridden size builds from the datasheet, not the bad default.

        Taking ``SMT_CHIP_DEFS["2512"]``'s 2.0 mm termination band gives a pad
        2.209 mm along the part axis; the datasheet's 0.6 mm T1 gives 0.833 mm.
        Nothing else in this suite looks at realized geometry, so without this
        the 2.65x oversize builds and ships silently.
        """
        design = VishayCRCWDesign()
        pads = design.circuit.r_2512.landpattern.p  # type: ignore
        self.assertEqual(len(pads), 2)
        for index in pads:
            points = pads[index].shape.elements
            # The pad's short axis runs along the part's length (the termination
            # direction); its long axis spans the 3.15 mm body width.
            along_part = min(
                max(c[axis] for c in points) - min(c[axis] for c in points)
                for axis in (0, 1)
            )
            self.assertLess(along_part, 1.5)

    def test_value_label(self):
        """The BOM value label: no build or type check ever looks at this."""
        design = VishayCRCWDesign()
        self.assertEqual(str(design.circuit.r_562_0603.value), "562 ohm")  # type: ignore
        self.assertEqual(str(design.circuit.r_1m_1206.value), "1.0 megaohm")  # type: ignore

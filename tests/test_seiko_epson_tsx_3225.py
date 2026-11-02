"""Checks of the TSX-3225 crystal family.

The electrical limits, pin functions and recommended footprint come from the
Epson FA-238V / FA-238 / TSX-3225 data sheet (page 1: the specification table,
Table 2, the internal connection and footprint drawings). Product numbers come
from the catalog the family reads. The 25 MHz unit for the KSZ9031RNX meets
Table 10-1 of the KSZ9031RNX data sheet, DS00002117K (25 MHz, +/-50 ppm,
40 ohms typical). Table 10-1 states no load capacitance: CL 16 pF is derived
from the 22 pF capacitors Figure 10-1 draws on XI and XO, under the 5 pF stray
allowance ``add_load_caps`` assumes (22 pF / 2 + 5 pF = 16 pF).
"""

from collections import Counter
from collections.abc import Callable, Iterable, Sequence

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_lm1117ld.py uses it
# for the same reason).
from jitx._translate.design import package_design
from jitx.circuit import Circuit
from jitx.inspect import extract, visit
from jitx.landpattern import Pad, PadMapping, PadShape
from jitx.net import Net, Port, ShortTrace
from jitx.sample import SampleDesign
from jitx.test import TestCase
from jitx.units import F
from jitxlib.parts import Capacitor, Lock, LockMode, PartSource
from jitxlib.parts.providers import CsvParts

from jitxexamples.components.crystals.seiko_epson_TSX_3225 import (
    TSX3225,
    TSX3225Package,
    TSX_3225_32_0000MF10Z_W6,
    CatalogEntry,
    catalog,
)
from tests.parts import PartsTestDesign


def ksz9031rnx_crystal() -> TSX3225:
    """25 MHz, CL 16 pF (derived from Figure 10-1's 22 pF capacitors), +/-10 ppm
    at +25 C, +/-10 ppm over -20 to +75 C."""
    return TSX3225(
        frequency=25e6,
        load_capacitance=16e-12,
        frequency_tolerance=10e-6,
        frequency_stability=10e-6,
        temperature_range=(-20, 75),
    )


def catalog_crystal(entry: CatalogEntry) -> TSX3225:
    """The unit one catalog row describes."""
    return TSX3225(
        frequency=entry.frequency_mhz * 1e6,
        load_capacitance=entry.load_capacitance_pf * 1e-12,
        frequency_tolerance=entry.tolerance_ppm * 1e-6,
        frequency_stability=entry.stability_ppm * 1e-6,
        temperature_range=(entry.temperature_min_c, entry.temperature_max_c),
        part_number=entry.part_number,
    )


def catalog_entry(part_number: str) -> CatalogEntry:
    (entry,) = (e for e in catalog() if e.part_number == part_number)
    return entry


class ReferenceClock(Circuit):
    def __init__(self, make_crystal: Callable[[], TSX3225]) -> None:
        self.gnd = Net(name="GND")
        self.crystal = make_crystal()
        self.gnd += self.crystal.GND0 + self.crystal.GND1
        self.crystal.add_load_caps(self.gnd)


class ReferenceClockDesign(PartsTestDesign):
    def __init__(
        self, make_crystal: Callable[[], TSX3225] = ksz9031rnx_crystal
    ) -> None:
        self.circuit = ReferenceClock(make_crystal)


# The example CSV alone, with no `ideal` behind it: a load-capacitor query the
# CSV cannot answer fails resolution instead of becoming an ideal part.
EXAMPLE_CSV_ONLY = PartSource(
    [p for p in PartsTestDesign.parts if isinstance(p, CsvParts)]
)


class ExampleCsvOnlyDesign(SampleDesign):
    parts = EXAMPLE_CSV_ONLY
    parts_lock = Lock(mode=LockMode.OFF)

    def __init__(self, make_crystal: Callable[[], TSX3225]) -> None:
        self.circuit = ReferenceClock(make_crystal)


class TwoCrystals(Circuit):
    def __init__(self) -> None:
        self.gnd = Net(name="GND")
        self.ksz = ksz9031rnx_crystal()
        self.nrf = TSX_3225_32_0000MF10Z_W6()
        self.gnd += self.ksz.GND0 + self.ksz.GND1 + self.nrf.GND0 + self.nrf.GND1
        self.ksz.add_load_caps(self.gnd)
        self.nrf.add_load_caps(self.gnd)


class TwoCrystalsDesign(PartsTestDesign):
    def __init__(self) -> None:
        self.circuit = TwoCrystals()


def connectivity(nets: Iterable[Net]) -> dict[int, set[int]]:
    """For each net and port the nets reach, by id, the ids of everything
    joined to it through those nets."""
    groups: dict[int, set[int]] = {}

    def join(a: object, b: object) -> None:
        merged = groups.get(id(a), {id(a)}) | groups.get(id(b), {id(b)})
        for member in merged:
            groups[member] = merged

    def walk(net: Net) -> None:
        for member in net.connected:
            join(net, member)
            if isinstance(member, Net):
                walk(member)

    for net in nets:
        walk(net)
    return groups


def single_pad(mapping: PadMapping, port: Port) -> Pad:
    pads = mapping[port]
    if isinstance(pads, Sequence):
        if len(pads) != 1:
            raise AssertionError(f"{port} maps to {len(pads)} pads")
        return pads[0]
    return pads


class TestTSX3225(TestCase):
    def test_preset_keeps_its_published_values(self) -> None:
        crystal = TSX_3225_32_0000MF10Z_W6()
        self.assertEqual(crystal.mpn, "TSX-3225 32.0000MF10Z-W6")
        self.assertEqual(crystal.manufacturer, "Seiko Epson")
        self.assertEqual(crystal.frequency, 32e6)
        self.assertEqual(crystal.load_capacitance, 12e-12)
        self.assertEqual(crystal.frequency_tolerance, 10e-6)
        self.assertEqual(crystal.esr, 40)
        self.assertAlmostEqual(crystal.max_drive_level, 100e-6)
        self.assertEqual(crystal.shunt_capacitance, 1.31e-12)
        self.assertEqual(crystal.motional_capacitance, 4.41e-15)
        # Nothing ties the distributor code to a catalog row, so the preset
        # takes none of a row's stability or temperature range.
        self.assertNotIsInstance(crystal, TSX3225)
        self.assertIsInstance(crystal, TSX3225Package)
        self.assertFalse(hasattr(crystal, "frequency_stability"))
        self.assertFalse(hasattr(crystal, "temperature_range"))

    def test_32_mhz_12_pf_specification_is_one_catalog_row(self) -> None:
        crystal = TSX3225(
            frequency=32e6,
            load_capacitance=12e-12,
            frequency_tolerance=10e-6,
            frequency_stability=10e-6,
            temperature_range=(-20, 75),
        )
        self.assertEqual(crystal.mpn, "X1E0000210164")

    def test_ksz9031rnx_crystal(self) -> None:
        crystal = ksz9031rnx_crystal()
        self.assertEqual(crystal.mpn, "X1E0000210135")
        # KSZ9031RNX Table 10-1: 25 MHz, +/-50 ppm, 40 ohms typical.
        self.assertEqual(crystal.frequency, 25e6)
        self.assertLessEqual(
            crystal.frequency_tolerance + crystal.frequency_stability, 50e-6
        )
        self.assertEqual(crystal.esr, 40)

    def test_ksz9031rnx_load_caps_resolve_from_the_example_csv(self) -> None:
        # KSZ9031RNX Figure 10-1 draws 22 pF on XI and XO; with the 5 pF stray
        # allowance, 2 x (16 pF - 5 pF) = 22 pF. The 25 MHz rows at CL 8 pF and
        # 9 pF ask for the E24 values nearest 6 pF and 8 pF.
        for name, make_crystal, expected in (
            ("KSZ9031RNX, CL 16 pF", ksz9031rnx_crystal, 22e-12),
            (
                "X1E0000210131, CL 8 pF",
                lambda: catalog_crystal(catalog_entry("X1E0000210131")),
                6.2e-12,
            ),
            (
                "X1E0000210132, CL 9 pF",
                lambda: catalog_crystal(catalog_entry("X1E0000210132")),
                8.2e-12,
            ),
        ):
            with self.subTest(crystal=name):
                circuit = ReferenceClockDesign(make_crystal).circuit
                caps = list(extract(circuit, Capacitor))
                self.assertEqual(len(caps), 2)
                for cap in caps:
                    capacitance = cap.capacitance
                    assert capacitance is not None
                    self.assertAlmostEqual(capacitance.m_as(F), expected)
                    self.assertEqual(cap.temperature_coefficient_code, "C0G")
                    # Only the CSV answers a C0G query in the test chain.
                    self.assertIsNotNone(cap.manufacturer)

    def test_every_catalog_row_gets_load_caps_from_the_example_csv(self) -> None:
        for entry in catalog():
            with self.subTest(
                part_number=entry.part_number, cl_pf=entry.load_capacitance_pf
            ):
                circuit = ExampleCsvOnlyDesign(
                    lambda entry=entry: catalog_crystal(entry)
                ).circuit
                caps = list(extract(circuit, Capacitor))
                self.assertEqual(len(caps), 2)
                for cap in caps:
                    self.assertEqual(cap.temperature_coefficient_code, "C0G")
                    self.assertIsNotNone(cap.manufacturer)
                    self.assertFalse(str(cap.mpn).startswith("IDEAL-"))

    def test_unlisted_combination_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "no product number"):
            TSX3225(
                frequency=25e6,
                load_capacitance=16e-12,
                frequency_tolerance=10e-6,
                frequency_stability=10e-6,
                temperature_range=(-40, 85),
            )

    def test_combination_listed_twice_raises(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"several product numbers .*X1E0000210111, X1E0000210803\. "
            r"Pass part_number= to choose one\.",
        ):
            TSX3225(
                frequency=16e6,
                load_capacitance=8e-12,
                frequency_tolerance=10e-6,
                frequency_stability=10e-6,
                temperature_range=(-20, 75),
            )

    def test_part_number_chooses_among_duplicate_rows(self) -> None:
        # The three specifications the catalog lists under two product numbers.
        for mhz, cl_pf, numbers in (
            (16, 8, ("X1E0000210111", "X1E0000210803")),
            (24, 18, ("X1E0000210527", "X1E0000210710")),
            (25, 18, ("X1E0000210263", "X1E0000210315")),
        ):
            for number in numbers:
                with self.subTest(mhz=mhz, part_number=number):
                    crystal = TSX3225(
                        frequency=mhz * 1e6,
                        load_capacitance=cl_pf * 1e-12,
                        frequency_tolerance=10e-6,
                        frequency_stability=10e-6,
                        temperature_range=(-20, 75),
                        part_number=number,
                    )
                    self.assertEqual(crystal.mpn, number)

    def test_part_number_outside_the_matches_raises(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"X1E0000210135 is not a product number Epson lists for .*; "
            r"it lists X1E0000210111, X1E0000210803",
        ):
            TSX3225(
                frequency=16e6,
                load_capacitance=8e-12,
                frequency_tolerance=10e-6,
                frequency_stability=10e-6,
                temperature_range=(-20, 75),
                part_number="X1E0000210135",
            )

    def test_unlisted_combination_labels_tolerance_and_stability(self) -> None:
        with self.assertRaises(ValueError) as raised:
            TSX3225(
                frequency=25e6,
                load_capacitance=16e-12,
                frequency_tolerance=10e-6,
                frequency_stability=10e-6,
                temperature_range=(-40, 85),
            )
        message = str(raised.exception)
        self.assertIn(
            "CL 16 pF, tolerance +/-10 ppm at +25 C, "
            "stability +/-10 ppm over -20 to 75 C",
            message,
        )
        self.assertNotIn("several", message)

    def test_catalog_matches_the_data_sheet(self) -> None:
        entries = catalog()
        numbers = Counter(e.part_number for e in entries)
        self.assertEqual(len(numbers), len(entries))
        for entry in entries:
            with self.subTest(part_number=entry.part_number):
                # The data sheet's product number is X1E000021xxxx17; the
                # catalog's omits that two-digit 17 suffix.
                self.assertRegex(entry.part_number, r"^X1E000021\d{4}$")
                # Nominal frequency range 16 MHz to 50 MHz.
                self.assertTrue(16 <= entry.frequency_mhz <= 50)
                # Table 2: 60 ohms max below 21 MHz, 40 ohms max above.
                self.assertLessEqual(
                    entry.esr_max_ohm, 60 if entry.frequency_mhz < 21 else 40
                )
                # Level of drive 200 uW max.
                self.assertEqual(entry.drive_level_max_uw, 200)

    def test_landpattern_matches_the_recommended_footprint(self) -> None:
        crystal = TSX_3225_32_0000MF10Z_W6()
        lp = crystal.landpattern
        self.assertEqual(sum(1 for _ in visit(lp, Pad)), 4)
        for n, (x, y) in {
            1: (-1.1, -0.8),
            2: (1.1, -0.8),
            3: (1.1, 0.8),
            4: (-1.1, 0.8),
        }.items():
            pad = lp.p[n]
            shape = pad.shape.shape if isinstance(pad.shape, PadShape) else pad.shape
            lox, loy, hix, hiy = shape.to_shapely().bounds
            self.assertAlmostEqual(hix - lox, 1.4)
            self.assertAlmostEqual(hiy - loy, 1.15)
            placement = pad.transform
            assert placement is not None
            px, py = placement.translation
            self.assertAlmostEqual(px, x)
            self.assertAlmostEqual(py, y)

    def test_pins_1_and_3_are_the_crystal(self) -> None:
        crystal = TSX_3225_32_0000MF10Z_W6()
        mapping = crystal.mappings[0]
        assert isinstance(mapping, PadMapping)
        lp = crystal.landpattern
        self.assertIs(single_pad(mapping, crystal.OSC1), lp.p[1])
        self.assertIs(single_pad(mapping, crystal.OSC2), lp.p[3])
        # Pads 2 and 4 are connected to the cover.
        self.assertIs(single_pad(mapping, crystal.GND1), lp.p[2])
        self.assertIs(single_pad(mapping, crystal.GND0), lp.p[4])

    def test_load_caps_join_the_crystal_pins_by_short_trace(self) -> None:
        circuit = ReferenceClockDesign().circuit
        assert isinstance(circuit, ReferenceClock)
        crystal = circuit.crystal
        caps = list(extract(circuit, Capacitor))
        pairs: list[tuple[Port, Port]] = []
        for trace in extract(circuit, ShortTrace):
            first, second = trace.connected
            assert isinstance(first, Port) and isinstance(second, Port)
            pairs.append((first, second))
        self.assertEqual(len(pairs), 2)
        served = []
        for first, second in pairs:
            # ShortTrace(cap.p1, <crystal pin>), one per capacitor.
            cap = next(c for c in caps if c.p1 is first)
            self.assertTrue(second is crystal.OSC1 or second is crystal.OSC2)
            served.append((cap, second))
        self.assertEqual({id(c) for c, _ in served}, {id(c) for c in caps})
        self.assertEqual(
            {id(pin) for _, pin in served}, {id(crystal.OSC1), id(crystal.OSC2)}
        )
        # The other half of the rule: each capacitor's p2 is on the ground net.
        ground = connectivity(extract(circuit, Net))[id(circuit.gnd)]
        for cap in caps:
            self.assertIn(id(cap.p2), ground, f"{cap.mpn} p2 is not on GND")
            self.assertNotIn(id(cap.p1), ground, f"{cap.mpn} p1 is on GND")

    def test_two_crystals_translate(self) -> None:
        packaged = package_design(TwoCrystalsDesign())
        self.assertIsNotNone(packaged.v1)

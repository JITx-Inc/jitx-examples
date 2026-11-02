"""Checks of the KSZ9031RNX component against its data sheet, DS00002117K.

Pin numbers and names come from Table 2-1 ("Signals - KSZ9031RNX"); package
and land-pattern dimensions from Figures 13-2, 13-3, 13-5, 13-6, 13-8 and 13-9;
ordering codes from the Product Identification System page. The tables below
are transcribed from the data sheet here, not imported from the component.
"""

import re
from collections.abc import Sequence

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_lm1117ld.py uses it
# for the same reason).
from jitx._translate.design import package_design
from jitx.circuit import Circuit
from jitx.container import inline
from jitx.feature import Paste
from jitx.inspect import extract, visit
from jitx.landpattern import Pad, PadMapping, PadShape
from jitx.net import Port
from jitx.sample import SampleDesign
from jitx.symbol import Pin
from jitx.test import TestCase
from jitxlib.symbols.box import BoxSymbol
from shapely.geometry import MultiPolygon

from jitxlib.landpatterns.generators.qfn import QFN

from jitxexamples.components.ethernet_phys.microchip_KSZ9031RNX import (
    KSZ9031RNX,
)

# Table 2-1, every pin in pin-number order, names as the table prints them.
PIN_TABLE: dict[int, str] = {
    1: "AVDDH",
    2: "TXRXP_A",
    3: "TXRXM_A",
    4: "AVDDL",
    5: "TXRXP_B",
    6: "TXRXM_B",
    7: "TXRXP_C",
    8: "TXRXM_C",
    9: "AVDDL",
    10: "TXRXP_D",
    11: "TXRXM_D",
    12: "AVDDH",
    13: "NC",
    14: "DVDDL",
    15: "LED2/PHYAD1",
    16: "DVDDH",
    17: "LED1/PHYAD0/PME_N1",
    18: "DVDDL",
    19: "TXD0",
    20: "TXD1",
    21: "TXD2",
    22: "TXD3",
    23: "DVDDL",
    24: "GTX_CLK",
    25: "TX_EN",
    26: "DVDDL",
    27: "RXD3/MODE3",
    28: "RXD2/MODE2",
    29: "VSS",
    30: "DVDDL",
    31: "RXD1/MODE1",
    32: "RXD0/MODE0",
    33: "RX_DV/CLK125_EN",
    34: "DVDDH",
    35: "RX_CLK/PHYAD2",
    36: "MDC",
    37: "MDIO",
    38: "INT_N/PME_N2",
    39: "DVDDL",
    40: "DVDDH",
    41: "CLK125_NDO/LED_MODE",
    42: "RESET_N",
    43: "LDO_O",
    44: "AVDDL_PLL",
    45: "XO",
    46: "XI",
    47: "NC",
    48: "ISET",
}

NUMBERED = re.compile(r"^(TXD|RXD)(\d)$")

# Product Identification System, ordering examples a) to h). f) and h) are the
# tape-and-reel (TR) forms of e) and g) and are not modeled.
# (temperature code, bond-wire code) -> part number
PIS_TRAY_EXAMPLES: dict[tuple[str, str], str] = {
    ("C", "A"): "KSZ9031RNXCA",  # a)
    ("C", "C"): "KSZ9031RNXCC",  # b)
    ("I", "A"): "KSZ9031RNXIA",  # c)
    ("I", "C"): "KSZ9031RNXIC",  # d)
    ("U", "B"): "KSZ9031RNXUB-VAO",  # e)
    ("V", "B"): "KSZ9031RNXVB-VAO",  # g)
}
PIS_TEMPERATURES = ("C", "I", "U", "V")
PIS_BOND_WIRES = ("A", "B", "C")


class DefaultDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        phy = KSZ9031RNX()


class PUADesign(SampleDesign):
    @inline
    class circuit(Circuit):
        phy = KSZ9031RNX(temperature="U", package="B")


class PSADesign(SampleDesign):
    @inline
    class circuit(Circuit):
        phy = KSZ9031RNX(temperature="I", package="C")


def expected_ports(phy: KSZ9031RNX) -> dict[int, Port]:
    """The port each pin of Table 2-1 should map to, found by the table's name.

    The first name of a multi-function pin is the port. ``TXD0`` is ``TXD[0]``.
    A name the table repeats is a list, indexed by occurrence in pin order.
    """
    seen: dict[str, int] = {}
    ports: dict[int, Port] = {}
    for pin, label in PIN_TABLE.items():
        name = label.split("/")[0]
        numbered = NUMBERED.match(name)
        if numbered:
            ports[pin] = getattr(phy, numbered.group(1))[int(numbered.group(2))]
            continue
        attribute = getattr(phy, name)
        if isinstance(attribute, Port):
            ports[pin] = attribute
        else:
            index = seen.get(name, 0)
            seen[name] = index + 1
            ports[pin] = attribute[index]
    return ports


def single_pad(mapping: PadMapping, port: Port) -> Pad:
    pads = mapping[port]
    if isinstance(pads, Sequence):
        if len(pads) != 1:
            raise AssertionError(f"{port} maps to {len(pads)} pads")
        return pads[0]
    return pads


def bounds(pad: Pad) -> tuple[float, float]:
    """Width and height of a pad's copper in its own frame."""
    shape = pad.shape.shape if isinstance(pad.shape, PadShape) else pad.shape
    lox, loy, hix, hiy = shape.to_shapely().bounds
    return hix - lox, hiy - loy


def center(pad: Pad) -> tuple[float, float]:
    placement = pad.transform
    if placement is None:
        raise AssertionError("pad has no placement")
    x, y = placement.translation
    return x, y


class TestKSZ9031RNX(TestCase):
    def test_pins_match_table_2_1(self) -> None:
        phy = DefaultDesign().circuit.phy
        self.assertIsInstance(phy, KSZ9031RNX)
        mapping = phy.mappings[0]
        lp = phy.landpattern
        for pin, port in expected_ports(phy).items():
            with self.subTest(pin=pin, name=PIN_TABLE[pin]):
                self.assertIs(single_pad(mapping, port), lp.p[pin])
        self.assertIs(single_pad(mapping, phy.P_GND), lp.thermal_pads[0])

    def test_port_and_pad_counts(self) -> None:
        phy = DefaultDesign().circuit.phy
        # 48 pins and the exposed paddle.
        self.assertEqual(len(list(extract(phy, Port))), 49)
        self.assertEqual(sum(1 for _ in visit(phy.landpattern, Pad)), 49)

    def test_nc_pins_are_no_connect(self) -> None:
        phy = DefaultDesign().circuit.phy
        self.assertTrue(all(nc.is_no_connect() for nc in phy.NC))
        self.assertFalse(phy.LDO_O.is_no_connect())

    def test_symbol_boxes_cover_every_port_once(self) -> None:
        phy = DefaultDesign().circuit.phy
        seen: list[int] = []
        for box in phy.symbols:
            self.assertIsInstance(box, BoxSymbol)
            # A port listed twice in one box keeps only its last pin.
            self.assertEqual(len(list(box.mapping)), len(list(extract(box, Pin))))
            seen.extend(id(port) for port in box.mapping)
        self.assertEqual(len(seen), len(set(seen)))
        self.assertEqual(set(seen), {id(p) for p in extract(phy, Port)})

    def test_pva_land_pattern_figure_13_3(self) -> None:
        self.check_land_pattern(
            DefaultDesign().circuit.phy,
            contact_pad_length=0.85,
            exposed_pad=3.60,
            paste_window=1.425,
        )

    def test_pua_land_pattern_figure_13_6(self) -> None:
        # Figure 13-6: Y1 0.90 max, X2 = Y2 5.20 max.
        self.check_land_pattern(
            PUADesign().circuit.phy,
            contact_pad_length=0.90,
            exposed_pad=5.20,
            paste_window=2.225,
        )

    def test_psa_land_pattern_figure_13_9(self) -> None:
        self.check_land_pattern(
            PSADesign().circuit.phy,
            contact_pad_length=0.90,
            exposed_pad=5.20,
            paste_window=2.225,
        )

    def check_land_pattern(
        self,
        phy: KSZ9031RNX,
        contact_pad_length: float,
        exposed_pad: float,
        paste_window: float,
    ) -> None:
        lp = phy.landpattern
        # Every contact pad is X1 = 0.30 wide and Y1 long.
        for n in range(1, 49):
            width, height = bounds(lp.p[n])
            self.assertAlmostEqual(width, contact_pad_length)
            self.assertAlmostEqual(height, 0.30)

        # C1: pins 1 and 36 face each other across the package.
        x1, y1 = center(lp.p[1])
        x36, y36 = center(lp.p[36])
        self.assertAlmostEqual(y1, y36)
        self.assertAlmostEqual(x36 - x1, 6.90)
        # C2: pins 13 and 48 face each other top to bottom.
        x13, y13 = center(lp.p[13])
        x48, y48 = center(lp.p[48])
        self.assertAlmostEqual(x13, x48)
        self.assertAlmostEqual(y48 - y13, 6.90)
        # E: 0.50 mm pitch, pin 1 at the top of the left side.
        _, y2 = center(lp.p[2])
        self.assertAlmostEqual(y1 - y2, 0.50)
        self.assertGreater(y1, 0.0)
        self.assertLess(x1, 0.0)
        # Pin 1's land reaches past the edge of the 7.00 mm body (D, E).
        self.assertLess(x1 - contact_pad_length / 2, -7.00 / 2)

        # X2 x Y2 exposed pad at the origin, with a 2 x 2 paste window grid.
        thermal = lp.thermal_pads[0]
        self.assertEqual(center(thermal), (0.0, 0.0))
        width, height = bounds(thermal)
        self.assertAlmostEqual(width, exposed_pad)
        self.assertAlmostEqual(height, exposed_pad)
        pastes = list(extract(thermal, Paste))
        self.assertEqual(len(pastes), 1)
        windows = pastes[0].shape.to_shapely().g
        self.assertIsInstance(windows, MultiPolygon)
        assert isinstance(windows, MultiPolygon)
        self.assertEqual(len(windows.geoms), 4)
        for window in windows.geoms:
            lox, loy, hix, hiy = window.bounds
            self.assertAlmostEqual(hix - lox, paste_window)
            self.assertAlmostEqual(hiy - loy, paste_window)

    def test_ordering_codes(self) -> None:
        self.assertEqual(DefaultDesign().circuit.phy.mpn, "KSZ9031RNXCA")
        self.assertEqual(PUADesign().circuit.phy.mpn, "KSZ9031RNXUB-VAO")
        self.assertEqual(PSADesign().circuit.phy.mpn, "KSZ9031RNXIC")

    def test_every_ordering_example(self) -> None:
        for temperature in PIS_TEMPERATURES:
            for bond_wire in PIS_BOND_WIRES:
                expected = PIS_TRAY_EXAMPLES.get((temperature, bond_wire))
                with self.subTest(temperature=temperature, package=bond_wire):
                    if expected is None:
                        with self.assertRaises(ValueError):
                            KSZ9031RNX(temperature=temperature, package=bond_wire)
                    else:
                        phy = KSZ9031RNX(temperature=temperature, package=bond_wire)
                        self.assertEqual(phy.mpn, expected)

    def test_land_pattern_guard_fails_loud(self) -> None:
        # RecommendedQFN overrides two private methods QFN inherits; if either
        # disappears the component must raise rather than fall back silently.
        for name in ("_lead_placements", "_pad_rectangle"):
            owner = next(c for c in QFN.__mro__ if name in c.__dict__)
            original = owner.__dict__[name]
            delattr(owner, name)
            try:
                with self.subTest(method=name):
                    with self.assertRaisesRegex(TypeError, name):
                        KSZ9031RNX()
            finally:
                setattr(owner, name, original)

    def test_unlisted_ordering_code_raises(self) -> None:
        with self.assertRaises(ValueError):
            KSZ9031RNX(temperature="C", package="B")

    def test_value_unset(self) -> None:
        self.assertIsNone(DefaultDesign().circuit.phy.value)

    def test_design_translates(self) -> None:
        packaged = package_design(DefaultDesign())
        self.assertIsNotNone(packaged.v1)

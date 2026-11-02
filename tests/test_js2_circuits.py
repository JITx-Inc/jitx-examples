"""JS2: tests for the Ethernet PHY board reference solution.

Pin numbers, strap functions and component values are transcribed from the
KSZ9031RNX data sheet, DS00002117K: Table 2-1 (pins), Table 2-2 (strap-in
options), Section 8.0 (reset), Section 9.0 (strap resistor values and LED
drive), Table 10-1 (crystal), Section 11.0 (LDO controller) and Section 12.0
(center taps); and from Figure 8 of Microchip application note ANLAN206 (the
LDO controller's MOSFET network).
"""

from collections.abc import Callable, Iterable, Sequence
from typing import cast

# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_lm1117ld.py uses it
# for the same reason).
from jitx._translate.design import package_design
from jitx import Circuit, Component, Net
from jitx.common import Power
from jitx.inspect import decompose, extract, visit
from jitx.landpattern import Pad, PadMapping
from jitx.net import Port, ShortTrace
from jitx.placement import Placement
from jitx.test import TestCase
from jitx.units import F, ohm
from jitxlib.parts import Capacitor, Inductor, Resistor
from jitxlib.protocols.ethernet.mdi.mdi1000base_t import MDI1000BaseT
from jitxlib.protocols.ethernet.mii.miim import MIIM
from jitxlib.protocols.ethernet.mii.rgmii import RGMII

from jitxexamples.components.connectors.bel_fuse_0826_1G1T_23_F import (
    Bel_0826_1G1T_23_F,
)
from jitxexamples.components.ethernet_phys.microchip_KSZ9031RNX import KSZ9031RNX
from jitxexamples.components.fets_p_ch.NTF6P02T3G import NTF6P02T3G
from jitxexamples.components.power_switchmode.texas_instruments_TPS62933DRLR import (
    TPS62933DRLRCircuit,
)
from jitxexamples.jumpstart_kits.js2_circuits.main import (
    EthernetPhyBoard,
    EthernetPhyDesign,
)
from jitxexamples.jumpstart_kits.js2_circuits.phy import KSZ9031RNXCircuit
from jitxexamples.jumpstart_kits.js2_circuits.straps import (
    DEFAULT_STRAPS,
    LedMode,
    Mode,
    Strap,
    StrapConfig,
)
from tests.parts import PartsTestDesign

PassivePart = Resistor | Capacitor | Inductor

#: Table 2-2: each strap, its pin number, and the PHY port on that pin.
STRAP_PINS: dict[Strap, tuple[int, Callable[[KSZ9031RNX], Port]]] = {
    Strap.PHYAD2: (35, lambda u: u.RX_CLK),
    Strap.PHYAD1: (15, lambda u: u.LED2),
    Strap.PHYAD0: (17, lambda u: u.LED1),
    Strap.MODE3: (27, lambda u: u.RXD[3]),
    Strap.MODE2: (28, lambda u: u.RXD[2]),
    Strap.MODE1: (31, lambda u: u.RXD[1]),
    Strap.MODE0: (32, lambda u: u.RXD[0]),
    Strap.CLK125_EN: (33, lambda u: u.RX_DV),
    Strap.LED_MODE: (41, lambda u: u.CLK125_NDO),
}

#: Section 9.0: 10 kOhm pull-up to DVDDH, 1.0 kOhm pull-down to ground.
PULL_UP_OHMS = 10e3
PULL_DOWN_OHMS = 1.0e3

#: Section 9.0, Figure 9-1: each LED takes DVDDH through 220 Ohm.
LED_SERIES_OHMS = 220.0

#: The packages the design-level defaults allow: 0402 and larger.
RESISTOR_CASES = {"0402", "0603", "0805", "1206"}
CAPACITOR_CASES = {"0402", "0603", "0805", "1206", "1210"}


class JS2TestDesign(PartsTestDesign, EthernetPhyDesign):
    """The kit's design, resolving passives through the test parts chain."""


def board(straps: StrapConfig = DEFAULT_STRAPS) -> EthernetPhyBoard:
    circuit = JS2TestDesign(straps).circuit
    assert isinstance(circuit, EthernetPhyBoard)
    return circuit


def leaves(port: Port) -> list[Port]:
    """The single pins of ``port``, in declaration order."""
    found = [p for p in extract(port, Port) if not list(extract(p, Port))]
    return found or [port]


class Connectivity:
    """Which single pins share a net anywhere under ``root``.

    A net of bundle ports joins the bundles member for member, as ``+`` does.
    """

    def __init__(self, root: Circuit) -> None:
        self._parent: dict[Port, Port] = {}
        for net in extract(root, Net):
            groups = [leaves(p) for p in net]
            for group in groups[1:]:
                for a, b in zip(groups[0], group, strict=True):
                    self._union(a, b)

    def _find(self, port: Port) -> Port:
        root = port
        while (parent := self._parent.get(root, root)) is not root:
            root = parent
        return root

    def _union(self, a: Port, b: Port) -> None:
        self._parent[self._find(a)] = self._find(b)

    def connected(self, a: Port, b: Port) -> bool:
        return self._find(a) is self._find(b)


def ohms(r: Resistor) -> float:
    return float(r.value.to(ohm).magnitude)


def farads(c: Capacitor) -> float:
    return float(c.value.to(F).magnitude)


def touching[T: PassivePart](
    conn: Connectivity, parts: Iterable[T], port: Port
) -> list[T]:
    """The parts with a pad on the same net as ``port``."""
    return [
        p for p in parts if conn.connected(p.p1, port) or conn.connected(p.p2, port)
    ]


def other_pad(conn: Connectivity, part: PassivePart, port: Port) -> Port:
    return part.p2 if conn.connected(part.p1, port) else part.p1


def single_pad(mapping: PadMapping, port: Port) -> Pad:
    pads = mapping[port]
    if isinstance(pads, Sequence):
        assert len(pads) == 1, f"{port} maps to {len(pads)} pads"
        return pads[0]
    return pads


def short_trace_partner(circuit: Circuit, port: Port) -> list[Port]:
    """The ports joined to ``port`` by a ``ShortTrace`` under ``circuit``."""
    partners: list[Port] = []
    for st in extract(circuit, ShortTrace):
        ports = list(st)
        if port in ports:
            partners.extend(p for p in ports if isinstance(p, Port) and p is not port)
    return partners


class TestHierarchy(TestCase):
    def test_children(self) -> None:
        top = board()
        children = list(decompose(top, Circuit))
        self.assertEqual(
            sorted(type(c).__name__ for c in children),
            sorted(
                [
                    TPS62933DRLRCircuit.__name__,
                    KSZ9031RNXCircuit.__name__,
                    Bel_0826_1G1T_23_F.__name__,
                ]
            ),
        )
        # The top level adds only the MDIO pull-up and the four center-tap
        # capacitors.
        own = list(decompose(top, Component))
        self.assertEqual(len(own), 5)
        for part in own:
            self.assertIsInstance(part, (Resistor, Capacitor))

    def test_top_level_parts(self) -> None:
        """The MDIO pull-up.

        KSZ9031RNX Table 2-1, pin 37: MDIO takes a 1.0 to 4.7 kOhm pull-up;
        MDC takes none.
        """
        top = board()
        conn = Connectivity(top)
        own = list(decompose(top, Component))
        resistors = [p for p in own if isinstance(p, Resistor)]
        capacitors = [p for p in own if isinstance(p, Capacitor)]
        u1 = top.phy.u1
        v3v3 = top.reg_3v3.vout.Vp
        on_pin = touching(conn, resistors, u1.MDIO)
        self.assertEqual(on_pin, resistors)
        self.assertEqual(len(on_pin), 1)
        r = on_pin[0]
        self.assertGreaterEqual(ohms(r), 1.0e3)
        self.assertLessEqual(ohms(r), 4.7e3)
        self.assertTrue(conn.connected(other_pad(conn, r, u1.MDIO), v3v3))
        self.assertEqual(touching(conn, resistors, u1.MDC), [])

        self.assertEqual(
            [c for c in capacitors if c not in top.c_ct],
            [],
        )

    def test_center_taps_kept_separate(self) -> None:
        """KSZ9031RNX Section 12.0: the four device-side center taps must be
        kept separate from one another, each connected through its own 0.1 uF
        common-mode capacitor to ground, and to no supply.
        """
        top = board()
        conn = Connectivity(top)
        jack = top.jack
        capacitors = [p for p in decompose(top, Component) if isinstance(p, Capacitor)]
        self.assertEqual(len(capacitors), 4)
        for n in range(1, 5):
            tap = jack.CT[n]
            with self.subTest(center_tap=n):
                on_tap = touching(conn, capacitors, tap)
                self.assertEqual(len(on_tap), 1)
                c = on_tap[0]
                self.assertAlmostEqual(farads(c), 100e-9)
                self.assertIn(tap, short_trace_partner(top, c.p1))
                self.assertTrue(conn.connected(other_pad(conn, c, tap), top.vin.Vn))
                self.assertTrue(conn.connected(tap, jack.J.TRCT[n]))
                for other in range(1, 5):
                    if other != n:
                        self.assertFalse(conn.connected(tap, jack.CT[other]))
                for rail in (top.reg_3v3.vout.Vp, top.phy.q_ldo.d, top.vin.Vp):
                    self.assertFalse(conn.connected(tap, rail))

    def test_jack_shield_off_board_nets_and_other_ports_wired(self) -> None:
        """The board wires every jack port but the shield: each center tap
        takes a capacitor and the PHY drives both LEDs. The shield is on no
        board net, left for the enclosure design; the jack terminates its
        cable side internally.
        """
        top = board()
        jack = top.jack
        wired = [*jack.CT.values(), jack.LED1.a, jack.LED1.c, jack.LED2.a, jack.LED2.c]
        # The nets the board itself makes, not those inside the jack circuit.
        on_board_nets: set[Port] = set()
        for net in decompose(top, Net):
            for port in net:
                on_board_nets.update(leaves(port))
        for port in wired:
            with self.subTest(port=str(port)):
                self.assertIn(port, on_board_nets)
        self.assertNotIn(jack.SHIELD, on_board_nets)

    def test_one_regulator_enabled_by_default(self) -> None:
        """One TPS62933 stage makes 3.3 V; its EN floats, which enables it."""
        top = board()
        regulators = [
            c for c in decompose(top, Circuit) if isinstance(c, TPS62933DRLRCircuit)
        ]
        self.assertEqual(regulators, [top.reg_3v3])
        self.assertIsNone(top.reg_3v3.enable)
        self.assertTrue(top.reg_3v3.buck.EN.is_no_connect())

    def test_rails_reach_the_right_supply_pins(self) -> None:
        """3.3 V from the regulator reaches AVDDH and DVDDH; the 1.2 V core
        pins sit on the LDO MOSFET's drain, apart from 3.3 V and the input.
        """
        top = board()
        conn = Connectivity(top)
        u1 = top.phy.u1
        v3v3, core = top.reg_3v3.vout.Vp, top.phy.q_ldo.d
        for pin in (*u1.AVDDH, *u1.DVDDH):
            self.assertTrue(conn.connected(v3v3, pin))
            self.assertFalse(conn.connected(core, pin))
        for pin in (*u1.AVDDL, u1.AVDDL_PLL, *u1.DVDDL):
            self.assertTrue(conn.connected(core, pin))
            self.assertFalse(conn.connected(v3v3, pin))
            self.assertFalse(conn.connected(top.vin.Vp, pin))
        self.assertTrue(conn.connected(top.vin.Vp, top.reg_3v3.vin.Vp))
        self.assertFalse(conn.connected(top.vin.Vp, v3v3))

    def test_wired_only_through_boundary_ports(self) -> None:
        top = board()
        inner: set[Port] = set()
        for child in decompose(top, Circuit):
            for part in extract(child, Component):
                inner.update(extract(part, Port))
        for net in decompose(top, Net):
            for port in net:
                for pin in leaves(port):
                    self.assertNotIn(pin, inner)


class TestTypedPorts(TestCase):
    def test_boundary_port_types(self) -> None:
        top = board()
        self.assertIsInstance(top.vin, Power)
        self.assertIsInstance(top.rgmii, RGMII)
        self.assertIsInstance(top.miim, MIIM)
        phy = top.phy
        self.assertIsInstance(phy.vdd_3v3, Power)
        self.assertIsInstance(phy.rgmii, RGMII)
        self.assertIsInstance(phy.miim, MIIM)
        self.assertIsInstance(phy.mdi, MDI1000BaseT)
        # RESET_N and INT_N are single active-low lines: single-pin ports, not
        # bundles, at both levels.
        for port in (top.reset_n, top.int_n, phy.reset_n, phy.int_n):
            self.assertIsInstance(port, Port)
            self.assertEqual(list(extract(port, Port)), [])

    def test_top_bundle_nets(self) -> None:
        top = board()
        nets = list(decompose(top, Net))
        for name, outer, inner, members in (
            ("rgmii", top.rgmii, top.phy.rgmii, 12),
            ("reset_n", top.reset_n, top.phy.reset_n, 1),
            ("int_n", top.int_n, top.phy.int_n, 1),
        ):
            with self.subTest(port=name):
                found = [n for n in nets if outer in list(n)]
                self.assertEqual(len(found), 1)
                self.assertEqual(len(list(found[0])), 2)
                self.assertIn(inner, list(found[0]))
                self.assertEqual(len(leaves(outer)), members)
        mdi = [n for n in nets if top.phy.mdi in list(n)]
        self.assertEqual(len(mdi), 1)
        ports = list(mdi[0])
        self.assertEqual(len(ports), 2)
        self.assertTrue(all(isinstance(p, MDI1000BaseT) for p in ports))
        self.assertEqual(len(leaves(top.phy.mdi)), 8)

    def test_members_reach_pins(self) -> None:
        top = board()
        conn = Connectivity(top)
        u1 = top.phy.u1
        rgmii, miim = top.rgmii, top.miim
        expected: list[tuple[Port, Port]] = [
            *zip(rgmii.TX.data, u1.TXD, strict=True),
            (rgmii.TX.clk, u1.GTX_CLK),
            (rgmii.TX.ctl, u1.TX_EN),
            *zip(rgmii.RX.data, u1.RXD, strict=True),
            (rgmii.RX.clk, u1.RX_CLK),
            (rgmii.RX.ctl, u1.RX_DV),
            (miim.mdc, u1.MDC),
            (miim.mdio, u1.MDIO),
            (top.reset_n, u1.RESET_N),
            (top.int_n, u1.INT_N),
        ]
        line = (
            (u1.TXRXP_A, u1.TXRXM_A),
            (u1.TXRXP_B, u1.TXRXM_B),
            (u1.TXRXP_C, u1.TXRXM_C),
            (u1.TXRXP_D, u1.TXRXM_D),
        )
        for pair, (p, n) in zip(top.phy.mdi.TP, line, strict=True):
            expected += [(pair.p, p), (pair.n, n)]
        self.assertEqual(len(expected), 12 + 2 + 2 + 8)
        signal_pins = [pin for _, pin in expected]
        for member, pin in expected:
            with self.subTest(pin=str(pin)):
                reached = [q for q in signal_pins if conn.connected(member, q)]
                self.assertEqual(reached, [pin])


class TestPhyApplicationCircuit(TestCase):
    def test_every_supply_pin_decoupled(self) -> None:
        """One 100 nF per supply pin; 10 uF beside a DVDDH pin on 3.3 V and,
        after ANLAN206 Figure 8, on AVDDL pin 9, DVDDL and AVDDL_PLL on 1.2 V.
        """
        phy = board().phy
        conn = Connectivity(phy)
        u1 = phy.u1
        caps = list(extract(phy, Capacitor))
        # Each rail's pins, and the pin groups that carry one 10 uF each.
        rails = {
            "3V3": (
                phy.vdd_3v3.Vp,
                [*u1.AVDDH, *u1.DVDDH],
                {"DVDDH": list(u1.DVDDH)},
            ),
            "1V2": (
                phy.q_ldo.d,
                [*u1.AVDDL, u1.AVDDL_PLL, *u1.DVDDL],
                {
                    "AVDDL pin 9": [u1.AVDDL[1]],
                    "AVDDL_PLL": [u1.AVDDL_PLL],
                    "DVDDL": list(u1.DVDDL),
                },
            ),
        }
        self.assertEqual(sum(len(pins) for _, pins, _ in rails.values()), 14)
        for name, (rail, pins, bulk_groups) in rails.items():
            bulk_on: list[str] = []
            for pin in pins:
                self.assertTrue(conn.connected(rail, pin))
                on_pin = [c for c in caps if pin in short_trace_partner(phy, c.p1)]
                hf = [c for c in on_pin if abs(farads(c) - 100e-9) < 1e-12]
                with self.subTest(rail=name, pin=str(pin)):
                    self.assertEqual(len(hf), 1)
                for c in on_pin:
                    self.assertTrue(conn.connected(c.p2, phy.vdd_3v3.Vn))
                for c in on_pin:
                    if abs(farads(c) - 10e-6) < 1e-9:
                        group = [
                            g for g, members in bulk_groups.items() if pin in members
                        ]
                        bulk_on += group or [str(pin)]
            with self.subTest(rail=name, bulk=True):
                self.assertEqual(sorted(bulk_on), sorted(bulk_groups))

    def test_crystal_load_caps(self) -> None:
        phy = board().phy
        conn = Connectivity(phy)
        self.assertEqual(phy.y1.mpn, "X1E0000210132")
        self.assertTrue(conn.connected(phy.y1.OSC1, phy.u1.XI))
        self.assertTrue(conn.connected(phy.y1.OSC2, phy.u1.XO))
        caps = list(extract(phy, Capacitor))
        for pin in (phy.y1.OSC1, phy.y1.OSC2):
            on_pin = [c for c in caps if pin in short_trace_partner(phy, c.p1)]
            with self.subTest(pin=str(pin)):
                self.assertEqual(len(on_pin), 1)
                self.assertAlmostEqual(farads(on_pin[0]), 8.2e-12, delta=1e-15)
                self.assertTrue(conn.connected(on_pin[0].p2, phy.vdd_3v3.Vn))

    def test_iset_bias(self) -> None:
        """Table 2-1, pin 48: ISET takes 12.1 kOhm to ground."""
        phy = board().phy
        conn = Connectivity(phy)
        u1 = phy.u1
        resistors = list(extract(phy, Resistor))
        iset = touching(conn, resistors, u1.ISET)
        self.assertEqual(len(iset), 1)
        self.assertAlmostEqual(ohms(iset[0]), 12.1e3)
        gnd = phy.vdd_3v3.Vn
        self.assertTrue(conn.connected(other_pad(conn, iset[0], u1.ISET), gnd))

    def test_core_ldo(self) -> None:
        """Table 2-1 pin 43 and Section 11.0: LDO_O drives the gate of a
        P-channel MOSFET with its source on 3.3 V and its drain on the 1.2 V
        core. ANLAN206 Figure 8: 100 kOhm gate to source, 10 uF on the source,
        10 uF, 1 uF and 100 nF on the drain, and a short trace from the drain
        to AVDDL pin 4. Every short trace lands on a pin of the MOSFET itself,
        not on its circuit's ports: the drain capacitors and the sense trace on
        the drain tab (pin 4), the source capacitor on the source pin.
        """
        phy = board().phy
        conn = Connectivity(phy)
        u1 = phy.u1
        fets = list(extract(phy, NTF6P02T3G))
        self.assertEqual(fets, [phy.q_ldo])
        q = phy.q_ldo
        tab, source = q.mosfet.D[1], q.mosfet.S
        v3v3, gnd = phy.vdd_3v3.Vp, phy.vdd_3v3.Vn
        self.assertFalse(u1.LDO_O.is_no_connect())
        self.assertTrue(conn.connected(q.g, u1.LDO_O))
        self.assertTrue(conn.connected(q.s, v3v3))
        self.assertFalse(conn.connected(q.g, v3v3))
        self.assertFalse(conn.connected(q.d, v3v3))
        for pin in (*u1.AVDDL, u1.AVDDL_PLL, *u1.DVDDL):
            self.assertTrue(conn.connected(q.d, pin))
        self.assertTrue(conn.connected(tab, q.d))
        self.assertTrue(conn.connected(source, q.s))
        self.assertIn(tab, short_trace_partner(phy, u1.AVDDL[0]))
        self.assertNotIn(q.mosfet.D[0], short_trace_partner(phy, u1.AVDDL[0]))
        self.assertNotIn(tab, short_trace_partner(phy, u1.AVDDL[1]))
        for port in (q.d, q.s, q.g):
            self.assertEqual(short_trace_partner(phy, port), [])

        gate = touching(conn, extract(phy, Resistor), q.g)
        self.assertEqual(len(gate), 1)
        self.assertAlmostEqual(ohms(gate[0]), 100e3)
        self.assertTrue(conn.connected(other_pad(conn, gate[0], q.g), q.s))

        caps = list(extract(phy, Capacitor))
        for terminal, values in (
            (source, [10e-6]),
            (tab, [100e-9, 1e-6, 10e-6]),
        ):
            on = [c for c in caps if terminal in short_trace_partner(phy, c.p1)]
            with self.subTest(terminal=str(terminal)):
                self.assertEqual(
                    sorted(round(farads(c), 12) for c in on),
                    [round(v, 12) for v in values],
                )
                for c in on:
                    self.assertTrue(conn.connected(c.p2, gnd))


class TestHostLines(TestCase):
    def test_reset_n_reaches_host_with_power_on_network(self) -> None:
        """Section 8.0, Figure 8-1: RESET_N takes 10 kOhm to DVDDH and 10 uF
        to ground, and the board brings it out to the host.
        """
        top = board()
        conn = Connectivity(top)
        phy = top.phy
        u1 = phy.u1
        self.assertTrue(conn.connected(top.reset_n, u1.RESET_N))
        reset_r = touching(conn, extract(top, Resistor), u1.RESET_N)
        reset_c = touching(conn, extract(top, Capacitor), u1.RESET_N)
        self.assertEqual([ohms(r) for r in reset_r], [10e3])
        self.assertEqual(len(reset_c), 1)
        self.assertAlmostEqual(farads(reset_c[0]), 10e-6, delta=1e-12)
        v3v3, gnd = top.reg_3v3.vout.Vp, top.vin.Vn
        self.assertTrue(conn.connected(other_pad(conn, reset_r[0], u1.RESET_N), v3v3))
        self.assertTrue(conn.connected(other_pad(conn, reset_c[0], u1.RESET_N), gnd))

    def test_int_n_reaches_host_with_pull_up(self) -> None:
        """Table 2-1, pin 38: INT_N takes a 1.0 to 4.7 kOhm pull-up to DVDDH,
        and the board brings it out to the host.
        """
        top = board()
        conn = Connectivity(top)
        u1 = top.phy.u1
        self.assertFalse(u1.INT_N.is_no_connect())
        self.assertTrue(conn.connected(top.int_n, u1.INT_N))
        self.assertEqual(touching(conn, extract(top, Capacitor), u1.INT_N), [])
        pull = touching(conn, extract(top, Resistor), u1.INT_N)
        self.assertEqual(len(pull), 1)
        self.assertGreaterEqual(ohms(pull[0]), 1.0e3)
        self.assertLessEqual(ohms(pull[0]), 4.7e3)
        far = other_pad(conn, pull[0], u1.INT_N)
        self.assertTrue(conn.connected(far, top.reg_3v3.vout.Vp))
        self.assertFalse(conn.connected(top.int_n, top.reset_n))


class TestStraps(TestCase):
    def check(self, straps: StrapConfig, levels: dict[Strap, bool]) -> None:
        phy = board(straps).phy
        conn = Connectivity(phy)
        u1 = phy.u1
        resistors = list(extract(phy, Resistor))
        # Nine strap resistors, two LED series resistors, ISET, the reset and
        # interrupt pull-ups, and the LDO MOSFET's gate resistor.
        self.assertEqual(len(resistors), 15)
        for strap, (pin_number, port_of) in STRAP_PINS.items():
            with self.subTest(strap=strap.name):
                pin = port_of(u1)
                self.assertEqual(strap.value, pin_number)
                self.assertIs(
                    single_pad(u1.mappings[0], pin), u1.landpattern.p[pin_number]
                )
                on_pin = touching(conn, resistors, pin)
                self.assertEqual(len(on_pin), 1)
                r = on_pin[0]
                self.assertIs(r, phy.strap_resistor(strap))
                far = other_pad(conn, r, pin)
                if levels[strap]:
                    self.assertAlmostEqual(ohms(r), PULL_UP_OHMS)
                    self.assertTrue(conn.connected(far, phy.vdd_3v3.Vp))
                else:
                    self.assertAlmostEqual(ohms(r), PULL_DOWN_OHMS)
                    self.assertTrue(conn.connected(far, phy.vdd_3v3.Vn))

    def test_default_configuration(self) -> None:
        # PHY address 0, all RGMII modes advertised, no 125 MHz clock out,
        # single-LED mode.
        self.check(
            StrapConfig(),
            {
                Strap.PHYAD2: False,
                Strap.PHYAD1: False,
                Strap.PHYAD0: False,
                Strap.MODE3: True,
                Strap.MODE2: True,
                Strap.MODE1: True,
                Strap.MODE0: True,
                Strap.CLK125_EN: False,
                Strap.LED_MODE: True,
            },
        )

    def test_address_5_gigabit_full_duplex_only(self) -> None:
        # PHYAD[2:0] = 101 and MODE[3:0] = 1100 flip four straps of the default.
        self.check(
            StrapConfig(phy_address=5, mode=Mode.RGMII_1000_FULL),
            {
                Strap.PHYAD2: True,
                Strap.PHYAD1: False,
                Strap.PHYAD0: True,
                Strap.MODE3: True,
                Strap.MODE2: True,
                Strap.MODE1: False,
                Strap.MODE0: False,
                Strap.CLK125_EN: False,
                Strap.LED_MODE: True,
            },
        )

    def test_clock_output_and_tri_color_leds(self) -> None:
        self.check(
            StrapConfig(
                phy_address=2,
                mode=Mode.RGMII_ALL_EXCEPT_1000_HALF,
                clk125_output=True,
                led_mode=LedMode.TRI_COLOR_DUAL,
            ),
            {
                Strap.PHYAD2: False,
                Strap.PHYAD1: True,
                Strap.PHYAD0: False,
                Strap.MODE3: True,
                Strap.MODE2: True,
                Strap.MODE1: True,
                Strap.MODE0: False,
                Strap.CLK125_EN: True,
                Strap.LED_MODE: False,
            },
        )

    def check_leds(self, straps: StrapConfig, pull_up: bool) -> None:
        """Section 9.0, Figure 9-1: each LED's anode takes DVDDH through
        220 Ohm and its cathode sits on the LED pin, beside the pin's strap
        resistor, 10 kOhm to DVDDH or 1.0 kOhm to ground.
        """
        top = board(straps)
        conn = Connectivity(top)
        phy = top.phy
        u1 = phy.u1
        v3v3, gnd = phy.vdd_3v3.Vp, phy.vdd_3v3.Vn
        resistors = list(extract(phy, Resistor))
        for name, pin, jack_led, strap in (
            ("LED1", u1.LED1, top.jack.LED1, Strap.PHYAD0),
            ("LED2", u1.LED2, top.jack.LED2, Strap.PHYAD1),
        ):
            with self.subTest(led=name):
                self.assertEqual(straps.level(strap), pull_up)
                self.assertTrue(conn.connected(jack_led.c, pin))
                self.assertFalse(conn.connected(jack_led.a, pin))
                series = touching(conn, resistors, jack_led.a)
                self.assertEqual(len(series), 1)
                self.assertAlmostEqual(ohms(series[0]), LED_SERIES_OHMS)
                far = other_pad(conn, series[0], jack_led.a)
                self.assertTrue(conn.connected(far, v3v3))
                strap_r = phy.strap_resistor(strap)
                self.assertEqual(touching(conn, resistors, pin), [strap_r])
                if pull_up:
                    self.assertAlmostEqual(ohms(strap_r), PULL_UP_OHMS)
                    self.assertTrue(conn.connected(other_pad(conn, strap_r, pin), v3v3))
                else:
                    self.assertAlmostEqual(ohms(strap_r), PULL_DOWN_OHMS)
                    self.assertTrue(conn.connected(other_pad(conn, strap_r, pin), gnd))

    def test_leds_on_pulled_up_strap_pins(self) -> None:
        # PHY address 3 pulls up PHYAD1 (LED2) and PHYAD0 (LED1).
        self.check_leds(StrapConfig(phy_address=3), pull_up=True)

    def test_leds_on_pulled_down_strap_pins(self) -> None:
        # PHY address 0 pulls down PHYAD1 (LED2) and PHYAD0 (LED1).
        self.check_leds(StrapConfig(phy_address=0), pull_up=False)

    def test_invalid_configurations_fail_at_construction(self) -> None:
        with self.assertRaises(ValueError):
            StrapConfig(phy_address=8)
        with self.assertRaises(ValueError):
            StrapConfig(phy_address=-1)
        # 0101 is reserved in Table 2-2.
        with self.assertRaises(ValueError):
            Mode(0b0101)
        # A bare code or level, not the enum, is refused at construction.
        with self.assertRaises(TypeError):
            StrapConfig(mode=cast(Mode, 0b1111))
        with self.assertRaises(TypeError):
            StrapConfig(led_mode=cast(LedMode, 1))


class TestPlacement(TestCase):
    def test_jack_fixed_rest_floating(self) -> None:
        top = board()
        self.assertIsInstance(top.jack.transform, Placement)
        assert top.jack.transform is not None
        self.assertEqual(tuple(top.jack.transform.translation), (0.0, 12.0))
        for child in (top.phy, top.reg_3v3):
            with self.subTest(child=type(child).__name__):
                self.assertIsNone(child.transform)
        # Nothing inside the PHY circuit or the jack carries its own placement,
        # so each moves with its circuit.
        for circuit in (top.phy, top.jack):
            for part in extract(circuit, Component):
                with self.subTest(part=type(part).__name__):
                    self.assertIsNone(part.transform)


class TestPassives(TestCase):
    def test_every_passive_from_the_catalogue(self) -> None:
        top = board()
        parts: list[PassivePart] = [
            *extract(top, Resistor),
            *extract(top, Capacitor),
            *extract(top, Inductor),
        ]
        self.assertGreater(len(parts), 0)
        for part in parts:
            with self.subTest(part=str(part.mpn)):
                self.assertFalse(str(part.mpn).startswith("IDEAL-"))
                self.assertEqual(
                    part.part.identity.provider, "csv:example-passives.csv"
                )

    def test_minimum_package_holds(self) -> None:
        top = board()
        for kind, cases in ((Resistor, RESISTOR_CASES), (Capacitor, CAPACITOR_CASES)):
            for part in extract(top, kind):
                with self.subTest(part=str(part.mpn)):
                    self.assertIn(part.part.identity.attributes["case"], cases)


class TestTranslation(TestCase):
    def test_no_connect_marks_only_on_component_pins(self) -> None:
        """The build accepts a no-connect mark only on a component pin; on a
        circuit's port it stops with "Cannot set a module pin as no-connect".
        Translation does not check this, so this test does. Every marked port
        is checked, a whole bundle included: ``pins`` holds every port of every
        component, its bundles and their members alike.
        """
        top = board()
        pins = {
            id(pin) for part in extract(top, Component) for pin in extract(part, Port)
        }
        marked = [
            (str(trace.path), port)
            for trace, port in visit(top, Port, transform=None)
            if port.is_no_connect()
        ]
        self.assertGreater(len(marked), 0)
        for name, port in marked:
            with self.subTest(port=name):
                self.assertTrue(
                    id(port) in pins,
                    f"{name} is marked no-connect but is not a component pin",
                )

    def test_design_translates(self) -> None:
        """The whole design translates, as a build does before anything else.

        The structural tests above inspect the Python objects; a ShortTrace to a
        net's port or a child stored twice passes them and fails translation.
        """
        packaged = package_design(JS2TestDesign())
        self.assertIsNotNone(packaged.v1)

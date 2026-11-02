"""KSZ9031RNX gigabit Ethernet PHY application circuit.

Section, table and figure numbers cite the KSZ9031RNX data sheet, DS00002117K,
linked from :attr:`~jitxexamples.components.ethernet_phys.microchip_KSZ9031RNX.KSZ9031RNX.datasheet`.
ANLAN206 is the Microchip application note Section 11.0 cites as the LDO
controller's design reference; its Figure 8 is the KSZ9031RNX circuit.

The circuit runs the PHY from one 3.3 V rail, for AVDDH and DVDDH. The PHY's
on-chip LDO controller makes the 1.2 V core (AVDDL, AVDDL_PLL and DVDDL) from it
through an external P-channel MOSFET. The circuit holds the parts the PHY needs
to run: that MOSFET and its capacitors, the 25 MHz crystal and its load
capacitors, the strap-in resistors, the LED series resistors, the ISET bias
resistor, the power-on reset network, the interrupt pull-up and the supply
decoupling. Its boundary is typed: one ``Power`` port for the 3.3 V rail,
``RGMII`` and ``MIIM`` toward the MAC, ``MDI1000BaseT`` toward the magnetics,
one ``Polarized`` port per LED output for the LED it drives, and one port each
for RESET_N and INT_N toward the host.

The MDIO pull-up is not here: it belongs to the circuit that composes the bus.
The exposed pad's thermal vias (V and EV of Figures 13-3, 13-6 and 13-9) are
left to layout.
"""

from jitx import Circuit, Net
from jitx.common import Polarized, Power
from jitx.net import Port, ShortTrace
from jitx.units import V, kohm, mW, nF, ohm, pct, uF
from jitxlib.parts import AtLeast, AtMost, Capacitor, Resistor
from jitxlib.protocols.ethernet.mdi.mdi1000base_t import MDI1000BaseT
from jitxlib.protocols.ethernet.mii.miim import MIIM
from jitxlib.protocols.ethernet.mii.rgmii import RGMII

from jitxexamples.components.crystals.seiko_epson_TSX_3225 import TSX3225
from jitxexamples.components.ethernet_phys.microchip_KSZ9031RNX import KSZ9031RNX
from jitxexamples.components.fets_p_ch.NTF6P02T3G import NTF6P02T3G

from .straps import DEFAULT_STRAPS, Strap, StrapConfig

# Section 9.0, Figure 9-1, and the text after it: a strap pin is pulled up with
# 10 kOhm to DVDDH or pulled down with 1.0 kOhm to ground. The data sheet gives
# these values for the LED strap pins only; Section 2.0 gives none for the
# RGMII and CLK125_NDO strap pins, so the circuit uses the same pair on all nine.
STRAP_PULL_UP = 10 * kohm
STRAP_PULL_DOWN = 1.0 * kohm
# Section 9.0, Figure 9-1: each LED is fed from DVDDH through 220 Ohm.
LED_SERIES = 220 * ohm


class KSZ9031RNXCircuit(Circuit):
    """KSZ9031RNX with its core LDO, crystal, straps, bias, reset, interrupt
    pull-up and decoupling.

    Args:
        straps: the configuration the strap resistors latch at power-up.
    """

    vdd_3v3 = Power()
    """3.3 V supply for AVDDH and DVDDH (I/O at 3.3 V), and the source of the
    1.2 V core."""
    rgmii = RGMII()
    """RGMII toward the MAC. ``TX`` carries MAC to PHY, ``RX`` PHY to MAC."""
    miim = MIIM()
    """Management interface. MDIO needs a pull-up in the composing circuit."""
    mdi = MDI1000BaseT()
    """The four line pairs, A to D, toward the magnetics."""
    led1 = Polarized()
    """LED driven by LED1 (pin 17): wire it anode to ``a``, cathode to ``c``."""
    led2 = Polarized()
    """LED driven by LED2 (pin 15): wire it anode to ``a``, cathode to ``c``."""
    reset_n = Port()
    """RESET_N (pin 42), active low, toward the host. The circuit holds the
    power-on RC network; the host may pull the line low to reset the PHY and
    otherwise leaves it undriven, as an open-drain output does."""
    int_n = Port()
    """INT_N (pin 38), active low by default, toward the host. The circuit holds
    its pull-up."""

    def __init__(self, straps: StrapConfig = DEFAULT_STRAPS) -> None:
        self.straps = straps
        self.u1 = KSZ9031RNX()
        u1 = self.u1

        self.GND = Net([self.vdd_3v3.Vn, u1.VSS, u1.P_GND], name="GND")
        self.V3V3 = Net([self.vdd_3v3.Vp, *u1.AVDDH, *u1.DVDDH], name="V3V3")
        self.V1V2 = Net([*u1.AVDDL, u1.AVDDL_PLL, *u1.DVDDL], name="V1V2")

        # Each net is stored in one field named for it, the name it exports
        # when no parent circuit joins it under another name.
        self.TXD = [m + p for m, p in zip(self.rgmii.TX.data, u1.TXD, strict=True)]
        self.GTX_CLK = self.rgmii.TX.clk + u1.GTX_CLK
        self.TX_EN = self.rgmii.TX.ctl + u1.TX_EN
        self.RXD = [m + p for m, p in zip(self.rgmii.RX.data, u1.RXD, strict=True)]
        self.RX_CLK = self.rgmii.RX.clk + u1.RX_CLK
        self.RX_DV = self.rgmii.RX.ctl + u1.RX_DV
        self.MDC = self.miim.mdc + u1.MDC
        self.MDIO = self.miim.mdio + u1.MDIO
        self.CLK125_NDO = Net([u1.CLK125_NDO])
        line_pins = (
            (u1.TXRXP_A, u1.TXRXM_A),
            (u1.TXRXP_B, u1.TXRXM_B),
            (u1.TXRXP_C, u1.TXRXM_C),
            (u1.TXRXP_D, u1.TXRXM_D),
        )
        self.TXRX_P = [
            pair.p + p for pair, (p, _) in zip(self.mdi.TP, line_pins, strict=True)
        ]
        self.TXRX_N = [
            pair.n + n for pair, (_, n) in zip(self.mdi.TP, line_pins, strict=True)
        ]

        self._add_core_ldo()
        self._add_decoupling()
        self._add_crystal()
        self._add_leds()
        self._add_straps()
        self._add_bias_and_reset()
        self._add_interrupt()

    def _add_core_ldo(self) -> None:
        """The 1.2 V core from 3.3 V through the on-chip LDO controller.

        Table 2-1, pin 43: LDO_O drives the gate of a P-channel MOSFET whose
        source is on 3.3 V and whose drain makes the 1.2 V core. Section 11.0
        asks for a P-channel part rated 500 mA continuous whose VGS at 500 mA,
        from a 3.3 V source, is -1.2 to -1.5 V, in saturation rather than near
        threshold. ANLAN206 names the part on Microchip's evaluation board, the
        FDT434P. When this part was chosen, Digi-Key listed the FDT434P as
        obsolete and named the onsemi NTF6P02T3G as its substitute; this
        circuit uses the NTF6P02T3G.

        The NTF6P02T3G is rated -20 V and -10 A continuous at 25 C. Its
        threshold at 250 uA is -0.7 V typical, -0.4 V and -1.0 V at its limits,
        and its magnitude falls 2.6 mV per C as the part heats. Here VDS is
        about -2.1 V (3.3 V - 1.2 V). At that VDS the typical on-region curve
        (Figure 1, 25 C) carries 500 mA at about -1.18 V, read from the plot:
        a typical part sits at the edge of Section 11.0's window. The data
        sheet gives no curve for other parts. Moving the typical curve by the
        threshold's spread and its temperature coefficient gives estimates of
        about -1.48 V at 25 C and -1.55 V at 0 C for a part at the -1.0 V
        limit, and about -0.88 V at 25 C and -0.62 V at a 125 C junction for
        a part at the -0.4 V limit. So the part does not meet Section 11.0's window
        across its spread: a part near the -1.0 V limit lands inside it at
        25 C, a typical part at its edge, and a part near the -0.4 V limit
        outside it. In every case VDS is beyond VGS - VGS(th), so the part
        runs in saturation.

        Table 6-11: LDO_O swings 0.85 to 2.8 V with AVDDH at 3.3 V, a VGS of
        -2.45 to -0.5 V. At 500 mA the estimated VGS stays inside that range:
        the largest, about -1.55 V, is about 0.9 V inside the -2.45 V limit,
        and the smallest, about -0.62 V, about 0.12 V inside the -0.5 V end.
        That covers 500 mA only; light load is below. Table 6-11 gives the
        range at AVDDH 3.3 V only. At 3.465 V (3.3 V + 5%) the same gate
        voltages give a VGS 0.165 V stronger, so if LDO_O still tops out at
        2.8 V its weakest drive is about -0.67 V, and the margins at the weak
        end shrink: the -0.62 V estimate would fall outside the range.

        ANLAN206 asks for about 250 mA at 1.9 V VDS with a VGS below 2.5 V.
        The typical curve gives 250 mA at about -1.10 V; by the same estimate
        a part at the -1.0 V limit needs about -1.40 V at 25 C and -1.47 V at
        0 C (read at -2.1 V VDS; the part is in saturation at either VDS).
        ANLAN206's Figure 6 shows the FDT434P's working point at a -VGS below
        1.5 V, which these estimates also stay under, by about 0.03 V at 0 C.
        ANLAN206 also asks for an input capacitance below 2 nF; Ciss is
        1200 pF at most (900 pF typical).

        Light load is not verified, and the risk is an estimate. Table 3-12's
        lightest core loads are 1.0 mA in software power-down and 7.1 mA at
        10BASE-T link-up. At LDO_O's weakest drive, a 2.8 V gate (Table 6-11),
        VGS is -0.5 V, and about -0.67 V from a 3.465 V AVDDH. A part at the
        -0.4 V threshold limit already passes 250 uA at -0.4 V. Its threshold
        magnitude falls as the part heats, by 2.6 mV per C, which makes
        turn-off harder, not easier. So at -0.5 V it may not turn off far
        enough to hold the drain to those loads, and the core could rise
        above 1.2 V. The data sheet gives no curve at these currents, and the
        KSZ9031RNX data sheet does not say whether LDO_O can pull the gate
        above 2.8 V. The FDT434P on Microchip's evaluation board has the same
        -0.4 V minimum threshold (onsemi FDT434P data sheet).

        ANLAN206 Figure 8 gives the rest: 100 kOhm from gate to source, which
        it adds to avoid a large inrush current from 3.3 V as the LDO powers up;
        10 uF on the source; 10 uF, 1 uF and 100 nF on the drain; and a short
        trace from the drain to AVDDL pin 4, which the controller senses as its
        feedback (the 10 uF bulk capacitor sits on AVDDL pin 9). The drain
        capacitors and the sense trace land on the drain tab, pin 4 of the
        MOSFET, and the source capacitor on its source pin. Figure 8 feeds
        DVDDL and AVDDL_PLL through ferrite beads. The example catalogue holds
        no ferrite bead, so this circuit puts all three on one 1.2 V net.
        AVDDL takes no bead in the figure: one there would degrade the LDO's
        load regulation.

        The MOSFET dissipates the core's whole drop. At Table 3-12's highest
        core current, 221 mA at 1000BASE-T full duplex, that is
        (3.3 V - 1.2 V) x 221 mA = 0.46 W. ANLAN206 sizes for typical current
        plus 20% at the supply extremes, 0.62 W. The NTF6P02T3G's steady-state
        junction-to-ambient resistance is 71.4 C/W on FR4 with a 1 inch drain
        pad, 1.127 square inches of copper (Note 2). At 0.46 W that is a 33 C
        rise: a 103 C junction at 70 C ambient, the top of the commercial
        range, and 118 C at 85 C, the top of the industrial range. At 0.62 W
        it is a 44 C rise: 114 C at 70 C and 129 C at 85 C. ANLAN206 asks for
        at most 90 C/W in the commercial range and 65 C/W in the industrial
        range, limits that put the junction near 125 C at 0.62 W. The
        NTF6P02T3G meets the commercial limit and not the industrial one: at
        0.62 W and 85 C its junction is about 4 C above 125 C, and 21 C under
        its own 150 C maximum. Its 160 C/W rating on the minimum recommended
        pad (Note 3) still assumes 0.412 square inches of copper, about 16
        times the 16.6 square millimetres of this footprint's own pads, so the
        layout must give the drain tab the Note 2 copper.

        The core comes from AVDDH, so it cannot lead 3.3 V at power-up, which
        meets Figure 7-5, Note 1 by construction. Figure 7-5, Note 3
        recommends the reverse at power-down, the 1.2 V core down before the
        3.3 V supplies. This circuit does not meet Note 3: the core is made
        from 3.3 V, so it stays up until 3.3 V has fallen. That is how the
        LDO controller scheme of Section 11.0 and ANLAN206 behaves.
        """
        u1 = self.u1
        self.q_ldo = NTF6P02T3G()
        q = self.q_ldo
        # The tab, the drain pad that carries the rated copper.
        drain_tab = q.mosfet.D[1]
        self.r_ldo_gate = Resistor(resistance=100 * kohm)
        self.LDO_GATE = u1.LDO_O + q.g + self.r_ldo_gate.p1
        self.V3V3 += Net([q.s, self.r_ldo_gate.p2])
        self.V1V2 += q.d
        self.c_ldo_in = _bulk_cap()
        self.c_ldo_out = [
            _bulk_cap(),
            Capacitor(
                capacitance=1 * uF,
                rated_voltage_dc=AtLeast(10 * V),
                temperature_coefficient_code="X5R",
            ),
            _hf_cap(),
        ]
        self.ldo_st = [
            ShortTrace(self.c_ldo_in.p1, q.mosfet.S),
            *(ShortTrace(c.p1, drain_tab) for c in self.c_ldo_out),
            ShortTrace(drain_tab, u1.AVDDL[0]),
        ]
        self.GND += Net([self.c_ldo_in.p2, *(c.p2 for c in self.c_ldo_out)])

    def _add_decoupling(self) -> None:
        """Supply decoupling.

        The data sheet gives no decoupling recommendation; ANLAN206 Figure 8
        places one 100 nF per 1.2 V supply pin (9 pins) and 10 uF on AVDDL
        pin 9, DVDDL and AVDDL_PLL. The 3.3 V pins follow the same pattern as
        a decision: one 100 nF X7R per supply pin (5 pins, so 14 across both
        rails), and one 10 uF X5R bulk capacitor beside a DVDDH pin. Each is
        rated at least 10 V, derated for DC bias on rails of 3.3 V and below.
        """
        u1 = self.u1
        pins_3v3 = [*u1.AVDDH, *u1.DVDDH]
        pins_1v2 = [*u1.AVDDL, u1.AVDDL_PLL, *u1.DVDDL]
        self.c_3v3 = [_hf_cap() for _ in pins_3v3]
        self.c_1v2 = [_hf_cap() for _ in pins_1v2]
        self.c_3v3_st = [
            ShortTrace(c.p1, pin) for c, pin in zip(self.c_3v3, pins_3v3, strict=True)
        ]
        self.c_1v2_st = [
            ShortTrace(c.p1, pin) for c, pin in zip(self.c_1v2, pins_1v2, strict=True)
        ]
        bulk_pins = [u1.DVDDH[0], u1.AVDDL[1], u1.DVDDL[0], u1.AVDDL_PLL]
        self.c_bulk = [_bulk_cap() for _ in bulk_pins]
        self.bulk_st = [
            ShortTrace(c.p1, pin) for c, pin in zip(self.c_bulk, bulk_pins, strict=True)
        ]
        self.GND += Net(
            [
                *(c.p2 for c in self.c_3v3),
                *(c.p2 for c in self.c_1v2),
                *(c.p2 for c in self.c_bulk),
            ]
        )

    def _add_crystal(self) -> None:
        """25 MHz crystal on XI and XO.

        Table 10-1 asks for 25 MHz, at most +/-50 ppm, about 40 Ohm series
        resistance. X1E0000210132 is +/-10 ppm at +25 C and +/-10 ppm over
        -20 to 75 C, 40 Ohm, with a 9 pF load: ``add_load_caps`` sizes the two
        C0G load capacitors and joins each to its crystal pin through a
        ``ShortTrace``. Figure 10-1 shows 22 pF without naming the crystal's
        load; the PHY does not constrain the load capacitance (Table 10-1).
        """
        self.y1 = TSX3225(
            frequency=25e6,
            load_capacitance=9e-12,
            frequency_tolerance=10e-6,
            frequency_stability=10e-6,
            temperature_range=(-20, 75),
        )
        self.XI = self.y1.OSC1 + self.u1.XI
        self.XO = self.y1.OSC2 + self.u1.XO
        self.GND += Net([self.y1.GND0, self.y1.GND1])
        # The capacitors belong to this circuit already; storing them on self
        # as well would register them twice.
        self.y1.add_load_caps(self.GND)

    def _add_straps(self) -> None:
        """One strap resistor per Table 2-2 strap pin, on the pin's own net.

        Each resistor joins the net that already carries its pin, so the net
        keeps its signal name.

        A pull-down sits on a pin that drives once the PHY is out of reset (an
        RGMII receive output, an LED output or CLK125_NDO), so it dissipates
        up to (3.3 V)^2 / 1.0 kOhm = 10.9 mW while the pin is high. A pull-up
        dissipates a tenth of that. Neither value needs a tolerance: each only
        sets a logic level.
        """
        nets = self._strap_nets()
        self.r_strap = [_strap_resistor(self.straps.level(s)) for s in Strap]
        for strap, r in zip(Strap, self.r_strap, strict=True):
            nets[strap] += r.p1
            if self.straps.level(strap):
                self.V3V3 += r.p2
            else:
                self.GND += r.p2

    def _add_leds(self) -> None:
        """LED drive on the LED1/PHYAD0 and LED2/PHYAD1 strap pins.

        Section 9.0, Figure 9-1 gives one reference circuit per strap level at
        3.3 V DVDDH. In both the LED's anode takes DVDDH through 220 Ohm and
        its cathode sits on the LED pin, which sinks current to light it
        (Table 3-9: L is on). The levels differ only in the strap resistor on
        the pin, 10 kOhm to DVDDH or 1.0 kOhm to ground, which ``_add_straps``
        places from the configuration. With a pull-down, the LED and 220 Ohm
        also feed the pin while reset holds it undriven, and the strap reads
        low only under the 1.3 V input-low maximum of Table 6-3. Figure 9-1 is
        Microchip's circuit for this case; the jack's drawing gives the LED's
        forward voltage only at 20 mA, so the pin voltage at the 1 mA or so
        that flows here is not computed.
        """
        u1 = self.u1
        self.r_led = [Resistor(resistance=LED_SERIES) for _ in range(2)]
        self.LED1_A = self.led1.a + self.r_led[0].p1
        self.LED2_A = self.led2.a + self.r_led[1].p1
        self.LED1 = self.led1.c + u1.LED1
        self.LED2 = self.led2.c + u1.LED2
        for r in self.r_led:
            self.V3V3 += r.p2

    def _add_bias_and_reset(self) -> None:
        """ISET bias resistor and power-on reset.

        Table 2-1, pin 48: ISET takes a 12.1 kOhm 1% resistor to ground.

        Section 8.0, Figure 8-1: RESET_N gets 10 kOhm to DVDDH and 10 uF to
        ground. Table 7-4 asks for supplies stable at least 10 ms before reset
        de-asserts (tSR). RESET_N's internal pull-up, 13 to 31 kOhm at 3.3 V
        (Table 6-6), sits in parallel with the 10 kOhm, giving 5.7 to
        7.6 kOhm. The 10 uF part the example catalogue resolves,
        CC0402MRX5R6BB106 (X5R, 0402, +/-20%), keeps about 42% of its value at
        3.3 V in its maker's simulated DC-bias curve, at least 3.3 uF. RESET_N
        reaches the 2.0 V input-high level (Table 6-3) after at least 17 ms,
        using that 3.3 V capacitance; the capacitor loses less below 2 V, which
        makes it longer, about 35 to 70 ms on the maker's curve. In the
        composed board, 3.3 V settles at most 2.9 ms after it starts to rise,
        the maximum of its regulator's soft start, and the core follows it
        through the LDO controller, for which the data sheet gives no start-up
        time. Reset de-asserts at least 14 ms after 3.3 V settles, so tSR holds
        while the core settles within 4 ms of it, and neither part takes a
        tolerance filter. The figure's 1N4148 diode is
        left off, because the reference library has no small-signal diode.
        Without it the capacitor discharges only through the resistors when
        DVDDH falls. A supply cycle that keeps Table 7-4's 150 ms off-to-on
        time (tPC) still resets the PHY; a shorter dip may not pull RESET_N low
        again, which the diode's fast discharge would. The reset capacitor is RC timing, not supply
        decoupling.

        The host joins RESET_N through ``reset_n``. Figure 8-2 puts a 1N4148
        in series from the host's reset output, so that output can only pull
        the line low and the RC network still sets power-on timing. With no
        small-signal diode in the library the host connects directly, so it
        drives the line open-drain: low to reset, released otherwise. Figure
        7-5, Note 2: after reset de-asserts, the host waits at least 100 us
        before MIIM access.
        """
        u1 = self.u1
        self.r_iset = Resistor(resistance=12.1 * kohm, tolerance=AtMost(1 * pct))
        self.ISET = u1.ISET + self.r_iset.p1
        self.GND += self.r_iset.p2

        self.r_reset = Resistor(resistance=10 * kohm)
        self.c_reset = Capacitor(
            capacitance=10 * uF,
            rated_voltage_dc=AtLeast(10 * V),
            temperature_coefficient_code="X5R",
        )
        self.RESET_N = self.reset_n + u1.RESET_N + self.r_reset.p1 + self.c_reset.p1
        self.V3V3 += self.r_reset.p2
        self.GND += self.c_reset.p2

    def _add_interrupt(self) -> None:
        """INT_N pull-up.

        Table 2-1, pin 38: for its interrupt function, active low by default,
        INT_N takes a 1.0 to 4.7 kOhm pull-up to DVDDH. The circuit uses
        4.7 kOhm and brings the pin out to the host as ``int_n``.
        """
        self.r_int = Resistor(resistance=4.7 * kohm)
        self.INT_N = self.int_n + self.u1.INT_N + self.r_int.p1
        self.V3V3 += self.r_int.p2

    def strap_pins(self) -> dict[Strap, Port]:
        """The KSZ9031RNX pin carrying each strap, per Table 2-2."""
        u1 = self.u1
        return {
            Strap.PHYAD2: u1.RX_CLK,
            Strap.PHYAD1: u1.LED2,
            Strap.PHYAD0: u1.LED1,
            Strap.MODE3: u1.RXD[3],
            Strap.MODE2: u1.RXD[2],
            Strap.MODE1: u1.RXD[1],
            Strap.MODE0: u1.RXD[0],
            Strap.CLK125_EN: u1.RX_DV,
            Strap.LED_MODE: u1.CLK125_NDO,
        }

    def _strap_nets(self) -> dict[Strap, Net[Port]]:
        """The stored net carrying each strap pin of ``strap_pins``."""
        nets = [
            self.RX_CLK,
            self.LED1,
            self.LED2,
            *self.RXD,
            self.RX_DV,
            self.CLK125_NDO,
        ]
        return {
            strap: next(n for n in nets if pin in list(n))
            for strap, pin in self.strap_pins().items()
        }

    def strap_resistor(self, strap: Strap) -> Resistor:
        """The resistor setting ``strap``."""
        return self.r_strap[list(Strap).index(strap)]


def _hf_cap() -> Capacitor:
    return Capacitor(
        capacitance=100 * nF,
        rated_voltage_dc=AtLeast(10 * V),
        temperature_coefficient_code="X7R",
    )


def _bulk_cap() -> Capacitor:
    return Capacitor(
        capacitance=10 * uF,
        rated_voltage_dc=AtLeast(10 * V),
        temperature_coefficient_code="X5R",
    )


def _strap_resistor(pull_up: bool) -> Resistor:
    if pull_up:
        return Resistor(resistance=STRAP_PULL_UP)
    return Resistor(resistance=STRAP_PULL_DOWN, max_power=AtLeast(11 * mW))

"""JS2 reference solution: a gigabit Ethernet PHY board.

A 12 V input feeds one buck regulator, which makes 3.3 V for the PHY's AVDDH and
DVDDH. The PHY's on-chip LDO controller makes its 1.2 V core from that rail
through an external P-channel MOSFET, inside the PHY circuit. The PHY's line
pairs run to an RJ45 jack with integrated magnetics, and its LED outputs drive
the jack's two LEDs. RGMII, MIIM, RESET_N and INT_N are boundary ports of the
top circuit, left for the MAC and host the board plugs into.

Build (runtime required)::

    jitx design build jitxexamples.jumpstart_kits.js2_circuits.main.EthernetPhyDesign
"""

from jitx import Circuit, Net
from jitx.common import Power
from jitx.net import Port, ShortTrace
from jitx.sample import SampleDesign
from jitx.units import V, kohm, nF
from jitxlib.parts import (
    AtLeast,
    Capacitor,
    CapacitorQuery,
    Resistor,
    ResistorQuery,
)
from jitxlib.protocols.ethernet.mdi.mdi1000base_t import MDI1000BaseT
from jitxlib.protocols.ethernet.mii.miim import MIIM
from jitxlib.protocols.ethernet.mii.rgmii import RGMII

from jitxexamples.components.connectors.bel_fuse_0826_1G1T_23_F import (
    Bel_0826_1G1T_23_F,
)
from jitxexamples.components.power_switchmode.texas_instruments_TPS62933DRLR import (
    TPS62933DRLRCircuit,
)

from .phy import KSZ9031RNXCircuit
from .straps import DEFAULT_STRAPS, StrapConfig

INPUT_VOLTAGE = 12.0
"""Nominal input in volts. The regulator sizes its inductor from it."""

REGULATOR_CURRENT = 1.82
"""Output current in amperes the regulator is sized for. The board draws about
330 mA from 3.3 V (KSZ9031RNX Table 3-12, 1000BASE-T full duplex: AVDDH
66.3 mA, DVDDH 41.5 mA, and the 221 mA core through the LDO). The regulator
sizes its inductor for 40% ripple at this current and asks for one rated at
least this current. At 1.81 A and below it asks for 3.3 uH or more: the example
catalogue holds no 6.8 or 15 uH part, and its 3.3, 4.7 and 10 uH parts are
rated 0.7 A or less. At 1.82 A it asks for 2.2 uH, which the catalogue holds
rated 3.3 A. 1.82 A is the smallest value, to 0.01 A, that resolves."""


class EthernetPhyBoard(Circuit):
    """A regulator, the PHY application circuit and an RJ45 jack with
    magnetics, wired through their boundary ports.

    No SI constraints and no routing structures are applied to this board
    yet: the RGMII signals and the four MDI pairs route unconstrained.
    JumpStart 4 covers both.

    Args:
        straps: the PHY strap configuration.
        input_voltage: nominal input in volts.
    """

    vin = Power()
    """Board input, nominally 12 V."""
    rgmii = RGMII()
    """PHY RGMII, toward the MAC."""
    miim = MIIM()
    """PHY management interface, toward the MAC."""
    reset_n = Port()
    """PHY RESET_N, active low, toward the host. The board holds the power-on
    RC network; the host pulls the line low to reset the PHY and otherwise
    leaves it undriven (open drain)."""
    int_n = Port()
    """PHY INT_N, active low, toward the host. The board holds its pull-up."""

    def __init__(
        self,
        straps: StrapConfig = DEFAULT_STRAPS,
        input_voltage: float = INPUT_VOLTAGE,
    ) -> None:
        self.reg_3v3 = TPS62933DRLRCircuit(
            output_voltage=3.3,
            input_voltage=input_voltage,
            output_current=REGULATOR_CURRENT,
        ).at(floating=True)
        self.phy = KSZ9031RNXCircuit(straps).at(floating=True)
        # The jack sits at a fixed position; everything else floats.
        self.jack = Bel_0826_1G1T_23_F().at(0.0, 12.0)

        # The core comes from 3.3 V inside the PHY circuit, so it cannot lead
        # 3.3 V at power-up: Figure 7-5, Note 1 of the KSZ9031RNX data sheet
        # holds by construction. Note 3, the core down before 3.3 V at
        # power-down, does not: the core stays up until 3.3 V has fallen.
        self.VIN = Net([self.vin.Vp, self.reg_3v3.vin.Vp], name="VIN")

        # Each net is stored in one field named for it, the name it exports.
        self.RGMII = self.rgmii + self.phy.rgmii
        self.MDC = self.miim.mdc + self.phy.miim.mdc
        self.MDI = self.phy.mdi + self.jack.require(MDI1000BaseT)
        self.RESET_N = self.reset_n + self.phy.reset_n
        self.INT_N = self.int_n + self.phy.int_n

        # A bus pull-up belongs to the circuit composing the bus. Table 2-1 of
        # the KSZ9031RNX data sheet, pin 37: MDIO takes a 1.0 to 4.7 kOhm
        # pull-up to DVDDH.
        self.r_mdio = Resistor(resistance=4.7 * kohm)
        self.MDIO = self.miim.mdio + self.phy.miim.mdio + self.r_mdio.p1

        # KSZ9031RNX data sheet Section 12.0: the four device-side center taps
        # must be kept separate, each through its own 0.1 uF common-mode
        # capacitor to ground, because the pairs' common-mode voltages can
        # differ with the speed mode. The jack, from Table 12-2, brings out
        # each tap, and each capacitor sits on a ShortTrace to its tap.
        self.c_ct = [
            Capacitor(
                capacitance=100 * nF,
                rated_voltage_dc=AtLeast(10 * V),
                temperature_coefficient_code="X7R",
            )
            for _ in range(4)
        ]
        self.CT = {
            n: ShortTrace(c.p1, self.jack.CT[n])
            for n, c in enumerate(self.c_ct, start=1)
        }

        # Section 9.0, Figure 9-1: LED1 and LED2 drive the jack's LEDs while
        # keeping their strap resistors; the PHY circuit holds the 220 Ohm
        # series resistors.
        self.LED1 = self.phy.led1 + self.jack.LED1
        self.LED2 = self.phy.led2 + self.jack.LED2

        # The jack's SHIELD port stays off every board net: it is left for the
        # enclosure design, which sets the chassis connection. The jack holds
        # Figure 12-1's cable-side termination inside (its drawing shows four
        # 75 Ohm resistors and 1000 pF, 2 kV to the shield), so it has no
        # cable-side pins and the board needs no 2 kV capacitor. A no-connect
        # mark applies only to a component pin, not to a circuit's port.

        self.V3V3 = Net(
            [self.reg_3v3.vout.Vp, self.phy.vdd_3v3.Vp, self.r_mdio.p2], name="V3V3"
        )
        self.GND = Net(
            [
                self.vin.Vn,
                self.reg_3v3.vin.Vn,
                self.reg_3v3.vout.Vn,
                self.phy.vdd_3v3.Vn,
                *(c.p2 for c in self.c_ct),
            ],
            name="GND",
        )


class EthernetPhyDesign(SampleDesign):
    """The board as a design.

    Every passive the kit adds leaves its package open; the design states the
    smallest package the assembler places, 0402, once for every query.

    Args:
        straps: the PHY strap configuration.
        input_voltage: nominal input in volts.
    """

    resistor_defaults = ResistorQuery(case=["0402", "0603", "0805", "1206"])
    capacitor_defaults = CapacitorQuery(case=["0402", "0603", "0805", "1206", "1210"])

    def __init__(
        self,
        straps: StrapConfig = DEFAULT_STRAPS,
        input_voltage: float = INPUT_VOLTAGE,
    ) -> None:
        self.circuit = EthernetPhyBoard(straps, input_voltage)

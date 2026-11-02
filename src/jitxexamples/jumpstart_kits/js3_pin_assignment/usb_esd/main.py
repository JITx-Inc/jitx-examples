"""JS3 Part 2 reference solution: USB 2.0 from an RP2040 through a PUSB3FR4 ESD
array to a USB Type-C receptacle, with the ESD channels left to pin assignment.

Parts and sources:

- Raspberry Pi RP2040 (``jitxexamples.components.mcus.raspberry_pi_RP2040``),
  the MCU side of the link, wired as a USB device, with its 27 ohm series
  resistors: Raspberry Pi Ltd, "RP2040 Datasheet", build-date 2025-02-20,
  section 1.4.2 and Table 620. Its USB controller supports a Full Speed
  device (12 Mbit/s), section 1.4.2.
- Nexperia PUSB3FR4 (``esd.ProtectedPair``): Nexperia, "PUSB3FR4 ESD protection
  for ultra high-speed interfaces", Product data sheet, 12 July 2018. The
  channel freedom and its citations are in ``esd``.
- Molex 2012670005 USB Type-C receptacle
  (``jitxexamples.components.connectors.molex_2012670005``).
- USB Type-C wiring for a USB 2.0 device: Microchip AN1953, "Introduction to
  USB Type-C", DS00001953A, 2015,
  https://ww1.microchip.com/downloads/en/Appnotes/00001953A.pdf. Section 1.3.1:
  the two D+ and D- contacts (A6/B6, A7/B7) are shorted on the board. Section
  3.2 and Table 7: a device (UFP) pulls CC1 and CC2 down with 5.1 kOhm, at most
  10% tolerance for Type-C current advertising.

The SI constraint is ``DiffPairConstraint`` with the USB 2.0 limits from
``jitxlib.protocols.usb.USB.v2``: skew 0 +/- 3.75 ps, insertion loss 12 dB.
They are jitxlib-standard's generic values (``usb.py`` cites no source), were
not checked against the USB 2.0 specification, and the skew limit is far tighter
than a Full Speed link needs (one bit is 83 ns), so the proofs show the constraint binding,
not compliance. The routing structure is JS1's ``HDISubstrate.DRS_100``, the
stackup's only differential structure: USB 2.0 asks for 90 ohm +/- 15%
(``USB.v2.impedance``, 76.5 to 103.5 ohm) and 100 ohm falls inside it. The
constraint runs from the RP2040's own USB pins to the connector's A6/A7 pins,
so it covers the series resistors (each with a 0 s, 0 dB ``BridgingPinModel``,
a modelling assumption) and the ESD channels. The B6/B7 contacts sit on the
same nets as a stub, outside the measured path.

Out of scope: power entry. ``VBUS`` and ``3V3`` are named nets with no
regulator between them; the kit is about the data path.
"""

from jitx.circuit import Circuit
from jitx.common import Power
from jitx.design import Design
from jitx.net import DiffPair, Net
from jitx.si import DiffPairConstraint, ReferencePlanes
from jitx.units import ohm
from jitxlib.parts import Resistor
from jitxlib.protocols.usb import USB

from jitxexamples.components.connectors.molex_2012670005 import USBTypeCComponent
from jitxexamples.components.mcus.raspberry_pi_RP2040 import RP2040
from jitxexamples.jumpstart_kits.js1_stackup_components.hdi_stackup.board import (
    HDIBoard,
    HDISubstrate,
)

from .esd import ProtectedPair

CC_PULLDOWN = 5.1e3 * ohm
"""AN1953 Table 7: Rd, 5.1 kOhm to GND on each CC pin of a device."""
CC_PULLDOWN_TOLERANCE = 0.01
"""The 1% grade, inside AN1953 Table 7's 10% limit for Type-C current
advertising."""


class UsbEsdCircuit(Circuit):
    """RP2040 USB through one PUSB3FR4 channel pair to a Type-C receptacle."""

    power = Power()
    """3V3 supply for the RP2040."""

    def __init__(self) -> None:
        self.mcu = RP2040()
        self.esd = ProtectedPair()
        self.conn = USBTypeCComponent()

        self.gnd = Net(
            [
                self.power.Vn,
                self.mcu.power.Vn,
                self.esd.gnd,
                *self.conn.GND,
                self.conn.SHIELD,
            ],
            name="GND",
        )
        self.v3v3 = Net([self.power.Vp, self.mcu.power.Vp], name="3V3")
        self.vbus = Net(list(self.conn.VBUS), name="VBUS")

        self.cc1_rd = Resistor(resistance=CC_PULLDOWN, tolerance=CC_PULLDOWN_TOLERANCE)
        self.cc2_rd = Resistor(resistance=CC_PULLDOWN, tolerance=CC_PULLDOWN_TOLERANCE)
        self.CC1 = self.conn.CC1 + self.cc1_rd.p1
        self.CC2 = self.conn.CC2 + self.cc2_rd.p1
        self.gnd += self.cc1_rd.p2
        self.gnd += self.cc2_rd.p2

        # The ESD pair is pin-assigned: net it, keep it local, store the nets.
        pair = self.esd.require(DiffPair)
        self.USB_DP = Net([self.mcu.usb.data.p, pair.p, self.conn.D0.p, self.conn.D1.p])
        self.USB_DM = Net([self.mcu.usb.data.n, pair.n, self.conn.D0.n, self.conn.D1.n])

        self.usb_constraint = DiffPairConstraint(
            skew=USB.v2.skew, loss=USB.v2.loss, structure=HDISubstrate.DRS_100
        )
        with ReferencePlanes(self.gnd):
            self.usb_constraint.constrain(self.mcu.mcu.USB, self.conn.D0)


class UsbEsdDesign(Design):
    """The shipping design: no placement, no routes, so the ESD channels stay
    free for whoever routes the board."""

    board = HDIBoard()
    substrate = HDISubstrate()
    circuit = UsbEsdCircuit()

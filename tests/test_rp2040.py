from jitx import current
from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxlib.protocols.serial import I2C, SPI, UART
from jitxlib.protocols.usb import USB

from jitxexamples.components.connectors import molex_2012670005
from jitxexamples.components.mcus import raspberry_pi_RP2040


class RP2040Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        mcu = raspberry_pi_RP2040.RP2040()

        def __init__(self):
            i1 = self.mcu.require(I2C)
            i2 = self.mcu.require(I2C)
            self.net = i1 + i2
            s1 = self.mcu.require(SPI(cs=True))
            s2 = self.mcu.require(SPI(cs=True))
            self.snet = s1 + s2

            # Test UART loopback - require two UART interfaces and connect them
            u1 = self.mcu.require(UART)
            u2 = self.mcu.require(UART)
            assert u1.rx and u1.tx
            assert u2.rx and u2.tx
            self.uart_loopback_nets = [
                u1.tx + u2.rx,  # Connect UART1 TX to UART2 RX
                u1.rx + u2.tx,  # Connect UART1 RX to UART2 TX
            ]

            self.usb = molex_2012670005.USBC_HighSpeed_Iface()

            self.usb_constraint = USB.v2.Constraint(
                current.substrate.differential_routing_structure(100.0)
            )
            with self.usb_constraint.constrain_topology(self.mcu.usb, self.usb.USB) as (
                src,
                dst,
            ):
                self += src >> dst


class TestRP2040(TestCase):
    def test_rp2040(self):
        design = RP2040Design()
        self.assertIsInstance(design.circuit.mcu, raspberry_pi_RP2040.RP2040)  # type: ignore

from collections.abc import Sequence

from jitx.container import inline
from jitx.inspect import extract
from jitx.landpattern import Pad
from jitx.net import Net, Port
from jitx.test import TestCase
from jitx.circuit import Circuit
from tests.parts import PartsTestDesign
from jitxlib.parts import CapacitorQuery, ResistorQuery

from jitxexamples.components.sensors.stmicroelectronics_LIS3DHTR import (
    Device as LIS3DHTRDevice,
)


class LIS3DHTRDesign(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        accelerometer = LIS3DHTRDevice()


class TestLIS3DHTR(TestCase):
    def test_lis3dhtr(self):
        design = LIS3DHTRDesign()
        self.assertIsInstance(design.circuit.accelerometer, LIS3DHTRDevice)  # type: ignore

    def test_serial_pins(self) -> None:
        """Each serial line lands on the pad the LIS3DH data sheet gives it.

        LIS3DH data sheet DocID17530 Rev 2, Table 2 (page 9): pin 4 is SCL/SPC,
        pin 6 is SDA/SDI (data into the sensor), pin 7 is SDO/SA0 (data out of
        it), pin 8 is CS.
        """
        circuit = LIS3DHTRDesign().circuit.accelerometer
        assert isinstance(circuit, LIS3DHTRDevice)
        acc = circuit.acc
        spi = circuit.spi
        assert spi.copi is not None and spi.cipo is not None and spi.cs is not None
        acc_ports = list(extract(acc, Port))

        def pads_on(member: Port) -> list[Pad]:
            pads: list[Pad] = []
            for net in extract(circuit, Net):
                ports = list(net)
                if member not in ports:
                    continue
                for port in ports:
                    if port in acc_ports:
                        mapped = acc.mappings[0][port]
                        pads.extend(
                            mapped if isinstance(mapped, Sequence) else [mapped]
                        )
            return pads

        p = acc.landpattern.p
        expected = [
            ("i2c.scl", circuit.i2c.scl, p[4]),
            ("spi.sck", spi.sck, p[4]),
            ("i2c.sda", circuit.i2c.sda, p[6]),
            ("spi.copi", spi.copi, p[6]),
            ("spi.cipo", spi.cipo, p[7]),
            ("spi.cs", spi.cs, p[8]),
        ]
        for name, member, pad in expected:
            with self.subTest(member=name):
                self.assertEqual(pads_on(member), [pad])

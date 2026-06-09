from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.sensors.stmicroelectronics_LIS3DHTR import (
    Device as LIS3DHTRDevice,
)


class LIS3DHTRDesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        accelerometer = LIS3DHTRDevice()


class TestLIS3DHTR(TestCase):
    def test_lis3dhtr(self):
        design = LIS3DHTRDesign()
        self.assertIsInstance(design.circuit.accelerometer, LIS3DHTRDevice)  # type: ignore

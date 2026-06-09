from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.logic.texas_instruments_SN74HC14PWR import (
    Device as SN74HC14PWRDevice,
)


class SN74HC14PWRDesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        inverter = SN74HC14PWRDevice()


class TestSN74HC14PWR(TestCase):
    def test_sn74hc14pwr(self):
        design = SN74HC14PWRDesign()
        self.assertIsInstance(design.circuit.inverter, SN74HC14PWRDevice)  # type: ignore

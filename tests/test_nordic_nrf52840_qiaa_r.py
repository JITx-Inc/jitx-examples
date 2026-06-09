from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, InductorQuery, ResistorQuery

from jitxexamples.components.mcus.nordic_NRF52840_QIAA_R import (
    Device as NRF52840_QIAA_RDevice,
)


class NRF52840_QIAA_RDesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])
    _inductor_defaults = InductorQuery(case=["0402", "0603"])

    @inline
    class circuit(Circuit):
        mcu = NRF52840_QIAA_RDevice()


class TestNRF52840(TestCase):
    def test_nrf52840(self):
        design = NRF52840_QIAA_RDesign()
        self.assertIsInstance(design.circuit.mcu, NRF52840_QIAA_RDevice)  # type: ignore

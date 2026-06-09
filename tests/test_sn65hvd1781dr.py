from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.transceivers.texas_instruments_SN65HVD1781DR import (
    Device as SN65HVD1781DRDevice,
)


class SN65HVD1781DRDesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        rs485_transceiver = SN65HVD1781DRDevice()


class TestSN65HVD1781DR(TestCase):
    def test_sn65hvd1781dr(self):
        design = SN65HVD1781DRDesign()
        self.assertIsInstance(design.circuit.rs485_transceiver, SN65HVD1781DRDevice)  # type: ignore

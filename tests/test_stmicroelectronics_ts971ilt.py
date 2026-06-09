from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.opamps.stmicroelectronics_TS971ILT import (
    Device as TS971ILTDevice,
)


class TS971ILTDesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        opamp = TS971ILTDevice()


class TestTS971ILT(TestCase):
    def test_ts971ilt(self):
        design = TS971ILTDesign()
        self.assertIsInstance(design.circuit.opamp, TS971ILTDevice)  # type: ignore

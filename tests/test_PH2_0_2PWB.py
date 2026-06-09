from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.battery_managers.PH2_0_2PWB import PH2_0_2PWB


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = PH2_0_2PWB()


class TestPH202PWB(TestCase):
    def test_ph2_0_2pwb(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, PH2_0_2PWB)  # type: ignore

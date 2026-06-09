from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.leds.KT_0603W import KT_0603W


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = KT_0603W()


class TestKT0603W(TestCase):
    def test_kt_0603w(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, KT_0603W)  # type: ignore

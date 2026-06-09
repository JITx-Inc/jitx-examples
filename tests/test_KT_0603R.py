from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.leds.KT_0603R import KT_0603R


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = KT_0603R()


class TestKT0603R(TestCase):
    def test_kt_0603r(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, KT_0603R)  # type: ignore

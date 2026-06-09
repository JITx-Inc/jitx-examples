from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.fets_p_ch.AO6409 import AO6409


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = AO6409()


class TestAO6409(TestCase):
    def test_ao6409(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, AO6409)  # type: ignore

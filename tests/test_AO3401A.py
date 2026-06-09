from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.fets_p_ch.AO3401A import AO3401A


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = AO3401A()


class TestAO3401A(TestCase):
    def test_ao3401a(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, AO3401A)  # type: ignore

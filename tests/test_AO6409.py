from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from tests.parts import PartsTestDesign
from jitxlib.parts import CapacitorQuery, ResistorQuery
from jitxexamples.components.fets_p_ch.AO6409 import AO6409


class Design(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = AO6409()


class TestAO6409(TestCase):
    def test_ao6409(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, AO6409)  # type: ignore

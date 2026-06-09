from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.fets_n_ch.BSS138 import BSS138


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = BSS138()


class TestBSS138(TestCase):
    def test_bss138(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, BSS138)  # type: ignore

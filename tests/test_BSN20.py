from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.fets_n_ch.BSN20 import BSN20


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = BSN20()


class TestBSN20(TestCase):
    def test_bsn20(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, BSN20)  # type: ignore

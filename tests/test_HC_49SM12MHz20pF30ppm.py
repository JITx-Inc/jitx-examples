from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.crystals.HC_49SM12MHz20pF30ppm import HC_49SM12MHz20pF30ppm


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = HC_49SM12MHz20pF30ppm()


class TestHC49SM(TestCase):
    def test_hc49sm(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, HC_49SM12MHz20pF30ppm)  # type: ignore

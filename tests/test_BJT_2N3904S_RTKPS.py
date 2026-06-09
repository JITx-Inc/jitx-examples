from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.bjts.BJT_2N3904S_RTKPS import BJT_2N3904S_RTKPS


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = BJT_2N3904S_RTKPS()


class TestBJT2N3904S(TestCase):
    def test_bjt_2n3904s(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, BJT_2N3904S_RTKPS)  # type: ignore

from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.digital_isolators.PUSB3FR4 import PUSB3FR4


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = PUSB3FR4()


class TestPUSB3FR4(TestCase):
    def test_pusb3fr4(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, PUSB3FR4)  # type: ignore

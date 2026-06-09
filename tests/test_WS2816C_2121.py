from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.leds.WS2816C_2121 import WS2816C_2121


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = WS2816C_2121()


class TestWS2816C2121(TestCase):
    def test_ws2816c_2121(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, WS2816C_2121)  # type: ignore

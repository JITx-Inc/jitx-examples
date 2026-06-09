from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.switches.MK_12C02_G025 import MK_12C02_G025


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = MK_12C02_G025()


class TestMK12C02(TestCase):
    def test_mk_12c02(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, MK_12C02_G025)  # type: ignore

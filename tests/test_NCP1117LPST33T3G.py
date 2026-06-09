from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.power_linear_regulators.NCP1117LPST33T3G import (
    NCP1117LPST33T3G,
)


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = NCP1117LPST33T3G()


class TestNCP1117(TestCase):
    def test_ncp1117(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, NCP1117LPST33T3G)  # type: ignore

from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from tests.parts import PartsTestDesign
from jitxlib.parts import CapacitorQuery, ResistorQuery
from jitxexamples.components.power_linear_regulators.AP2125K_2_8TRG1 import (
    AP2125K_2_8TRG1,
)


class Design(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = AP2125K_2_8TRG1()


class TestAP2125K(TestCase):
    def test_ap2125k(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, AP2125K_2_8TRG1)  # type: ignore

from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from tests.parts import PartsTestDesign
from jitxlib.parts import CapacitorQuery, ResistorQuery
from jitxexamples.components.passives.RK09K1130AP5 import RK09K1130AP5


class Design(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = RK09K1130AP5()


class TestRK09K1130AP5(TestCase):
    def test_rk09k1130ap5(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, RK09K1130AP5)  # type: ignore

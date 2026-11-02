from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from tests.parts import PartsTestDesign
from jitxlib.parts import CapacitorQuery, ResistorQuery
from jitxexamples.components.buttons.PTS810SJM250SMTRLFS import PTS810SJM250SMTRLFS


class Design(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = PTS810SJM250SMTRLFS()


class TestPTS810SJM(TestCase):
    def test_pts810sjm(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, PTS810SJM250SMTRLFS)  # type: ignore

from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from tests.parts import PartsTestDesign
from jitxlib.parts import CapacitorQuery, ResistorQuery
from jitxexamples.components.power_switches.high_side_switch import HighSideSwitch


class Design(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = HighSideSwitch()


class TestHighSideSwitch(TestCase):
    def test_high_side_switch(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, HighSideSwitch)  # type: ignore

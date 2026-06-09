from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.level_translators.logic_level_shifter import (
    LogicLevelShifter,
    I2CLevelShifter,
)


class Design1(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = LogicLevelShifter()


class Design2(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = I2CLevelShifter()


class TestLogicLevelShifter(TestCase):
    def test_logic_level_shifter(self):
        design = Design1()
        self.assertIsInstance(design.circuit.comp, LogicLevelShifter)  # type: ignore

    def test_i2c_level_shifter(self):
        design = Design2()
        self.assertIsInstance(design.circuit.comp, I2CLevelShifter)  # type: ignore

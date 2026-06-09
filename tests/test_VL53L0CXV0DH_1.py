from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.sensors_distance.VL53L0CXV0DH_1 import VL53L0CXV0DH_1


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = VL53L0CXV0DH_1()


class TestVL53L0CXV0DH1(TestCase):
    def test_vl53l0cxv0dh1(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, VL53L0CXV0DH_1)  # type: ignore

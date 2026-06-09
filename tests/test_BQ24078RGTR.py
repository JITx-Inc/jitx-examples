from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.battery_managers.BQ24078RGTR import BQ24078RGTR


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = BQ24078RGTR()


class TestBQ24078RGTR(TestCase):
    def test_bq24078rgtr(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, BQ24078RGTR)  # type: ignore

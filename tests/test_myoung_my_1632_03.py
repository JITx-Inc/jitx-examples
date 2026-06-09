from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.connectors.myoung_MY_1632_03 import (
    Device as MY_1632_03Device,
)


class MY_1632_03Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        battery_connector = MY_1632_03Device()


class TestMY163203(TestCase):
    def test_my_1632_03(self):
        design = MY_1632_03Design()
        self.assertIsInstance(design.circuit.battery_connector, MY_1632_03Device)  # type: ignore

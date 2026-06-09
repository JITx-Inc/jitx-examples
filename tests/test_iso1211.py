from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.isolators.texas_instruments_ISO1211 import (
    Device as ISO1211Device,
)


class ISO1211Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        isolator_circuit = ISO1211Device()


class TestISO1211(TestCase):
    def test_iso1211(self):
        design = ISO1211Design()
        self.assertIsInstance(design.circuit.isolator_circuit, ISO1211Device)  # type: ignore

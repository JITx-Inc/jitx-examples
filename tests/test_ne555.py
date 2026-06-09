from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.timers.texas_instruments_NE555 import (
    Device as NE555Device,
)


class NE555Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        timer = NE555Device()


class TestNE555(TestCase):
    def test_ne555(self):
        design = NE555Design()
        self.assertIsInstance(design.circuit.timer, NE555Device)  # type: ignore

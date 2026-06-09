from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.microphones.allpower_AP3722AT import (
    Device as AP3722ATDevice,
)


class AP3722ATDesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        microphone = AP3722ATDevice()


class TestAP3722AT(TestCase):
    def test_ap3722at(self):
        design = AP3722ATDesign()
        self.assertIsInstance(design.circuit.microphone, AP3722ATDevice)  # type: ignore

from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign

from jitxexamples.components.crystals.yangxing_tech_X322512MSB4SI import (
    Device as X322512MSB4SIDevice,
)


class X322512MSB4SIDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        crystal = X322512MSB4SIDevice()


class TestX322512MSB4SI(TestCase):
    def test_x322512msb4si(self):
        design = X322512MSB4SIDesign()
        self.assertIsInstance(design.circuit.crystal, X322512MSB4SIDevice)  # type: ignore

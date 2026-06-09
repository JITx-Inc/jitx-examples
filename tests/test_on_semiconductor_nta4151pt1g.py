from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign

from jitxexamples.components.transistors.on_semiconductor_NTA4151PT1G import (
    Device as NTA4151PT1GDevice,
)


class NTA4151PT1GDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        mosfet = NTA4151PT1GDevice()


class TestNTA4151PT1G(TestCase):
    def test_nta4151pt1g(self):
        design = NTA4151PT1GDesign()
        self.assertIsInstance(design.circuit.mosfet, NTA4151PT1GDevice)  # type: ignore

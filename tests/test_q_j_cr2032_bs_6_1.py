from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign

from jitxexamples.components.connectors.q_j_CR2032_BS_6_1 import (
    Device as CR2032Device,
)


class CR2032Design(SampleDesign):
    @inline
    class circuit(Circuit):
        battery_holder = CR2032Device()


class TestCR2032BS61(TestCase):
    def test_cr2032_bs_6_1(self):
        design = CR2032Design()
        self.assertIsInstance(design.circuit.battery_holder, CR2032Device)  # type: ignore

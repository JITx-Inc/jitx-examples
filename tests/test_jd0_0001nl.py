from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign

from jitxexamples.components.connectors import pulse_electronics_JD0_0001NL


class JD0_0001NLDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        rj45 = pulse_electronics_JD0_0001NL.Device()


class TestLSF_SMT(TestCase):
    def test_lsf_smt(self):
        design = JD0_0001NLDesign()
        self.assertIsInstance(design.circuit.rj45, pulse_electronics_JD0_0001NL.Device)  # type: ignore

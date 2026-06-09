from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign

from jitxexamples.components.connectors import weidmuller_LSF_SMT


class LSF_SMTDesign(SampleDesign):
    @inline
    class circuit(Circuit):
        comps = [weidmuller_LSF_SMT.Device(i) for i in range(1, 11)]


class TestLSF_SMT(TestCase):
    def test_lsf_smt(self):
        design = LSF_SMTDesign()
        # type ignore here because the type checker requires a type-narrowing check
        self.assertIsInstance(design.circuit.comps[0], weidmuller_LSF_SMT.Device)  # type: ignore

from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign

from jitxexamples.components.diodes_tvs.littelfuse_SMBJ43CA import (
    Device as SMBJ43CADevice,
)


class SMBJ43CADesign(SampleDesign):
    @inline
    class circuit(Circuit):
        tvs_diode = SMBJ43CADevice()


class TestSMBJ43CA(TestCase):
    def test_smbj43ca(self):
        design = SMBJ43CADesign()
        self.assertIsInstance(design.circuit.tvs_diode, SMBJ43CADevice)  # type: ignore

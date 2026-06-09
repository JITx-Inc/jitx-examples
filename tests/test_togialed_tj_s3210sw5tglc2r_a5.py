from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign

from jitxexamples.components.leds.togialed_TJ_S3210SW5TGLC2R_A5 import (
    Device as TJ_S3210Device,
)


class TJ_S3210Design(SampleDesign):
    @inline
    class circuit(Circuit):
        led = TJ_S3210Device()


class TestTJS3210SW5TGLC2RA5(TestCase):
    def test_tj_s3210sw5tglc2r_a5(self):
        design = TJ_S3210Design()
        self.assertIsInstance(design.circuit.led, TJ_S3210Device)  # type: ignore

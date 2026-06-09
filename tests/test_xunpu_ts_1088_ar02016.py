from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign

from jitxexamples.components.buttons.xunpu_TS_1088_AR02016 import (
    Device as TS1088Device,
)


class TS1088Design(SampleDesign):
    @inline
    class circuit(Circuit):
        button = TS1088Device()


class TestTS1088AR02016(TestCase):
    def test_ts_1088_ar02016(self):
        design = TS1088Design()
        self.assertIsInstance(design.circuit.button, TS1088Device)  # type: ignore

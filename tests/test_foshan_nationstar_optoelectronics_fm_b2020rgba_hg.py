from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.leds.foshan_nationstar_optoelectronics_FM_B2020RGBA_HG import (
    Device as FM_B2020RGBA_HGDevice,
)


class FM_B2020RGBA_HGDesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        rgb_led = FM_B2020RGBA_HGDevice()


class TestFMB2020RGBAHG(TestCase):
    def test_fm_b2020rgba_hg(self):
        design = FM_B2020RGBA_HGDesign()
        self.assertIsInstance(design.circuit.rgb_led, FM_B2020RGBA_HGDevice)  # type: ignore

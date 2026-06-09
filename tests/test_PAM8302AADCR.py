from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.audio_amps.PAM8302AADCR import PAM8302AADCR


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = PAM8302AADCR()


class TestPAM8302AADCR(TestCase):
    def test_pam8302aadcr(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, PAM8302AADCR)  # type: ignore

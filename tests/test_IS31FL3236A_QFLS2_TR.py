from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.led_drivers.IS31FL3236A_QFLS2_TR import (
    IS31FL3236A_QFLS2_TR,
)


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = IS31FL3236A_QFLS2_TR()


class TestIS31FL3236A(TestCase):
    def test_is31fl3236a(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, IS31FL3236A_QFLS2_TR)  # type: ignore

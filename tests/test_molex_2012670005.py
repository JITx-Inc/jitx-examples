from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.connectors.molex_2012670005 import (
    Device as USBTypeCDevice,
)


class USBTypeCDesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        usb_connector = USBTypeCDevice()


class TestMolex2012670005(TestCase):
    def test_molex_2012670005(self):
        design = USBTypeCDesign()
        self.assertIsInstance(design.circuit.usb_connector, USBTypeCDevice)  # type: ignore

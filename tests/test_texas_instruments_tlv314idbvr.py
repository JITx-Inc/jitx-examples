from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.opamps.texas_instruments_TLV314IDBVR import (
    Device as TLV314IDBVRDevice,
)


class TLV314IDBVRDesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        opamp = TLV314IDBVRDevice()


class TestTLV314IDBVR(TestCase):
    def test_tlv314idbvr(self):
        design = TLV314IDBVRDesign()
        self.assertIsInstance(design.circuit.opamp, TLV314IDBVRDevice)  # type: ignore

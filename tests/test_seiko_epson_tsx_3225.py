from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.transistors.seiko_epson_TSX_3225_32_0000MF10Z_W6 import (
    Device as TSX3225Device,
)


class TSX3225Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        crystal = TSX3225Device()


class TestTSX3225(TestCase):
    def test_tsx3225(self):
        design = TSX3225Design()
        self.assertIsInstance(design.circuit.crystal, TSX3225Device)  # type: ignore

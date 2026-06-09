from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.flash.winbond_W25Q128JVSIQ import (
    Device as W25Q128Device,
)


class W25Q128Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        flash_circuit = W25Q128Device()


class TestW25Q128(TestCase):
    def test_w25q128(self):
        design = W25Q128Design()
        self.assertIsInstance(design.circuit.flash_circuit, W25Q128Device)  # type: ignore

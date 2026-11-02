from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from tests.parts import PartsTestDesign
from jitxlib.parts import CapacitorQuery, ResistorQuery

from jitxexamples.components.transistors.changjiang_electronics_tech_BSS138 import (
    Device as BSS138Device,
)


class BSS138Design(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        mosfet = BSS138Device()


class TestBSS138CJ(TestCase):
    def test_bss138_cj(self):
        design = BSS138Design()
        self.assertIsInstance(design.circuit.mosfet, BSS138Device)  # type: ignore

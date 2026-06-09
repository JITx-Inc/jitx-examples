from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery
from jitxexamples.components.memories.W25Q128JVSIQTR import W25Q128JVSIQTR


class Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        comp = W25Q128JVSIQTR()


class TestW25Q128JVSIQTR(TestCase):
    def test_w25q128jvsiqtr(self):
        design = Design()
        self.assertIsInstance(design.circuit.comp, W25Q128JVSIQTR)  # type: ignore

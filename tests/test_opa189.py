from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.net import Net
from jitx.sample import SampleDesign
from jitxlib.parts import Capacitor, Resistor
from jitxlib.symbols.net_symbols.ground import GroundSymbol

from jitxexamples.components.opamps.texas_instruments_OPA189 import (
    Device as OPA189Device,
)


class OPA189Design(SampleDesign):
    @inline
    class circuit(Circuit):
        opamp = OPA189Device()

        r1 = Resistor(resistance=590)
        c2 = Capacitor(capacitance=39e-9).insert(opamp.INp, r1.p1)
        r3 = Resistor(resistance=499)
        r4 = Resistor(resistance=2940)
        c5 = Capacitor(capacitance=1e-9).insert(opamp.INn, opamp.OUT)

        gnd = Net([opamp.INp], name="GND", symbol=GroundSymbol())
        nets = [
            r1.p1 + r3.p1 + r4.p1,
            r3.p2 + opamp.INn,
            r4.p2 + opamp.OUT,
        ]


class TestOPA189(TestCase):
    def test_opa189(self):
        design = OPA189Design()
        self.assertIsInstance(design.circuit.opamp, OPA189Device)  # type: ignore

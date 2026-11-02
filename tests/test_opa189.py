from jitx.units import F, ohm
from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.net import Net
from tests.parts import PartsTestDesign
from jitxlib.parts import Capacitor, Resistor
from jitxlib.symbols.net_symbols.ground import GroundSymbol

from jitxexamples.components.opamps.texas_instruments_OPA189 import (
    Device as OPA189Device,
)


class OPA189Design(PartsTestDesign):
    @inline
    class circuit(Circuit):
        opamp = OPA189Device()

        r1 = Resistor(resistance=(590) * ohm)
        c2 = Capacitor(capacitance=(39e-9) * F)
        r3 = Resistor(resistance=(499) * ohm)
        r4 = Resistor(resistance=(2940) * ohm)
        c5 = Capacitor(capacitance=(1e-9) * F)

        gnd = Net([opamp.INp], name="GND", symbol=GroundSymbol())
        nets = [
            r1.p1 + r3.p1 + r4.p1,
            r3.p2 + opamp.INn,
            r4.p2 + opamp.OUT,
            opamp.INp + c2.p1,
            c2.p2 + r1.p1,
            opamp.INn + c5.p1,
            c5.p2 + opamp.OUT,
        ]


class TestOPA189(TestCase):
    def test_opa189(self):
        design = OPA189Design()
        self.assertIsInstance(design.circuit.opamp, OPA189Device)  # type: ignore

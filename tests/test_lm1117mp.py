from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.net import Net
from jitx.sample import SampleDesign
from jitxlib.symbols.net_symbols.ground import GroundSymbol
from jitxlib.parts import Capacitor, Resistor
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.power_linear_regulators.texas_instruments_LM1117MP import (
    Device as LM1117MPDevice,
)


class LM1117MPDesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        regulator = LM1117MPDevice()

        def __init__(self):
            # Basic voltage regulator circuit
            # Input capacitor for stability
            self.input_cap = Capacitor(capacitance=10e-6).insert(
                self.regulator.IN, self.regulator.ADJ, short_trace=True
            )

            # Output capacitor for stability (minimum 10µF as per datasheet)
            self.output_cap = Capacitor(capacitance=22e-6).insert(
                self.regulator.OUT, self.regulator.ADJ, short_trace=True
            )

            # Feedback resistors for adjustable output voltage
            # R1 = 1.24kΩ, R2 = 3.09kΩ for 3.3V output
            self.r1 = Resistor(resistance=1.24e3).insert(
                self.regulator.OUT, self.regulator.ADJ
            )
            self.r2 = Resistor(resistance=3.09e3).insert(
                self.regulator.ADJ,
                self.regulator.ADJ,  # Ground reference
            )

            self.GND = Net([self.regulator.ADJ], name="GND", symbol=GroundSymbol())


class TestLM1117MP(TestCase):
    def test_lm1117mp(self):
        design = LM1117MPDesign()
        self.assertIsInstance(design.circuit.regulator, LM1117MPDevice)  # type: ignore

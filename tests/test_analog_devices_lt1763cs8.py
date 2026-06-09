from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.power_linear_regulators.analog_devices_LT1763CS8 import (
    Device as LT1763LDODevice,
)


class LT1763LDODesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        # LT1763LDO requires input_voltage and output_voltage parameters
        ldo = LT1763LDODevice(input_voltage=5.0, output_voltage=3.3)


class TestLT1763CS8(TestCase):
    def test_lt1763cs8(self):
        design = LT1763LDODesign()
        self.assertIsInstance(design.circuit.ldo, LT1763LDODevice)  # type: ignore

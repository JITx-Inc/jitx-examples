import os

import pytest
from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.sample import SampleDesign

from jitxexamples.components.power_switchmode import texas_instruments_TPS62933DRLR
from jitxlib.parts import CapacitorQuery, InductorQuery, ResistorQuery


class TPS62933DRLRDesign(SampleDesign):
    _capacitor_defaults = CapacitorQuery()
    _resistor_defaults = ResistorQuery(case="0402")
    _inductor_defaults = InductorQuery()

    @inline
    class circuit(Circuit):
        comp = texas_instruments_TPS62933DRLR.Device()


class TestTPS62933DRLR(TestCase):
    def test_tps62933drlr(self):
        # Skip if using mock parts database - voltage divider solver requires real DB
        if os.environ.get("JITX_MOCK_PARTS_DB") == "1":
            pytest.skip("Voltage divider solver requires real parts database")

        design = TPS62933DRLRDesign()
        self.assertIsInstance(
            design.circuit.comp, texas_instruments_TPS62933DRLR.Device
        )  # type: ignore

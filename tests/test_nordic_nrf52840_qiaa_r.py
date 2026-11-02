from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from tests.parts import PartsTestDesign
from jitxlib.parts import CapacitorQuery, InductorQuery, ResistorQuery

from jitxexamples.components.mcus.nordic_NRF52840_QIAA_R import (
    NRF52840_QIAA_R,
)
from jitxexamples.components.mcus.nordic_NRF52840_QIAA_R import (
    Device as NRF52840_QIAA_RDevice,
)


class NRF52840_QIAA_RDesign(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])
    _inductor_defaults = InductorQuery(case=["0402", "0603"])

    @inline
    class circuit(Circuit):
        mcu = NRF52840_QIAA_RDevice()


class TestNRF52840(TestCase):
    def test_nrf52840(self):
        design = NRF52840_QIAA_RDesign()
        self.assertIsInstance(design.circuit.mcu, NRF52840_QIAA_RDevice)  # type: ignore


class SupplyDesign(PartsTestDesign):
    """One nRF52840 circuit in a design, so its passive queries resolve."""

    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])
    _inductor_defaults = InductorQuery(case=["0402", "0603"])

    def __init__(self, power_config: int) -> None:
        self.nrf = NRF52840_QIAA_R(power_config=power_config)
        self.circuit = self.nrf


class TestNRF52840Supply(TestCase):
    def test_every_vdd_ball_is_on_the_supply(self) -> None:
        for power_config in (5, 6):
            with self.subTest(power_config=power_config):
                nrf = SupplyDesign(power_config).nrf
                connected = nrf.VDD.connected
                self.assertEqual(len(nrf.mcu.VDD), 5)
                for pin in nrf.mcu.VDD:
                    self.assertTrue(any(pin is port for port in connected))

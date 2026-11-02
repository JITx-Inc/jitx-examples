from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.inspect import extract
from jitx.net import Net, Port
from jitx.toleranced import Toleranced
from jitx.units import ohm
from tests.parts import PartsTestDesign

from jitxexamples.components.power_switchmode import texas_instruments_TPS62933DRLR
from jitxlib.parts import CapacitorQuery, InductorQuery, ResistorQuery


class TPS62933DRLRDesign(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery()
    _resistor_defaults = ResistorQuery(case="0402")
    _inductor_defaults = InductorQuery()

    @inline
    class circuit(Circuit):
        comp = texas_instruments_TPS62933DRLR.Device()


class TPS62933DRLREnableDesign(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery()
    _resistor_defaults = ResistorQuery(case="0402")
    _inductor_defaults = InductorQuery()

    @inline
    class circuit(Circuit):
        comp = texas_instruments_TPS62933DRLR.TPS62933DRLRCircuit(enable_control=True)


def joined(root: Circuit, a: Port, b: Port) -> bool:
    """Whether one net under ``root`` holds both ports."""
    return any(
        any(p is a for p in net) and any(p is b for p in net)
        for net in extract(root, Net)
    )


class TestTPS62933DRLR(TestCase):
    def test_en_floats_by_default(self) -> None:
        comp = TPS62933DRLRDesign().circuit.comp
        assert isinstance(comp, texas_instruments_TPS62933DRLR.TPS62933DRLRCircuit)
        self.assertIsNone(comp.enable)
        self.assertTrue(comp.buck.EN.is_no_connect())

    def test_enable_control_brings_en_to_the_boundary(self) -> None:
        comp = TPS62933DRLREnableDesign().circuit.comp
        enable = comp.enable
        assert enable is not None
        self.assertFalse(comp.buck.EN.is_no_connect())
        self.assertTrue(joined(comp, enable, comp.buck.EN))

    def test_tps62933drlr(self):
        design = TPS62933DRLRDesign()
        self.assertIsInstance(
            design.circuit.comp, texas_instruments_TPS62933DRLR.Device
        )  # type: ignore

        divider = design.circuit.comp.fb_vdiv_ckt  # type: ignore
        high = float(divider.r_hi.value.to(ohm).magnitude)
        low = float(divider.r_lo.value.to(ohm).magnitude)
        self.assertEqual((high, low), (30900.0, 10000.0))
        self.assertAlmostEqual(3.3 * low / (high + low), divider.feedback_voltage)
        nets = [divider.IN, divider.FB, divider.LO]
        self.assertEqual([len(list(net)) for net in nets], [2, 3, 2])
        for net in nets:
            self.assertIsNotNone(net.typecheck())

    def test_feedback_divider_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            texas_instruments_TPS62933DRLR.FeedbackCircuit(
                Toleranced.exact(3.3), Toleranced.exact(0.8), 0.0
            )

    def test_feedback_divider_rejects_snapped_ratio_outside_range(self):
        with self.assertRaises(ValueError):
            texas_instruments_TPS62933DRLR.FeedbackCircuit(
                Toleranced.exact(3.3), Toleranced.exact(0.8), 0.8 / 10e3
            )

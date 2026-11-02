# `package_design` is private; jitx.test.TestCase supplies the instantiation
# context but exposes no public translate entry point (test_js1_hdi_stackup.py
# uses it for the same reason).
from jitx._translate.design import package_design
from jitx.units import F, V, ohm
from jitx.container import inline
from jitx.test import TestCase
from jitx.circuit import Circuit
from jitx.net import Net, ShortTrace
from tests.parts import PartsTestDesign
from jitxlib.symbols.net_symbols.ground import GroundSymbol
from jitxlib.parts import AtLeast, Capacitor, Resistor
from jitxlib.parts import CapacitorQuery, ResistorQuery

from jitxexamples.components.power_linear_regulators.texas_instruments_LM1117LD import (
    Device as LM1117LDDevice,
)


class LM1117LDDesign(PartsTestDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603", "0805"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        regulator = LM1117LDDevice()

        def __init__(self) -> None:
            # Adjustable regulator of Figure 9-1 in the LM1117 datasheet, set for
            # a 3.3 V output from a 5 V input. VOUT = 1.25 V * (1 + R2 / R1):
            # R1 = 121 ohm (as in Figure 9-1) and R2 = 200 ohm give 3.32 V. The
            # optional CADJ is omitted. Section 9.2.2.1.3 asks for an output
            # capacitor ESR of 0.3 to 22 ohm (tantalum); this repo's example
            # catalogue holds only ceramics, so the output capacitor here
            # resolves to a ceramic part far below that ESR. Use a tantalum part
            # in a real design.
            self.input_cap = Capacitor(
                capacitance=10e-6 * F, rated_voltage_dc=AtLeast(10 * V)
            )
            self.output_cap = Capacitor(
                capacitance=100e-6 * F, rated_voltage_dc=AtLeast(6.3 * V)
            )
            self.short_traces = [
                ShortTrace(self.regulator.IN, self.input_cap.p1),
                ShortTrace(self.regulator.OUT, self.output_cap.p1),
            ]

            # R1 from VOUT to ADJ, R2 from ADJ to ground.
            self.r1 = Resistor(resistance=121 * ohm)
            self.r2 = Resistor(resistance=200 * ohm)
            self.ADJ = Net([self.regulator.ADJ, self.r1.p2, self.r2.p1], name="ADJ")
            self.VOUT = Net([self.regulator.OUT, self.r1.p1], name="VOUT")
            self.GND = Net(
                [self.input_cap.p2, self.output_cap.p2, self.r2.p2],
                name="GND",
                symbol=GroundSymbol(),
            )

            self.regulator.NC.no_connect()


class TestLM1117LD(TestCase):
    def test_lm1117ld(self) -> None:
        design = LM1117LDDesign()
        self.assertIsInstance(design.circuit.regulator, LM1117LDDevice)  # type: ignore

    def test_adj_is_not_on_ground(self) -> None:
        packaged = package_design(LM1117LDDesign()).v1
        top = {m.id: m for m in packaged.modules}[packaged.module]
        (regulator,) = [i for i in top.instances if i.name == "regulator"]
        (component,) = [
            c for c in packaged.components if c.id == regulator.instantiable
        ]
        (adj,) = [p.id for p in component.ports if p.name == "ADJ"]
        (ground,) = [n for n in top.nets if n.name == "GND"]

        # The translated module lists each declared net on its own, and a net
        # built from another net (GND + port, ADJ + r2.p2) refers to that net by
        # its id. Each net's set holds its own id and its refs, so nets that
        # share a pin or name each other merge here into one electrical net.
        grounded = {(ground.id,)} | {tuple(r.path) for r in ground.refs}
        nets = [{(n.id,)} | {tuple(r.path) for r in n.refs} for n in top.nets]
        grew = True
        while grew:
            grew = False
            for refs in nets:
                if refs & grounded and not refs <= grounded:
                    grounded |= refs
                    grew = True

        self.assertNotIn(
            (regulator.id, adj), grounded, msg="regulator ADJ is on the GND net"
        )

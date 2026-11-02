"""
DDR4 example
============

A fictional controller drives a Micron MT40A1G16TB-062E:F over a single-rank
x16 DDR4 link, constrained with
:py:class:`~jitxexamples.protocols.memory.ddr4.DDR4Constraint`.

- Both parts expose their DDR4 pins as a
  :py:class:`~jitxexamples.protocols.memory.ddr4.DDR4` bundle, and one
  ordinary net joins the two bundles. There is one memory, so the
  address/command bus is point to point and there is no ``>>``.
- The constraint names the same two bundles, so every ``Topology`` runs from
  a controller pin to a memory pin.
- The board is :py:class:`jitx.sample.SampleDesign`: two layers, with 50 ohm
  and 100 ohm routing structures. Those are not DDR4 impedance targets; a
  real board passes its own structures.

The example is not routed, so the issue report lists each constrained path as
``Unconnected Topology`` and carries no measurement yet. To see the report,
with the project's runtime running::

    import jitx

    from jitxexamples.protocols.memory.ddr4_example import DDR4ExampleDesign


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(DDR4ExampleDesign).issues(satisfied=True, wait=30)
            if not report.complete:
                print("report incomplete: raise wait and run again")
            for group in report.groups():
                print("met" if group.satisfied else "NOT MET", group.text)
                if len(group.issues) > 1:
                    for issue in group:
                        print("   ", issue.text)


    if __name__ == "__main__":
        main()
"""

from __future__ import annotations

from jitx import PadMapping
from jitx.circuit import Circuit
from jitx.component import Component
from jitx.landpattern import Pad
from jitx.net import Net, Port
from jitx.sample import SampleDesign, SampleSubstrate
from jitxlib.landpatterns.generators.bga import BGA
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from jitxexamples.components.memories.MT40A1G16TB_062E_F import MT40A1G16TB_062E_F
from jitxexamples.protocols.memory.ddr4 import (
    DDR4,
    DDR4Constraint,
    DDR4Rank,
    DDR4Width,
    signal_ports,
)


class ControllerLandpattern(BGA):
    """8 x 8 ball BGA at 0.8 mm pitch for the fictional controller."""

    def __init__(self) -> None:
        super().__init__(num_rows=8, num_cols=8, ball_diameter=0.4, pitch=0.8)
        self.pad_config(SMDPadConfig(copper=-0.05))

    def balls(self) -> list[Pad]:
        """Return the balls row by row, A1 to H8."""
        rows = (self.A, self.B, self.C, self.D, self.E, self.F, self.G, self.H)
        return [row[col] for row in rows for col in range(1, 9)]


class ExampleDDR4Controller(Component):
    """Fictional DDR4 controller. Not a real product.

    Its DDR4 pins are the leaves of an x16, single-rank bundle with one CK
    pair and one bank-group bit, to match the memory, assigned to balls in
    :py:func:`~jitxexamples.protocols.memory.ddr4.signal_ports` order from
    A1; the remaining balls are ground.
    """

    reference_designator_prefix = "U"
    mpn = "EXAMPLE-DDR4-CTRL"
    manufacturer = "Fictional"

    ddr4 = DDR4(DDR4Width.x16, DDR4Rank.SingleRank, ck_count=1, bg_count=1)
    "Controller DDR4 interface"

    def __init__(self) -> None:
        self.landpattern = ControllerLandpattern()
        self.symbol = BoxSymbol()
        signals = signal_ports(self.ddr4)
        balls = self.landpattern.balls()
        self.gnd = [Port() for _ in range(len(balls) - len(signals))]
        pins = [*signals, *self.gnd]
        self.mapping = PadMapping(dict(zip(pins, balls, strict=True)))


class DDR4Example(Circuit):
    """Controller to memory over x16 DDR4, constrained, not routed."""

    def __init__(self) -> None:
        self.controller = ExampleDDR4Controller().at(-10, 0)
        self.memory = MT40A1G16TB_062E_F().at(10, 0)

        self.link = self.controller.ddr4 + self.memory.ddr4
        self.si = DDR4Constraint(
            ck_structure=SampleSubstrate.DRS_100,
            dqs_structure=SampleSubstrate.DRS_100,
            dq_structure=SampleSubstrate.RS_50,
            acc_structure=SampleSubstrate.RS_50,
        )
        self.si.constrain(self.controller.ddr4, self.memory.ddr4)

        mem = self.memory
        self.gnd = Net([*self.controller.gnd, *mem.VSS, *mem.VSSQ], name="GND")
        self.vdd = Net(mem.VDD, name="VDD")
        self.vddq = Net(mem.VDDQ, name="VDDQ")
        self.vpp = Net(mem.VPP, name="VPP")


class DDR4ExampleDesign(SampleDesign):
    """DDR4 example on the sample board and substrate."""

    circuit = DDR4Example()

"""
LPDDR4 example
==============

A fictional controller drives a Micron MT53E1G32D2FW-046 WT:B (LPDDR4X/LPDDR4)
over a dual-rank x32 link (two x16 channels), constrained with
:py:class:`~jitxexamples.protocols.memory.lpddr4.LPDDR4Constraint`.

- Both parts expose their LPDDR4 pins as an
  :py:class:`~jitxexamples.protocols.memory.lpddr4.LPDDR4` bundle, and one
  ordinary net joins the two bundles. There is no ``>>``.
- The constraint names the same two bundles, so every ``Topology`` runs from
  a controller pin to a memory pin.
- The board is :py:class:`jitx.sample.SampleDesign`: two layers, with 50 ohm
  and 100 ohm routing structures. Those are not LPDDR4 impedance targets; a
  real board passes its own structures.

The example is not routed, so the issue report lists each constrained path as
``Unconnected Topology`` and carries no measurement yet. Once the board is
routed, by hand or with code ``Route``\\ s, each constraint reports its
measured skew, and ``group.satisfied`` says whether it is met. To see the
report, with the project's runtime running::

    import jitx

    from jitxexamples.protocols.memory.lpddr4_example import LPDDR4ExampleDesign


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(LPDDR4ExampleDesign).issues(satisfied=True, wait=30)
            if not report.complete:
                print("report incomplete: raise wait and run again")
            for group in report.groups():
                print("met" if group.satisfied else "NOT MET", group.text)
                if len(group.issues) > 1:
                    for issue in group:
                        print("   ", issue.text)


    if __name__ == "__main__":
        main()

Keep the two bundles on the parts themselves. On jitx 4.6, an unrouted path
that passes through a circuit's port reports ``No path for signal
constraint`` instead of ``Unconnected Topology``, which reads like a wiring
fault; the same path measures normally once routed.
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

from jitxexamples.components.memories.MT53E1G32D2FW_046_WT_B import (
    MT53E1G32D2FW_046_WT_B,
)
from jitxexamples.protocols.memory.lpddr4 import (
    LPDDR4,
    LPDDR4Constraint,
    LPDDR4Rank,
    LPDDR4Width,
    signal_ports,
)


class ControllerLandpattern(BGA):
    """10 x 10 ball BGA at 0.8 mm pitch for the fictional controller."""

    def __init__(self) -> None:
        super().__init__(num_rows=10, num_cols=10, ball_diameter=0.4, pitch=0.8)
        self.pad_config(SMDPadConfig(copper=-0.05))

    def balls(self) -> list[Pad]:
        """Return the balls row by row, A1 to K10."""
        rows = (
            self.A,
            self.B,
            self.C,
            self.D,
            self.E,
            self.F,
            self.G,
            self.H,
            self.J,
            self.K,
        )
        return [row[col] for row in rows for col in range(1, 11)]


class ExampleLPDDR4Controller(Component):
    """Fictional LPDDR4 controller. Not a real product.

    Its LPDDR4 pins are the leaves of an x32, dual-rank bundle, assigned to
    balls in :py:func:`~jitxexamples.protocols.memory.lpddr4.signal_ports`
    order from A1; the remaining balls are ground.
    """

    reference_designator_prefix = "U"
    mpn = "EXAMPLE-LPDDR4-CTRL"
    manufacturer = "Fictional"

    lpddr4 = LPDDR4(LPDDR4Width.x32, LPDDR4Rank.Rank2)
    "Controller LPDDR4 interface"

    def __init__(self) -> None:
        self.landpattern = ControllerLandpattern()
        self.symbol = BoxSymbol()
        signals = signal_ports(self.lpddr4)
        balls = self.landpattern.balls()
        self.gnd = [Port() for _ in range(len(balls) - len(signals))]
        pins = [*signals, *self.gnd]
        self.mapping = PadMapping(dict(zip(pins, balls, strict=True)))


class LPDDR4Example(Circuit):
    """Controller to memory over x32 LPDDR4, constrained, not routed."""

    def __init__(self) -> None:
        self.controller = ExampleLPDDR4Controller().at(-12, 0)
        self.memory = MT53E1G32D2FW_046_WT_B().at(12, 0)

        self.link = self.controller.lpddr4 + self.memory.lpddr4
        self.si = LPDDR4Constraint(
            diff_structure=SampleSubstrate.DRS_100,
            se_structure=SampleSubstrate.RS_50,
        )
        self.si.constrain(self.controller.lpddr4, self.memory.lpddr4)

        mem = self.memory
        self.gnd = Net([*self.controller.gnd, *mem.VSS], name="GND")
        self.vdd1 = Net(mem.VDD1, name="VDD1")
        self.vdd2 = Net(mem.VDD2, name="VDD2")
        self.vddq = Net(mem.VDDQ, name="VDDQ")


class LPDDR4ExampleDesign(SampleDesign):
    """LPDDR4 example on the sample board and substrate."""

    circuit = LPDDR4Example()

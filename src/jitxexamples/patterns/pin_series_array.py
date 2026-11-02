"""Channel choice through a pass-through part, with both sides in one mapping.

Use this pattern when signals pass through a part whose channels are
interchangeable, and choosing a channel fixes a pin on each side of the part.
Here a 4-bit bus runs from a driver to a receiver through a 4-channel series
termination array; any channel may carry any bit, but a bit enters and leaves
on the same channel. Four pieces compose:

1. A bundle over both sides. ``ArrayChannel`` has a driver-side port ``a``
   and a receiver-side port ``b``. Each offered mapping sets both, so one
   choice moves both ends of the channel together. Two separate offers, one
   per side, could pick different channels for the two ends of a bit.
2. The provider. ``SeriesTermination`` offers ``ArrayChannel`` with
   ``@provide`` (``all_of``): one option per channel, each usable once, all
   usable together. The consumer takes four with
   ``require(ArrayChannel, count=4)`` and keeps them local.
3. The pin model. Each channel carries a ``BridgingPinModel`` from ``a[i]``
   to ``b[i]``; without one the path stops at the array.
4. The constraints, on fixed physical ends either side of the assigned part:
   ``Constrain(Topology(drv.d[i], rcv.d[i]))`` per bit, and
   ``ConstrainReferenceDifference`` for bus skew with bit 0 as the
   single-pin guide. While the assignment is unresolved, a bit reports
   ``No path for signal constraint``.

The shipping design, ``SeriesArrayDesign``, has no placement and no routes.
The verification designs place the parts and close every bit with code
``Route``\\ s that end on the array's physical pins:

- ``SwappedChannelsProof``: bits 0 and 1 swap channels (bit 0 on channel 1,
  bit 1 on channel 0), the same on both sides. Offered, so every bit
  measures.
- ``SidesDisagreeIllegal``: the driver side as in the swapped proof, the
  receiver side straight. Bits 0 and 1 enter on one channel and leave on
  another, which no option offers, so two of their four routes are dropped
  and both bits have no path; bits 2 and 3 still measure.

Every part is fictional, not a real product. The array's 5 ps and 0.05 dB per
channel, the 1 ns delay budget and the 10 ps bus skew window are illustrative
values; take real ones from the part's datasheet and the interface's timing
budget.

To check it, save this as a script in the project root and run it with the
project's runtime running::

    import jitx

    from jitxexamples.patterns.pin_series_array import SwappedChannelsProof


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(SwappedChannelsProof).issues(satisfied=True, wait=30)
            if not report.complete:
                print("report incomplete: raise wait and run again")
            for group in report.groups():
                print("met" if group.satisfied else "NOT MET", group.text)
                if len(group.issues) > 1:
                    for issue in group:
                        print("   ", issue.text)


    if __name__ == "__main__":
        main()

The real output for each design, on jitx 4.6.0rc10 against runtime
4.6.0-rc.16 (the shipping design and the two verification designs):

``SeriesArrayDesign``::

    NOT MET No path for signal constraint from drv.d[0] to rcv.d[0]
    NOT MET No path for signal constraint from drv.d[1] to rcv.d[1]
    NOT MET No path for signal constraint from drv.d[2] to rcv.d[2]
    NOT MET No path for signal constraint from drv.d[3] to rcv.d[3]
    met Satisfied

``SwappedChannelsProof``::

    met Time: 74.729ps - Target: 500ps ± 500ps from dut.drv.d[0] to dut.rcv.d[0]
    met Time: 97.061ps - Target: 500ps ± 500ps from dut.drv.d[1] to dut.rcv.d[1]
    met Time: 73.144ps - Target: 500ps ± 500ps from dut.drv.d[2] to dut.rcv.d[2]
    met Time: 73.144ps - Target: 500ps ± 500ps from dut.drv.d[3] to dut.rcv.d[3]
    NOT MET Skew: 22.332ps - Target: ± 10ps (longer from dut.drv.d[1] to dut.rcv.d[1], shorter from dut.drv.d[0] to dut.rcv.d[0])
    met Skew: 1.585ps - Target: ± 10ps (longer from dut.drv.d[0] to dut.rcv.d[0], shorter from dut.drv.d[2] to dut.rcv.d[2])
    met Skew: 1.585ps - Target: ± 10ps (longer from dut.drv.d[0] to dut.rcv.d[0], shorter from dut.drv.d[3] to dut.rcv.d[3])
    met Satisfied

``SidesDisagreeIllegal``::

    met Time: 73.144ps - Target: 500ps ± 500ps from dut.drv.d[2] to dut.rcv.d[2]
    met Time: 73.144ps - Target: 500ps ± 500ps from dut.drv.d[3] to dut.rcv.d[3]
    NOT MET No path for signal constraint from dut.drv.d[0] to dut.rcv.d[0]
    NOT MET No path for signal constraint from dut.drv.d[1] to dut.rcv.d[1]
    NOT MET 2 issues: Code route dropped: it conflicts with other connections
        Code route dropped: it conflicts with other connections
        Code route dropped: it conflicts with other connections

Bit 1's skew against bit 0 misses its window because the swapped routes
cross on one layer and come out unequal: the constraint bound, and this
routing fails it; read ``group.satisfied``, not the text. In the illegal
design bits 0 and 1 have no path, so the bus skew, guided by bit 0, has
no line at all.
"""

from collections.abc import Sequence

from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.feature import Courtyard, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.net import Net, Port, Topology, provide
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.shapes.composites import rectangle
from jitx.si import BridgingPinModel, Constrain, ConstrainReferenceDifference
from jitx.symbol import Direction, Pin, Symbol
from jitx.toleranced import Toleranced

BITS = 4
"""Bus width, and the array's channel count."""
ARRAY_DELAY = 5e-12
"""Illustrative: 5 ps through each array channel."""
ARRAY_LOSS = 0.05
"""Illustrative: 0.05 dB through each array channel."""
BIT_DELAY_BUDGET = 1e-9
"""Illustrative: 1 ns from driver to receiver."""
BUS_SKEW = Toleranced(0, 10e-12)
"""Illustrative: each bit within 10 ps of bit 0."""

STRAIGHT: tuple[int, ...] = (0, 1, 2, 3)
"""Array channel for each bit, bit 0 first: bit ``i`` on channel ``i``."""
SWAPPED: tuple[int, ...] = (1, 0, 2, 3)
"""Bits 0 and 1 exchange channels."""


class _SquarePad(Pad):
    shape = rectangle(0.6, 0.6)
    soldermask = Soldermask(shape)


class _ColumnLandpattern(Landpattern):
    """Pads in columns at 1 mm pitch, in port declaration order, top to bottom
    and left column first."""

    def __init__(self, columns: tuple[int, ...], pitch_x: float = 3.0) -> None:
        x0 = -pitch_x * (len(columns) - 1) / 2
        self.pads = [
            _SquarePad().at(x0 + c * pitch_x, (count - 1) / 2 - i)
            for c, count in enumerate(columns)
            for i in range(count)
        ]
        height = max(columns) + 0.5
        self.courtyard = Courtyard(
            rectangle(pitch_x * (len(columns) - 1) + 1.5, height)
        )


class _BoxSymbol(Symbol):
    def __init__(self, count: int) -> None:
        self.pins = [
            Pin(at=(-1, count // 2 - i), length=1, direction=Direction.Left)
            for i in range(count)
        ]
        self.body = rectangle(2, count + 1)


class BusDriver(Component):
    """Fictional 4-bit bus driver. Not a real part."""

    d = [Port() for _ in range(BITS)]
    gnd = Port()

    def __init__(self) -> None:
        self.landpattern = _ColumnLandpattern((BITS + 1,))
        self.symbol = _BoxSymbol(BITS + 1)


class BusReceiver(Component):
    """Fictional 4-bit bus receiver. Not a real part."""

    d = [Port() for _ in range(BITS)]
    gnd = Port()

    def __init__(self) -> None:
        self.landpattern = _ColumnLandpattern((BITS + 1,))
        self.symbol = _BoxSymbol(BITS + 1)


class SeriesArray4(Component):
    """Fictional 4-channel series termination array: channel ``i`` runs from
    ``a[i]`` to ``b[i]``, and the channels are identical. Not a real part; its
    pin-model values are illustrative."""

    a = [Port() for _ in range(BITS)]
    b = [Port() for _ in range(BITS)]

    def __init__(self) -> None:
        self.landpattern = _ColumnLandpattern((BITS, BITS))
        self.symbol = _BoxSymbol(2 * BITS)
        self.channels = [
            BridgingPinModel(self.a[i], self.b[i], delay=ARRAY_DELAY, loss=ARRAY_LOSS)
            for i in range(BITS)
        ]


class ArrayChannel(Port):
    """One array channel, both sides: ``a`` faces the driver, ``b`` the
    receiver."""

    a = Port()
    b = Port()


class SeriesTermination(Circuit):
    """The provider: every channel of the array, each offered once."""

    def __init__(self) -> None:
        self.array = SeriesArray4()

    @provide(ArrayChannel)
    def channel(self, ch: ArrayChannel) -> list[dict[Port, Port]]:
        # One mapping per channel, setting both sides.
        return [{ch.a: self.array.a[i], ch.b: self.array.b[i]} for i in range(BITS)]


class SeriesArrayBus(Circuit):
    """Driver to receiver through the array, every bit constrained. Unplaced
    and route-free, so the channel choice stays open."""

    def __init__(self) -> None:
        self.drv = BusDriver()
        self.rcv = BusReceiver()
        self.term = SeriesTermination()

        channels = self.term.require(ArrayChannel, count=BITS)  # local
        # Bit i: driver to the array's a side, b side to the receiver.
        self.D_DRV = [self.drv.d[i] + ch.a for i, ch in enumerate(channels)]
        self.D_RCV = [ch.b + self.rcv.d[i] for i, ch in enumerate(channels)]
        self.gnd_net = Net([self.drv.gnd, self.rcv.gnd], name="GND")

        # Fixed physical ends either side of the assigned part.
        bits = [Topology(self.drv.d[i], self.rcv.d[i]) for i in range(BITS)]
        self.bit_constraints = [
            Constrain(t).timing(BIT_DELAY_BUDGET).structure(SampleSubstrate.RS_50)
            for t in bits
        ]
        self.bus_skew = ConstrainReferenceDifference(
            guide=bits[0], topologies=bits[1:]
        ).timing_difference(BUS_SKEW)


class SeriesArrayDesign(SampleDesign):
    """The shipping design: no placement, no routes."""

    circuit = SeriesArrayBus()


class SeriesArrayProof(Circuit):
    """``SeriesArrayBus`` placed, with code routes on chosen array channels:
    bit ``i`` enters on ``drv_side[i]`` and leaves on ``rcv_side[i]``."""

    def __init__(self, drv_side: Sequence[int], rcv_side: Sequence[int]) -> None:
        self.dut = SeriesArrayBus()
        drv, rcv, array = self.dut.drv, self.dut.rcv, self.dut.term.array
        drv.at(-8, 0)
        array.at(0, 0)
        rcv.at(8, 0)
        self.routes = [
            route
            for i in range(BITS)
            for route in (
                Route(drv.d[i], array.a[drv_side[i]], layer=0),
                Route(array.b[rcv_side[i]], rcv.d[i], layer=0),
            )
        ]


class SwappedChannelsProof(SampleDesign):
    """Bits 0 and 1 on each other's channel, both sides: offered, so every
    bit measures."""

    def __init__(self) -> None:
        self.circuit = SeriesArrayProof(drv_side=SWAPPED, rcv_side=SWAPPED)


class SidesDisagreeIllegal(SampleDesign):
    """Driver side swapped, receiver side straight: bits 0 and 1 change
    channel inside the part, which is not offered, so their routes drop."""

    def __init__(self) -> None:
        self.circuit = SeriesArrayProof(drv_side=SWAPPED, rcv_side=STRAIGHT)

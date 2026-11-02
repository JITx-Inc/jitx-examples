"""Lane choice and P/N inversion on a provider that is one end of the path.

Use this pattern when a part may drive a differential link from any of
several lanes, either way round, and an SI constraint covers the link. The
provider is the driving part itself, so the constrained path begins on the
required port. Four pieces compose:

1. The provider. ``SerializerLanes`` offers one ``DiffPair`` with
   ``@provide.one_of``: lane 0 or lane 1, each straight or inverted
   (:py:data:`OFFERED`). ``one_of`` because the receiver takes a single lane.
   Offer inversion only where both ends of the link tolerate it, as the
   fictional parts here do.
2. The consumer. ``LanePolarityLink`` requires the pair, keeps it in a local
   variable (a required port stored on ``self`` fails the build), and nets it
   with plain ``+`` nets through a common-mode choke to the connector.
3. The pin model. The choke is a pass-through part, so each winding carries
   a ``BridgingPinModel``; without one the path stops at the choke.
4. The constraint. ``ConstrainDiffPair(Topology(lane, conn.rx))`` begins on
   the required pair. Until routes resolve the assignment the report says
   ``Unassigned Pin on Path``. Once they do, the measured line names the
   serializer pin the routes chose, inverted lanes included.

The shipping design, ``LanePolarityDesign``, has no placement and no routes,
so the assignment stays open for whoever routes the board. The verification
designs place the parts and close the path with code ``Route``\\ s that end
on the serializer's physical pins (a route cannot end on a required port):

- ``LaneZeroProof``: lane 0, straight. Offered, so it measures.
- ``LaneOneInvertedProof``: lane 1, inverted (``tx[1].n`` to connector
  ``rx.p``). Offered, so it measures from ``tx[1].n``.
- ``SplitLanesIllegal``: ``rx.p`` from lane 0, ``rx.n`` from lane 1. No
  offered mapping splits a lane, so a route is dropped.

Every part is fictional, not a real product. The choke's 2 ps and 0.02 dB per
winding, the 1 ns delay budget and the 5 ps skew limit are illustrative
values; take real ones from the part's datasheet and the protocol's
specification.

To check it, save this as a script in the project root and run it with the
project's runtime running::

    import jitx

    from jitxexamples.patterns.pin_lane_polarity import LaneOneInvertedProof


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(LaneOneInvertedProof).issues(satisfied=True, wait=30)
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
4.6.0-rc.16 (the shipping design and the three verification designs):

``LanePolarityDesign``::

    NOT MET 2 issues: Unassigned Pin on Path: TX_P.p
        Unassigned Pin on Path: TX_P.p
        Unconnected Topology on Path: choke.a_out, conn.rx.p
    NOT MET 2 issues: Unassigned Pin on Path: TX_P.n
        Unassigned Pin on Path: TX_P.n
        Unconnected Topology on Path: choke.b_out, conn.rx.n
    NOT MET 4 issues: Unassigned Pin on Path: TX_P.p
        Unassigned Pin on Path: TX_P.p
        Unconnected Topology on Path: choke.a_out, conn.rx.p
        Unassigned Pin on Path: TX_P.n
        Unconnected Topology on Path: choke.b_out, conn.rx.n
    met Satisfied

``LaneZeroProof``::

    met Time: 70.937ps - Target: 500ps ± 500ps from dut.ser.serializer.tx[0].p to dut.conn.rx.p
    met Time: 70.937ps - Target: 500ps ± 500ps from dut.ser.serializer.tx[0].n to dut.conn.rx.n
    met Skew: 0s - Target: ± 5ps (longer from dut.ser.serializer.tx[0].p to dut.conn.rx.p, shorter from dut.ser.serializer.tx[0].n to dut.conn.rx.n)
    met Satisfied

``LaneOneInvertedProof``::

    met Time: 70.937ps - Target: 500ps ± 500ps from dut.ser.serializer.tx[1].n to dut.conn.rx.p
    met Time: 81.924ps - Target: 500ps ± 500ps from dut.ser.serializer.tx[1].p to dut.conn.rx.n
    NOT MET Skew: 10.987ps - Target: ± 5ps (longer from dut.ser.serializer.tx[1].p to dut.conn.rx.n, shorter from dut.ser.serializer.tx[1].n to dut.conn.rx.p)
    met Satisfied

``SplitLanesIllegal``::

    NOT MET Unassigned Pin on Path: dut.TX_P.p
    NOT MET Unassigned Pin on Path: dut.TX_P.p
    met Time: 70.144ps - Target: 500ps ± 500ps from dut.ser.serializer.tx[1].n to dut.conn.rx.n
    NOT MET Code route dropped: it conflicts with other connections

Lane 1 inverted measures from ``tx[1].n``: the routes resolved the inverted
mapping. Its skew misses the window because its two routes cross on one
layer and come out unequal: the constraint bound, and this routing fails it.
A measurement means the constraint applied; whether it is met is
``group.satisfied``. In the illegal design the dropped route leaves ``rx.p``
with no assignment, and ``rx.n`` still measures from the lane its route
fits.
"""

from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.feature import Courtyard, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.net import DiffPair, Net, Port, Topology, provide
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.shapes.composites import rectangle
from jitx.si import BridgingPinModel, ConstrainDiffPair
from jitx.symbol import Direction, Pin, Symbol
from jitx.toleranced import Toleranced

CHOKE_DELAY = 2e-12
"""Illustrative: 2 ps through each choke winding."""
CHOKE_LOSS = 0.02
"""Illustrative: 0.02 dB through each choke winding."""
LINK_DELAY_BUDGET = 1e-9
"""Illustrative: 1 ns from serializer to connector."""
LINK_SKEW = Toleranced(0, 5e-12)
"""Illustrative: 5 ps intra-pair skew."""

Mapping = tuple[int, bool]
"""A serializer lane and whether its P/N are inverted."""

OFFERED: tuple[Mapping, ...] = ((0, False), (0, True), (1, False), (1, True))
"""Every option the provider offers: either lane, either way round."""


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


class Serializer(Component):
    """Fictional two-lane serializer. Either lane may carry the link, and its
    link partner corrects P/N polarity. Not a real part."""

    tx = (DiffPair(), DiffPair())
    """Transmit lanes 0 and 1."""
    gnd = Port()

    def __init__(self) -> None:
        self.landpattern = _ColumnLandpattern((5,))
        self.symbol = _BoxSymbol(5)


class CommonModeChoke(Component):
    """Fictional common-mode choke: winding A from ``a_in`` to ``a_out``,
    winding B from ``b_in`` to ``b_out``. Not a real part; its pin-model values
    are illustrative."""

    a_in = Port()
    b_in = Port()
    a_out = Port()
    b_out = Port()

    def __init__(self) -> None:
        self.landpattern = _ColumnLandpattern((2, 2))
        self.symbol = _BoxSymbol(4)
        self.windings = [
            BridgingPinModel(self.a_in, self.a_out, delay=CHOKE_DELAY, loss=CHOKE_LOSS),
            BridgingPinModel(self.b_in, self.b_out, delay=CHOKE_DELAY, loss=CHOKE_LOSS),
        ]


class LinkConnector(Component):
    """Fictional one-lane connector. Not a real part."""

    rx = DiffPair()
    gnd = Port()

    def __init__(self) -> None:
        self.landpattern = _ColumnLandpattern((3,))
        self.symbol = _BoxSymbol(3)


class SerializerLanes(Circuit):
    """The provider: the serializer, offering one lane either way round."""

    gnd = Port()

    def __init__(self) -> None:
        self.serializer = Serializer()
        self.gnd_net = self.gnd + self.serializer.gnd

    @provide.one_of(DiffPair)
    def lane(self, pair: DiffPair) -> list[dict[Port, Port]]:
        tx = self.serializer.tx
        return [
            {pair.p: tx[k].n, pair.n: tx[k].p}
            if inverted
            else {pair.p: tx[k].p, pair.n: tx[k].n}
            for k, inverted in OFFERED
        ]


class LanePolarityLink(Circuit):
    """Serializer lane to connector through the choke, constrained end to end.
    Unplaced and route-free, so the assignment stays open."""

    def __init__(self) -> None:
        self.ser = SerializerLanes()
        self.choke = CommonModeChoke()
        self.conn = LinkConnector()

        lane = self.ser.require(DiffPair)  # local, never self.lane
        self.TX_P = lane.p + self.choke.a_in
        self.TX_N = lane.n + self.choke.b_in
        self.RX_P = self.choke.a_out + self.conn.rx.p
        self.RX_N = self.choke.b_out + self.conn.rx.n
        self.gnd_net = Net([self.ser.gnd, self.conn.gnd], name="GND")

        # The provider is one end: the Topology begins on the required pair.
        self.link_constraint = (
            ConstrainDiffPair(Topology(lane, self.conn.rx))
            .timing_difference(LINK_SKEW)
            .timing(LINK_DELAY_BUDGET)
            .structure(SampleSubstrate.DRS_100)
        )


class LanePolarityDesign(SampleDesign):
    """The shipping design: no placement, no routes."""

    circuit = LanePolarityLink()


class LanePolarityProof(Circuit):
    """``LanePolarityLink`` placed, with code routes from the serializer to
    the choke: ``rx.p``'s winding from lane ``p_lane``, ``rx.n``'s from lane
    ``n_lane``, each lane's legs crossed when ``inverted``."""

    def __init__(self, p_lane: int, n_lane: int, inverted: bool) -> None:
        self.dut = LanePolarityLink()
        tx = self.dut.ser.serializer.tx
        choke = self.dut.choke
        conn = self.dut.conn
        self.dut.ser.serializer.at(-8, 0)
        choke.at(0, 0)
        conn.at(8, 0)

        p_pin = tx[p_lane].n if inverted else tx[p_lane].p
        n_pin = tx[n_lane].p if inverted else tx[n_lane].n
        self.routes = [
            Route(p_pin, choke.a_in, layer=0),
            Route(n_pin, choke.b_in, layer=0),
            Route(choke.a_out, conn.rx.p, layer=0),
            Route(choke.b_out, conn.rx.n, layer=0),
        ]


class LaneZeroProof(SampleDesign):
    """Lane 0, straight: offered, so the constraint measures."""

    def __init__(self) -> None:
        self.circuit = LanePolarityProof(p_lane=0, n_lane=0, inverted=False)


class LaneOneInvertedProof(SampleDesign):
    """Lane 1, inverted: offered, so the constraint measures from ``tx[1].n``."""

    def __init__(self) -> None:
        self.circuit = LanePolarityProof(p_lane=1, n_lane=1, inverted=True)


class SplitLanesIllegal(SampleDesign):
    """``rx.p`` from lane 0 and ``rx.n`` from lane 1: not offered, so a route
    is dropped."""

    def __init__(self) -> None:
        self.circuit = LanePolarityProof(p_lane=0, n_lane=1, inverted=False)

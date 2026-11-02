"""A reusable protocol constraint: a ``SignalConstraint`` subclass, built and
applied on ordinary nets.

:py:class:`ExampleLinkConstraint` constrains an
:py:class:`ExampleSerialLink` bundle (a ``tx`` and an ``rx`` pair) between
two ends. Its parameters live in a frozen dataclass,
:py:class:`ExampleLinkStandard`, and its ``__init__`` calls
``super().__init__()`` first: the base initializer creates the collection
that ``self.add(...)`` extends. It looks the differential structure up on
the design's substrate by impedance unless one is passed, and holds one
``DiffPairConstraint`` stored on ``self``. ``constrain(src, dst)`` applies it
across the crossover, each end's ``tx`` to the other end's ``rx``.

The circuit calls ``self.link_cst.constrain(self.host.link, self.phy.link)``
on the chips' own bundles, the true ends, and wires the parts between them
as usual. The host's transmit pair passes through
:py:class:`ExampleDualCoupler`, which carries a ``BridgingPinModel`` on each
leg. The constraint does not change for the coupler; the pin models carry
the path across it.

``SignalConstraint.constrain_topology(src, dst)`` calls ``constrain(src,
dst)`` at once and returns a context manager that yields ``(src, dst)``; it
only moves an end along a ``>>`` chain already in the circuit, so on
ordinary nets it adds nothing over ``constrain``.

The standard's values are illustrative, not from any specification. For
protocols with several signal groups, compose: hold one constraint per group
and call each from ``constrain``, as
:py:mod:`jitxexamples.protocols.memory` does for DDR4 and LPDDR4.

Checked with the design-issues query, run as a script from a project
root with that project's runtime running
(jitx 4.6.0rc10, runtime 4.6.0-rc.16)::

    import jitx

    from jitxexamples.patterns.si_signal_constraint import SerialLinkDesign


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(SerialLinkDesign).issues(satisfied=True, wait=30)
            if not report.complete:
                print("report incomplete: raise wait and run again")
            for group in report.groups():
                print("met" if group.satisfied else "NOT MET", group.text)
                if len(group.issues) > 1:
                    for issue in group:
                        print("   ", issue.text)


    if __name__ == "__main__":
        main()

It printed::

    met Loss: 0.389db - Target: 1.5db ± 1.5db from host.link.tx.p to phy.link.rx.p
    met Loss: 0.389db - Target: 1.5db ± 1.5db from host.link.tx.n to phy.link.rx.n
    met Loss: 0.356db ± 0db - Target: 1.5db ± 1.5db from phy.link.tx.p to host.link.rx.p
    met Loss: 0.356db ± 0db - Target: 1.5db ± 1.5db from phy.link.tx.n to host.link.rx.n
    met Skew: 0s - Target: ± 2ps (longer from host.link.tx.p to phy.link.rx.p, shorter from host.link.tx.n to phy.link.rx.n)
    met Skew: 0s - Target: ± 2ps (longer from phy.link.tx.p to host.link.rx.p, shorter from phy.link.tx.n to host.link.rx.n)
    met Satisfied

The transmit legs measure more loss than the receive legs, 0.389 dB against
0.356 dB. Their path adds the coupler's 0.06 dB per leg but carries 1.5 mm
less trace, the coupler's pad span, so the difference is 0.033 dB, not the
model's 0.06 dB.

The last line is the Routing category's group: every code route was made.
It is not a constraint verdict.
"""

from __future__ import annotations

from dataclasses import dataclass

from jitx import PadMapping, current
from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.feature import Courtyard
from jitx.landpattern import Landpattern
from jitx.net import DiffPair, Port
from jitx.sample import SampleDesign
from jitx.shapes.composites import rectangle
from jitx.si import (
    BridgingPinModel,
    DiffPairConstraint,
    DifferentialRoutingStructure,
    SignalConstraint,
)
from jitx.toleranced import Toleranced
from jitxlib.symbols.box import BoxSymbol

from jitxexamples.patterns.si_parts import PadColumn, SquarePad


@dataclass(frozen=True)
class ExampleLinkStandard:
    """Limits for the fictional serial link. The values are illustrative, not
    taken from any standard."""

    skew: Toleranced = Toleranced(0, 2e-12)
    """Intra-pair skew window, in seconds."""
    loss: float = 3.0
    """Maximum insertion loss per leg, in dB."""
    impedance: float = 100.0
    """Differential impedance target, in ohms, used to look up the routing
    structure on the design's substrate."""


class ExampleSerialLink(Port):
    """A full-duplex serial link: one transmit pair and one receive pair."""

    tx = DiffPair()
    rx = DiffPair()


class ExampleLinkConstraint(SignalConstraint[ExampleSerialLink]):
    """Constrain a serial link between two ends: each end's ``tx`` to the
    other end's ``rx``, with the standard's skew, loss and structure."""

    def __init__(
        self,
        standard: ExampleLinkStandard,
        structure: DifferentialRoutingStructure | None = None,
    ) -> None:
        super().__init__()
        if structure is None:
            structure = current.substrate.differential_routing_structure(
                standard.impedance
            )
        self.pair_cst = DiffPairConstraint(
            skew=standard.skew, loss=standard.loss, structure=structure
        )

    def constrain(self, src: ExampleSerialLink, dst: ExampleSerialLink) -> None:
        self.pair_cst.constrain(src.tx, dst.rx)
        self.pair_cst.constrain(dst.tx, src.rx)


class ExampleLinkChip(Component):
    """Fictional chip with one serial link. Not a real product, and it has no
    pin models.

    ``rx_first`` puts the receive pair on the lower two pads, so two chips
    facing each other line their crossing pairs up.
    """

    manufacturer = "Fictional"
    mpn = "EXAMPLE-LINK"
    reference_designator_prefix = "U"

    link = ExampleSerialLink()

    def __init__(self, rx_first: bool = False) -> None:
        self.landpattern = PadColumn(4)
        self.symbol = BoxSymbol()
        lower, upper = (
            (self.link.rx, self.link.tx)
            if rx_first
            else (
                self.link.tx,
                self.link.rx,
            )
        )
        pins = [lower.p, lower.n, upper.p, upper.n]
        self.mapping = PadMapping(dict(zip(pins, self.landpattern.pads, strict=True)))


class CouplerPads(Landpattern):
    """Two columns of two square pads, 1.5 mm apart: ``a`` left, ``b`` right."""

    def __init__(self) -> None:
        self.pads = [SquarePad().at(x, y) for x in (-0.75, 0.75) for y in (-0.5, 0.5)]
        self.courtyard = Courtyard(rectangle(2.5, 2.0))


class ExampleDualCoupler(Component):
    """Fictional two-channel AC coupling part for one differential pair. Not
    a real product.

    The signal passes through it from ``a`` to ``b`` on each leg, so each leg
    carries a ``BridgingPinModel``: 3 ps and 0.06 dB, values that are
    illustrative.
    """

    manufacturer = "Fictional"
    mpn = "EXAMPLE-COUPLER"
    reference_designator_prefix = "C"

    a = DiffPair()
    b = DiffPair()
    through = [
        BridgingPinModel(a.p, b.p, delay=3e-12, loss=0.06),
        BridgingPinModel(a.n, b.n, delay=3e-12, loss=0.06),
    ]

    def __init__(self) -> None:
        self.landpattern = CouplerPads()
        self.symbol = BoxSymbol()
        pins = [self.a.p, self.a.n, self.b.p, self.b.n]
        self.mapping = PadMapping(dict(zip(pins, self.landpattern.pads, strict=True)))


class SerialLink(Circuit):
    """Two chips joined by a serial link, constrained by one
    ``ExampleLinkConstraint``; the transmit pair from ``host`` passes through
    a coupler."""

    def __init__(self) -> None:
        self.host = ExampleLinkChip().at(-10, 0)
        self.phy = ExampleLinkChip(rx_first=True).at(10, 0)
        self.coupler = ExampleDualCoupler().at(0, -1.0)

        self.link_cst = ExampleLinkConstraint(ExampleLinkStandard())
        self.link_cst.constrain(self.host.link, self.phy.link)

        host, phy, cpl = self.host.link, self.phy.link, self.coupler
        # Host TX into the coupler, coupler out to the PHY RX, PHY TX back.
        self.TX = host.tx + cpl.a
        self.TX_CPL = cpl.b + phy.rx
        self.RX = phy.tx + host.rx
        self.routes = [
            Route(host.tx.p, cpl.a.p, layer=0),
            Route(host.tx.n, cpl.a.n, layer=0),
            Route(cpl.b.p, phy.rx.p, layer=0),
            Route(cpl.b.n, phy.rx.n, layer=0),
            Route(phy.tx.p, host.rx.p, layer=0),
            Route(phy.tx.n, host.rx.n, layer=0),
        ]


class SerialLinkDesign(SampleDesign):
    """The serial link on the sample board."""

    circuit = SerialLink()

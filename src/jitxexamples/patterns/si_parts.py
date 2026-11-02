"""Fictional parts shared by the ``si_*`` signal-integrity patterns.

None of these parts is a real product. Every pin model value below is
illustrative: it stands where a datasheet, IBIS model or vendor model figure
goes in a real design. A measurement in a pattern is therefore a proof-route
number on the two-layer :py:class:`jitx.sample.SampleSubstrate`, not a
characterization of any part.

Each part has one column of 0.6 mm square pads at 1.0 mm pitch, assigned to
its ports in declaration order (a ``DiffPair`` gives ``p`` then ``n``). Two
parts placed facing each other at the same height line their pads up, so a
straight code ``Route`` on layer 0 joins each pair of pads.
"""

from __future__ import annotations

from jitx.component import Component
from jitx.feature import Courtyard, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.net import DiffPair, Port
from jitx.shapes.composites import rectangle
from jitx.si import BridgingPinModel, TerminatingPinModel
from jitxlib.symbols.box import BoxSymbol

PAD_PITCH = 1.0
"""Distance between pad centres, in mm."""


class SquarePad(Pad):
    """0.6 mm square SMD pad."""

    shape = rectangle(0.6, 0.6)
    soldermask = Soldermask(shape)


class PadColumn(Landpattern):
    """``count`` square pads in one column, centred on the origin."""

    def __init__(self, count: int) -> None:
        offset = (count - 1) * PAD_PITCH / 2
        self.pads = [SquarePad().at(0, i * PAD_PITCH - offset) for i in range(count)]
        self.courtyard = Courtyard(rectangle(1.5, count * PAD_PITCH + 0.5))


class ExampleChip(Component):
    """Fictional chip with one single-ended signal pin, ``io``. Not a real
    product. It has no pin model: the measured delay starts and ends at its
    pad."""

    manufacturer = "Fictional"
    mpn = "EXAMPLE-SE-CHIP"
    reference_designator_prefix = "U"

    io = Port()

    def __init__(self) -> None:
        self.landpattern = PadColumn(1)
        self.symbol = BoxSymbol()


class ExampleTerminatedChip(Component):
    """Fictional chip whose signal pin carries a package model. Not a real
    product.

    ``package`` adds 10 ps and 0.2 dB from the pad into the die, values that
    are illustrative. A real part takes them from its datasheet or IBIS
    package model.
    """

    manufacturer = "Fictional"
    mpn = "EXAMPLE-SE-CHIP-PKG"
    reference_designator_prefix = "U"

    io = Port()
    package = TerminatingPinModel(io, delay=10e-12, loss=0.2)

    def __init__(self) -> None:
        self.landpattern = PadColumn(1)
        self.symbol = BoxSymbol()


class ExampleSeriesResistor(Component):
    """Fictional series resistor that a signal passes through. Not a real
    product.

    ``through`` gives the path 4 ps and 0.08 dB from ``a`` to ``b``, values
    that are illustrative. Without a ``BridgingPinModel`` the runtime stops
    the path at this part.
    """

    manufacturer = "Fictional"
    mpn = "EXAMPLE-SERIES-R"
    reference_designator_prefix = "R"

    a = Port()
    b = Port()
    through = BridgingPinModel(a, b, delay=4e-12, loss=0.08)

    def __init__(self) -> None:
        self.landpattern = PadColumn(2)
        self.symbol = BoxSymbol()


class ExampleTwoLaneChip(Component):
    """Fictional chip with two differential lanes, ``lane0`` and ``lane1``.
    Not a real product, and it has no pin models."""

    manufacturer = "Fictional"
    mpn = "EXAMPLE-2LANE"
    reference_designator_prefix = "U"

    lane0 = DiffPair()
    lane1 = DiffPair()

    def __init__(self) -> None:
        self.landpattern = PadColumn(4)
        self.symbol = BoxSymbol()

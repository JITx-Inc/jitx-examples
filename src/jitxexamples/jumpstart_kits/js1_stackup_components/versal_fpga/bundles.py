"""Versal GTM transceiver bundle and its structural pin grouping.

Bundle shape
    Follows the JITX Versal protocol-bundle convention: a GT quad is four
    ``LanePair`` lanes plus two reference-clock diff pairs.
    On the VP1002 in NFVI1369 each GTM bank (202-207) carries exactly
    4 x (RXP/RXN + TXP/TXN) lanes and 2 x REFCLKP/REFCLKN pairs — see the
    per-bank rows of the AMD package pinout file (``xcvp1002nfvi1369pkg.txt``)
    and AM013 (v1.9) "GTM Transceiver Pins".

Naming
    ``LanePair`` keeps the upper-case ``TX``/``RX`` sub-port style of
    ``jitx.common``; ``DiffPair`` uses lower-case ``p``/``n`` (the Python
    convention). Consumers therefore write ``quad.L[0].TX.p``.

``GTMQuadPins``
    The structural grouping the generated :class:`~.xcvp1002.XCVP1002`
    component exposes for each GTM bank so the circuit wrapper can wire a
    :class:`GTMQuad` bundle without composing attribute names at runtime.
    (Wrapper code in the wild often resolves pins via ``getattr`` name
    composition; this repo's conventions forbid that — every reference in
    a ``GTMQuadPins`` is an explicit attribute of the generated component.)
"""

from collections.abc import Sequence
from dataclasses import dataclass

from jitx.common import LanePair
from jitx.net import DiffPair, Port

LANES_PER_QUAD = 4
REFCLKS_PER_QUAD = 2


class GTMQuad(Port):
    """Versal GTM transceiver quad: 4 lanes + 2 reference clocks."""

    L: Sequence[LanePair]
    REFCLK: Sequence[DiffPair]

    def __init__(self):
        self.L = tuple(LanePair() for _ in range(LANES_PER_QUAD))
        self.REFCLK = tuple(DiffPair() for _ in range(REFCLKS_PER_QUAD))


@dataclass(frozen=True)
class GTMQuadPins:
    """Component pins of one GTM bank, in lane / refclk index order."""

    rxp: tuple[Port, ...]
    rxn: tuple[Port, ...]
    txp: tuple[Port, ...]
    txn: tuple[Port, ...]
    refclkp: tuple[Port, ...]
    refclkn: tuple[Port, ...]

    def __post_init__(self) -> None:
        lanes = {
            "rxp": self.rxp,
            "rxn": self.rxn,
            "txp": self.txp,
            "txn": self.txn,
        }
        for name, pins in lanes.items():
            if len(pins) != LANES_PER_QUAD:
                raise ValueError(f"{name} must have {LANES_PER_QUAD} pins")
        refclks = {"refclkp": self.refclkp, "refclkn": self.refclkn}
        for name, pins in refclks.items():
            if len(pins) != REFCLKS_PER_QUAD:
                raise ValueError(f"{name} must have {REFCLKS_PER_QUAD} pins")

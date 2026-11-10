"""Port bundles for the Versal side of an LPDDR4X x32 interface.

The memory side is :py:class:`~jitxexamples.protocols.memory.lpddr4.LPDDR4`.
The controller side drives one CKE per channel, as AMD's VMK180, VCK190 and
VPK120 boards map it, where a dual-rank memory has one per rank (UG863 lists
CKE0 and CKE1 per channel; see :py:mod:`.pinout`). So it is
:py:class:`~jitxexamples.protocols.memory.lpddr4.LPDDR4SharedCKE`, and a
design nets its one CKE to both memory CKE balls.
"""

from jitx.net import Port

from jitxexamples.protocols.memory.lpddr4 import LPDDR4SharedCKE


class VersalLPDDR4X(LPDDR4SharedCKE):
    """An x32 LPDDR4X interface of a Versal DDRMC: channels A (DQ0 to DQ15)
    and B (DQ16 to DQ31), and the memory reset."""

    reset_n = Port()
    "Memory reset, active low"


class Slot0Bit(Port):
    """One DQ pin of byte slot 0. See :py:class:`.circuit.VP1002LPDDR4X`."""

    p = Port()


class Slot1Bit(Port):
    """One DQ pin of byte slot 1."""

    p = Port()


class Slot2Bit(Port):
    """One DQ pin of byte slot 2."""

    p = Port()


class Slot3Bit(Port):
    """One DQ pin of byte slot 3."""

    p = Port()


SLOT_BITS: tuple[type[Slot0Bit | Slot1Bit | Slot2Bit | Slot3Bit], ...] = (
    Slot0Bit,
    Slot1Bit,
    Slot2Bit,
    Slot3Bit,
)
"The DQ pin type of each byte slot, in :py:data:`.pinout.LPDDR4X_X32` order."

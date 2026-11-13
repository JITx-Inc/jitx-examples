"""The LPDDR4 x32 pinout the VP1002 offers on banks 702 and 701, as data.

Positions are triplet-relative: ``Pos(bank, nibble, pin)``, where ``bank`` is
0, 1 or 2 within the triplet, ``nibble`` is N0 to N8 and ``pin`` is P0 to P5.
``Pos.index`` is the ``MxP`` number in the pin file's pin names. On the
VP1002 the only triplet is M0, banks 700, 701 and 702.

The layout is the single channel x32 pinout, flipped, on the third and second
banks of the triplet. Its free choices are AMD's two LPDDR4/4X pin swaps:
a byte may take either byte slot of its channel, with its DQS and DMI, and a
byte's eight DQ may take its slot's DQ pins in any order. Command, address,
clock, chip select, clock enable, reset and system clock pins are fixed.
That is ``2 * 2 * factorial(8) ** 4`` assignments,
:py:func:`assignment_count`.

Sources
-------

- AMD PG313, *Versal Adaptive SoC Programmable Network on Chip and
  Integrated Memory Controller LogiCORE IP Product Guide*, v1.1, 2026-06-23,
  "LPDDR4/4X Pin Rules" (the swaps, Tables 1 and 2) and "Single Channel
  LPDDR4/4X Interfaces" (the nibble use).
- AMD Vivado-Design-Tutorials, tag 2025.2,
  ``Versal/PCB_Design/Memory_Pinouts/README.md``, Appendix B (the flipped
  pinout).
- PG313 places most fixed pins only to the nibble. The pin within each
  nibble is where channel 0 of AMD's VMK180, VCK190 and VPK120 boards puts it
  (XilinxBoardStore tag 2025.2; VCK190 from Vivado-Design-Tutorials tag
  2025.2, ``lpddr4_mc3_vck190.xdc``). VCK190 is single rank and has no CS1.
- The offer has one CKE per channel, as every one of those boards maps it,
  including the dual-rank VMK180 and VPK120; a design nets it to both of the
  memory channel's CKE balls. UG863's LPDDR4/4x timing table lists CKE0 and
  CKE1 per channel for dual-rank devices, so a design that needs a second
  CKE does not use this layout as is.

PG313 says every pin swap must be captured in the design's XDC and validated
before generating hardware. This module exports no XDC and does not claim
Vivado legality: validating the chosen assignment is the designer's step.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from math import factorial

BANK_NIBBLES = 9
NIBBLE_PINS = 6


@dataclass(frozen=True, order=True)
class Pos:
    """A triplet-relative pin position."""

    bank: int
    "0, 1 or 2 within the triplet"

    nibble: int
    "0 to 8"

    pin: int
    "0 to 5"

    @property
    def index(self) -> int:
        """The ``MxP`` number of this position in the pin file."""
        return (self.bank * BANK_NIBBLES + self.nibble) * NIBBLE_PINS + self.pin


class Channel(Enum):
    """An LPDDR4 x16 channel of the memory."""

    A = "A"
    B = "B"


@dataclass(frozen=True)
class ByteSlot:
    """The nibble pair one byte occupies: DQS_T and DQS_C on P0 and P1 of one
    nibble, DMI on P0 of its partner, the eight DQ on P2 to P5 of both."""

    channel: Channel
    bank: int
    dqs_nibble: int

    @property
    def dmi_nibble(self) -> int:
        """The partner nibble, with DMI on P0."""
        return self.dqs_nibble ^ 1

    @property
    def dqs_t(self) -> Pos:
        return Pos(self.bank, self.dqs_nibble, 0)

    @property
    def dqs_c(self) -> Pos:
        return Pos(self.bank, self.dqs_nibble, 1)

    @property
    def dmi(self) -> Pos:
        return Pos(self.bank, self.dmi_nibble, 0)

    @property
    def dq(self) -> tuple[Pos, ...]:
        """The eight DQ positions: P2 to P5 of the DQS nibble, then of the DMI
        nibble. A byte's DQ may take them in any order."""
        return tuple(
            Pos(self.bank, n, p)
            for n in (self.dqs_nibble, self.dmi_nibble)
            for p in range(2, NIBBLE_PINS)
        )


@dataclass(frozen=True)
class PinLayout:
    """A layout at pin level: the fixed pins and the byte slots."""

    slots: tuple[ByteSlot, ...]
    "Byte slots; slot ``k`` holds byte ``k`` before any byte swap"

    fixed: Mapping[str, Pos]

    def byte_orders(self) -> list[tuple[int, int, int, int]]:
        """Every allowed byte-to-slot assignment: entry ``k`` is the slot
        index byte ``k`` takes. A byte stays in its own channel."""
        a = [i for i, s in enumerate(self.slots) if s.channel is Channel.A]
        b = [i for i, s in enumerate(self.slots) if s.channel is Channel.B]
        return [
            (a0, a1, b0, b1)
            for a0, a1 in (tuple(a), tuple(reversed(a)))
            for b0, b1 in (tuple(b), tuple(reversed(b)))
        ]


A, B = Channel.A, Channel.B

LPDDR4_X32 = PinLayout(
    slots=(
        ByteSlot(A, 1, 3),  # byte 0: bank 701, DQS on N3
        ByteSlot(A, 2, 5),  # byte 1: bank 702, DQS on N5
        ByteSlot(B, 1, 7),  # byte 2: bank 701, DQS on N7
        ByteSlot(B, 2, 6),  # byte 3: bank 702, DQS on N6
    ),
    fixed={
        # Bank 702 N0 and N1: channel A command, address and clock
        "CA2_A": Pos(2, 0, 0),
        "CS1_A": Pos(2, 0, 1),
        "CA1_A": Pos(2, 0, 2),
        "CA0_A": Pos(2, 0, 3),
        "CS0_A": Pos(2, 0, 4),
        "CA3_A": Pos(2, 0, 5),
        "CK_T_A": Pos(2, 1, 0),
        "CK_C_A": Pos(2, 1, 1),
        "CA4_A": Pos(2, 1, 2),
        "CA5_A": Pos(2, 1, 3),
        "CKE_A": Pos(2, 1, 4),
        # Bank 702 N2 and N3: channel B command, address and clock
        "CA0_B": Pos(2, 2, 2),
        "CA3_B": Pos(2, 2, 4),
        "CA2_B": Pos(2, 2, 5),
        "CK_T_B": Pos(2, 3, 0),
        "CK_C_B": Pos(2, 3, 1),
        "CA5_B": Pos(2, 3, 2),
        "CA4_B": Pos(2, 3, 3),
        "CKE_B": Pos(2, 3, 4),
        "CA1_B": Pos(2, 3, 5),
        # P1 of two DMI nibbles
        "CS0_B": Pos(2, 7, 1),
        "CS1_B": Pos(2, 4, 1),
        # Bank 702 N8: system clock and reset
        "SYS_CLK_P": Pos(2, 8, 0),
        "SYS_CLK_N": Pos(2, 8, 1),
        "RESET_N": Pos(2, 8, 2),
    },
)
"""The offered layout: single channel x32, flipped, on banks 702 and 701."""


def assignment_count(layout: PinLayout = LPDDR4_X32) -> int:
    """Number of distinct pin assignments the layout allows."""
    return len(layout.byte_orders()) * factorial(8) ** len(layout.slots)

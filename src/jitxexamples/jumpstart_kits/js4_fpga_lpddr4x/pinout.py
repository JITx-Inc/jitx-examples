"""AMD Versal LPDDR4/4X pin rules on one DDRMC triplet, as data.

Positions are triplet-relative: ``Pos(bank, nibble, pin)``, where ``bank`` is
0, 1 or 2 within the triplet (the first, second and third bank of AMD's
figures), ``nibble`` is N0 to N8 and ``pin`` is P0 to P5. ``Pos.index`` is the
``MxP`` number in the pin file's pin names. On the VP1002 the only triplet is
M0, banks 700, 701 and 702.

Sources
-------

- PG313: AMD, *Versal Adaptive SoC Programmable Network on Chip and
  Integrated Memory Controller 1.1 LogiCORE IP Product Guide*, PG313 v1.1,
  2026-06-23, https://docs.amd.com/r/en-US/pg313-network-on-chip.
- AM013: AMD, *Versal Adaptive SoC Packaging and Pinouts Architecture
  Manual*, AM013 v1.10, "About ASCII Package Files".
- Tutorial: AMD, Vivado-Design-Tutorials, tag 2025.2,
  ``Versal/PCB_Design/Memory_Pinouts/README.md``, Appendix B, "LPDDR4 and
  LPDDR4X Pinouts" (Apache-2.0).
- Boards: AMD board files, XilinxBoardStore tag 2025.2,
  ``boards/Xilinx/vmk180/production/3.3``, ``.../vpk120/production/1.2`` and
  ``.../vek280/production/1.2`` (``part0_pins.xml`` and ``board.xml``), and
  the VCK190 constraints ``lpddr4_mc3_vck190.xdc`` in Vivado-Design-Tutorials
  tag 2025.2, ``Versal/Memory_and_NoC/NoC_DDRMC/Performance_Tuning``
  (Apache-2.0). Each pin there is placed in its triplet with the device's
  own AMD package file. ``tests/test_js4_pinout.py`` holds the result.

Rule table
----------

==  ==========================================================  ==============================
#   Rule                                                        Source
==  ==========================================================  ==============================
1   Every command, address, control, reset and clock pin is     PG313, "LPDDR4/4X Pin Rules"
    fixed: CA_A, CA_B, CKE_A, CKE_B, CS_A, CS_B, CK_T, CK_C,
    RESET_N.
2   DQ, DM and DQS pins are fixed apart from the two swaps      PG313, "LPDDR4/4X Pin Rules"
    in rules 3 and 4.
3   DQ bits within a byte can be swapped.                       PG313, "LPDDR4/4X Pin Rules",
                                                                Table 1
4   Bytes can swap between the x16 halves of one channel        PG313, "LPDDR4/4X Pin Rules",
    (DQ[7:0] with DQ[15:8]); the DQS and DM go with their       Table 2
    byte. A DQS pair swaps only with a DQS pair and a DM only
    with a DM. Channel A (DQ[15:0]) must not swap with
    channel B (DQ[31:16]).
5   Memory controller channel 0 must not swap with channel 1.   PG313, "LPDDR4/4X Pin Rules"
6   The DQ mapping to the memory is one to one by name:         PG313, "LPDDR4/4X Pin Rules"
    LPDDR4_DQ_A[0] to DQ0 of channel A, through
    LPDDR4_DQ_B[15] to DQ15 of channel B.
7   A byte occupies one nibble pair (N0/N1, N2/N3, N4/N5 or     PG313, Tables 1 and 2
    N6/N7) of one bank: DQS_T and DQS_C on P0 and P1 of one
    nibble, DMI on P0 of the other, the eight DQ on P2 to P5
    of both. P0 and P1 of either nibble cannot swap with a DQ.
    In Tables 1 and 2, P1 of the DMI nibble carries CS_B or is
    NC.
8   IO_VR_700 connects to a 240 ohm resistor pulled up to the   PG313, "LPDDR4/4X Pin Rules"
    bank's VCCO.
9   Each DDRMC needs one differential system clock (sys_clk).   PG313, "LPDDR4/4X Pin Rules"
10  The sys_clk nibble holds the system clock pair, RESET_n     PG313, "Pin Efficient 1x32
    and ALERT_n.                                                Component Interface
                                                                (Non-Flipped)"
11  A single channel interface always uses the Optimum          PG313, "Single Channel
    pinout, which supports single or dual rank, and cannot      LPDDR4/4X Interfaces"
    select the pin efficient option.
12  Single channel 32-bit, non-flipped nibble use: first bank   PG313, "Single Channel
    N0, N1 DQ B; N2, N3 DQ A; N8 sys_clk; N4, N5 AC B; N6, N7   LPDDR4/4X Interfaces",
    AC A. Second bank N0, N1 DQ B; N4, N5 DQ A. The rest is     Figure 2
    free.
13  Standard dual channel 2x32, non-flipped: channel 0 as       PG313, "Dual Channel
    rule 12; second bank N2, N3 DQ CH1 B and N6, N7 DQ CH1 A;   LPDDR4/4X Interfaces",
    third bank N0, N1 AC CH1 A, N2, N3 DQ CH1 A, N4, N5 AC      Figure 2
    CH1 B, N6, N7 DQ CH1 B. A single channel pinout is
    channel 0 of this one.
14  Pin efficient 2x32, non-flipped, single rank only: first    PG313, "Dual Channel
    bank N0 to N3 DQ CH0 B, N8 AC CH0, N4 to N7 DQ CH0 A;       LPDDR4/4X Interfaces",
    second bank N0, N1 DQ CH1 A, N2, N3 DQ CH1 B, N8 AC CH1,    Figure 3
    N4, N5 DQ CH1 A, N6, N7 DQ CH1 B; third bank N8 sys_clk.
15  The pins of an interface can be reversed in the triplet     Tutorial, Appendix B
    of banks (the flipped pinout).
16  LPDDR4 and LPDDR4X pinouts are identical; the interface is  Tutorial, Appendix B
    x32 only; two ranks are supported for dual-die devices.
17  The pin file's "DDRMC Only" column: YES means DDR memory    AM013, "About ASCII Package
    only, YES_PLUS_GC adds clock management access, NO means    Files"
    full I/O logic access. NO does not exclude DDR use.
18  "All pins swaps must be captured in the design's XDC and    PG313, "LPDDR4/4X Pin Rules"
    validated before generating hardware." This kit exports
    no XDC and does not check Vivado legality; that
    validation is the designer's step.
==  ==========================================================  ==============================

Inferred from the boards
------------------------

The documents place most command, address, clock, reset and sys_clk pins
only to the nibble. The positions below are where the boards that use a
layout agree, and the kit encodes them on that basis. VEK280 uses the pin
efficient layout on all three of its triplets, M0 and M1 non-flipped and M2
flipped; every other board interface uses the standard layout, flipped.

The kit offers the flipped layout, :py:data:`OPTIMUM_X32_FLIPPED`, so each
of its fixed positions, and every DQS_T, DQS_C and DMI position, is where
channel 0 of VMK180, VCK190 and VPK120 puts it, pin for pin
(``test_standard_channel0_matches_the_kit_layout_pin_for_pin``). The kit
encodes the layout as the mirror of the non-flipped
:py:data:`OPTIMUM_X32` (see :py:meth:`Pos.mirrored`); that test is what
ties it to the boards. The non-flipped positions are the other way round:
23 of :py:data:`OPTIMUM_X32`'s 25 fixed positions (all but CS0_B and CS1_B,
which PG313 Tables 1 and 2 print) and the DQS_T, DQS_C and DMI positions of
byte slot 2 are mirrors of flipped board layouts, which no board carries
and no AMD document prints. Either way, the chosen assignment is validated
in Vivado (the Tutorial's "Obtaining Versal Memory Pinouts in Vivado" and
"Modifying XDC Pinouts and DRC Checking"; rule 18).

- Flip as a mirror: bank ``b`` to ``2 - b``, nibble ``n`` to ``7 - n`` (N8
  stays), pin kept. The nibble mirror is what PG313's figures "Nibble
  Utilization for 1x32 Component Interface (Non-Flipped)" and "(Flipped)"
  show. That the pin index is kept is from the boards: VEK280's flipped M2
  interfaces, mirrored, put every non-DQ pin at the pin index of its
  non-flipped M0 counterpart (lpddr4_5 against lpddr4_1, lpddr4_4 against
  lpddr4_0; ``test_vek280_flipped_triplet_mirrors_an_unflipped_one``).
  Every board interface, mirrored, matches rules 7 and 12 to 14 and the
  pin positions PG313 Tables 1 and 2 print. VMK180, VCK190, VPK120,
  VEK280.
- Pin positions of CA, CK and CKE of both channels, CS0_A, RESET_N, and
  the sys_clk pair (``fixed``): channel 0 of VMK180, VCK190 and VPK120 all
  agree. VEK280 uses the pin efficient pinout (rule
  14), a different documented configuration, and has no say.
- Byte slot 2, second bank: rule 12 puts channel B's byte on N0 and N1
  (N7 and N6 flipped); which nibble carries DQS and which DMI is from
  channel 0 of VMK180, VCK190 and VPK120.
- A command or address pin may sit on P1 of a DMI nibble: VEK280's pin
  efficient interfaces put CA bits of channel A there (rule 14 gives each
  controller channel one AC nibble, N8). :py:func:`nibble_violations`
  accepts it; the kit's layouts use it only for CS0_B and CS1_B, as
  Tables 1 and 2 print.
- CS1_A position: VMK180 and VPK120 agree; VCK190 is single rank and has no
  CS1. CS1_B is PG313 Table 2's MxP19 in the non-flipped layout; flipped,
  it is MxP133, where VMK180 and VPK120 put it.
- One CKE per channel on the controller side, a judgement the person
  confirms. What each source says:

  - PG313 "LPDDR4/4X Pin Rules" names the controller pins ``CKE_A`` and
    ``CKE_B``, with no rank index.
  - UG863 v1.12 "Timing Constraint Rules for LPDDR4/4x Signals", Table 1,
    lists ``CKE0_A`` and ``CKE1_A`` (and the ``_B`` pair) under the pin
    pair set "Adaptive SoC to LPDDR4/4x Device", CKE1 marked dual rank only.
    That reads as a second controller CKE per channel for dual rank.
  - UG863 "Signals and Connections for LPDDR4/4x Interfaces" lists CKE0 and
    CKE1 (dual rank only) as memory signals, each terminated 160 ohm.
  - Every board file maps one controller pin to ``CKE_A`` and one to
    ``CKE_B``, including the dual-rank VMK180 and VPK120, which map two CS
    pins per channel. The VCK190 constraints name ``cke_a[0]``, indexed.

  The kit follows the boards: both memory CKE balls of a channel join the
  controller's one CKE. If the controller drives a CKE1, this is wrong and
  the offer needs a second CKE pin per channel, whose position no source in
  hand gives.

What the kit offers
-------------------

:py:data:`OPTIMUM_X32_FLIPPED` is rule 12 taken to pin level and flipped
(rule 15): a single channel x32 on the third and second banks of the
triplet (VP1002 banks 702 and 701), the layout VMK180, VCK190 and VPK120
use for channel 0. Its free choices are rule 4 (which of its channel's two
byte slots each byte takes) and rule 3 (any order of a byte's eight DQ
within its slot): ``2 * 2 * factorial(8) ** 4`` assignments,
:py:func:`assignment_count`.

Not offered, though documented: the non-flipped pinout
(:py:data:`OPTIMUM_X32`, banks 700 and 701), dual channel, and pin
efficient (rule 14, single rank only; the kit's memory is dual rank).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from math import factorial

TRIPLET_BANKS = 3
BANK_NIBBLES = 9
NIBBLE_PINS = 6
SYS_CLK_NIBBLE = 8


@dataclass(frozen=True, order=True)
class Pos:
    """A triplet-relative pin position."""

    bank: int
    "0, 1 or 2 within the triplet"

    nibble: int
    "0 to 8"

    pin: int
    "0 to 5"

    def __post_init__(self) -> None:
        if not (
            0 <= self.bank < TRIPLET_BANKS
            and 0 <= self.nibble < BANK_NIBBLES
            and 0 <= self.pin < NIBBLE_PINS
        ):
            raise ValueError(f"not a triplet position: {self}")

    @property
    def index(self) -> int:
        """The ``MxP`` number of this position in the pin file."""
        return (self.bank * BANK_NIBBLES + self.nibble) * NIBBLE_PINS + self.pin

    def mirrored(self) -> Pos:
        """This position in the flipped pinout (rule 15, mirror inferred)."""
        nibble = self.nibble if self.nibble == SYS_CLK_NIBBLE else 7 - self.nibble
        return Pos(TRIPLET_BANKS - 1 - self.bank, nibble, self.pin)

    @staticmethod
    def parse(text: str) -> Pos:
        """Parse three digits: bank, nibble, pin (``"130"`` is bank 1 N3 P0)."""
        if len(text) != 3 or not text.isdigit():
            raise ValueError(f"expected three digits, got {text!r}")
        return Pos(int(text[0]), int(text[1]), int(text[2]))


class Channel(Enum):
    """An LPDDR4 x16 channel of the memory."""

    A = "A"
    B = "B"


def byte_channel(byte: int) -> Channel:
    """The channel of byte 0 to 3 (rule 4: bytes 0 and 1 are channel A)."""
    if not 0 <= byte < 4:
        raise ValueError(f"byte must be 0 to 3, got {byte}")
    return Channel.A if byte < 2 else Channel.B


@dataclass(frozen=True)
class ByteSlot:
    """The nibble pair one byte occupies (rule 7)."""

    channel: Channel
    bank: int
    dqs_nibble: int
    "Nibble with DQS_T on P0 and DQS_C on P1"

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
        nibble. Any order of a byte's DQ over them is allowed (rule 3)."""
        return tuple(
            Pos(self.bank, n, p)
            for n in (self.dqs_nibble, self.dmi_nibble)
            for p in range(2, NIBBLE_PINS)
        )

    def mirrored(self) -> ByteSlot:
        return ByteSlot(
            self.channel, TRIPLET_BANKS - 1 - self.bank, 7 - self.dqs_nibble
        )


@dataclass(frozen=True)
class NibbleLayout:
    """A documented base layout at nibble level, for one x32 interface."""

    name: str
    pairs: Mapping[Channel, tuple[tuple[int, int], ...]]
    "Per channel, the (bank, even nibble) of each DQ nibble pair"

    ac: Mapping[Channel, frozenset[tuple[int, int]]]
    "Per channel, the (bank, nibble) of each AC nibble"

    sys_clk_bank: int

    def mirrored(self) -> NibbleLayout:
        def pair(bank: int, even: int) -> tuple[int, int]:
            return (TRIPLET_BANKS - 1 - bank, 6 - even)

        def nib(bank: int, n: int) -> tuple[int, int]:
            m = Pos(bank, n, 0).mirrored()
            return (m.bank, m.nibble)

        return NibbleLayout(
            name=f"{self.name}, flipped",
            pairs={c: tuple(pair(*p) for p in ps) for c, ps in self.pairs.items()},
            ac={c: frozenset(nib(*n) for n in ns) for c, ns in self.ac.items()},
            sys_clk_bank=TRIPLET_BANKS - 1 - self.sys_clk_bank,
        )


A, B = Channel.A, Channel.B

OPTIMUM_CH0 = NibbleLayout(
    name="Optimum x32, channel 0 (PG313 single channel Figure 2)",
    pairs={A: ((0, 2), (1, 4)), B: ((0, 0), (1, 0))},
    ac={A: frozenset({(0, 6), (0, 7)}), B: frozenset({(0, 4), (0, 5)})},
    sys_clk_bank=0,
)
"Rules 12 and 13, channel 0."

OPTIMUM_CH1 = NibbleLayout(
    name="Optimum 2x32, channel 1 (PG313 dual channel Figure 2)",
    pairs={A: ((1, 6), (2, 2)), B: ((1, 2), (2, 6))},
    ac={A: frozenset({(2, 0), (2, 1)}), B: frozenset({(2, 4), (2, 5)})},
    sys_clk_bank=0,
)
"Rule 13, channel 1."

PIN_EFFICIENT_CH0 = NibbleLayout(
    name="Pin efficient 2x32, channel 0 (PG313 dual channel Figure 3)",
    pairs={A: ((0, 4), (0, 6)), B: ((0, 0), (0, 2))},
    ac={A: frozenset({(0, 8)}), B: frozenset({(0, 8)})},
    sys_clk_bank=2,
)
"Rule 14, channel 0. Its AC nibble serves both memory channels."

PIN_EFFICIENT_CH1 = NibbleLayout(
    name="Pin efficient 2x32, channel 1 (PG313 dual channel Figure 3)",
    pairs={A: ((1, 0), (1, 4)), B: ((1, 2), (1, 6))},
    ac={A: frozenset({(1, 8)}), B: frozenset({(1, 8)})},
    sys_clk_bank=2,
)
"Rule 14, channel 1."


def _ac_name_channel(name: str) -> Channel | None:
    """Channel of a command, address or clock signal name, else None."""
    if name.startswith(("CA", "CK_", "CKE_", "CS")) and name[-2:] in ("_A", "_B"):
        return Channel(name[-1])
    return None


def nibble_violations(pinout: Mapping[str, Pos], layout: NibbleLayout) -> list[str]:
    """Check a pinout against rules 1 to 7, 10 and one nibble layout.

    ``pinout`` maps canonical names to positions: ``DQ0`` to ``DQ31``,
    ``DQS0_T``/``DQS0_C`` to ``DQS3_*``, ``DMI0`` to ``DMI3``, ``CA0_A`` to
    ``CA5_B``, ``CK_T_A``, ``CK_C_A``, ``CKE_A``, ``CS0_A``, ``CS1_A`` (and
    ``_B``), ``RESET_N``, and optionally ``SYS_CLK_P``/``SYS_CLK_N``. Returns
    one line per broken rule; an empty list is a member.
    """
    bad: list[str] = []
    seen: dict[Pos, str] = {}
    for name, pos in pinout.items():
        if pos in seen:
            bad.append(f"{name} and {seen[pos]} share {pos}")
        seen[pos] = name

    dmi_nibbles: set[tuple[int, int]] = set()
    used_pairs: set[tuple[int, int]] = set()
    for byte in range(4):
        t, c, m = (pinout[f"DQS{byte}_T"], pinout[f"DQS{byte}_C"], pinout[f"DMI{byte}"])
        if (t.pin, c.pin) != (0, 1) or (t.bank, t.nibble) != (c.bank, c.nibble):
            bad.append(f"byte {byte}: DQS not on P0/P1 of one nibble ({t}, {c})")
            continue
        slot = ByteSlot(byte_channel(byte), t.bank, t.nibble)
        if m != slot.dmi:
            bad.append(f"byte {byte}: DMI at {m}, expected {slot.dmi}")
        dq = {pinout[f"DQ{8 * byte + i}"] for i in range(8)}
        if dq != set(slot.dq):
            bad.append(f"byte {byte}: DQ not on P2 to P5 of its nibble pair")
        pair = (t.bank, t.nibble & ~1)
        if pair not in layout.pairs[slot.channel]:
            bad.append(
                f"byte {byte}: nibble pair {pair} is not a channel "
                f"{slot.channel.value} pair of {layout.name}"
            )
        if pair in used_pairs:
            bad.append(f"byte {byte}: nibble pair {pair} already used")
        used_pairs.add(pair)
        dmi_nibbles.add((slot.bank, slot.dmi_nibble))

    for name, pos in pinout.items():
        ch = _ac_name_channel(name)
        if ch is not None:
            in_ac = (pos.bank, pos.nibble) in layout.ac[ch]
            on_dmi_p1 = pos.pin == 1 and (pos.bank, pos.nibble) in dmi_nibbles
            if not (in_ac or on_dmi_p1):
                bad.append(f"{name} at {pos}: not in a channel {ch.value} AC nibble")
        if name in ("RESET_N", "SYS_CLK_P", "SYS_CLK_N"):
            if (pos.bank, pos.nibble) != (layout.sys_clk_bank, SYS_CLK_NIBBLE):
                bad.append(f"{name} at {pos}: not in the sys_clk nibble")
    for name, pin in (("SYS_CLK_P", 0), ("SYS_CLK_N", 1)):
        if name in pinout and pinout[name].pin != pin:
            bad.append(f"{name} at {pinout[name]}: expected P{pin}")
    return bad


@dataclass(frozen=True)
class PinLayout:
    """A base layout at pin level: the fixed pins and the byte slots."""

    nibbles: NibbleLayout
    slots: tuple[ByteSlot, ...]
    "Byte slots; slot ``k`` holds byte ``k`` before any byte swap"

    fixed: Mapping[str, Pos] = field(default_factory=dict)

    def mirrored(self) -> PinLayout:
        return PinLayout(
            nibbles=self.nibbles.mirrored(),
            slots=tuple(s.mirrored() for s in self.slots),
            fixed={k: v.mirrored() for k, v in self.fixed.items()},
        )

    def byte_orders(self) -> list[tuple[int, int, int, int]]:
        """Every allowed byte-to-slot assignment (rule 4): entry ``k`` is the
        slot index byte ``k`` takes."""
        a = [i for i, s in enumerate(self.slots) if s.channel is Channel.A]
        b = [i for i, s in enumerate(self.slots) if s.channel is Channel.B]
        return [
            (a0, a1, b0, b1)
            for a0, a1 in (tuple(a), tuple(reversed(a)))
            for b0, b1 in (tuple(b), tuple(reversed(b)))
        ]

    def violations(self, pinout: Mapping[str, Pos]) -> list[str]:
        """Check a pinout against this layout at pin level, plus every rule
        :py:func:`nibble_violations` checks. Fixed names absent from
        ``pinout`` (CS1 on a single-rank board) are skipped."""
        bad = nibble_violations(pinout, self.nibbles)
        for name, pos in self.fixed.items():
            if name in pinout and pinout[name] != pos:
                bad.append(f"{name} at {pinout[name]}, fixed at {pos}")
        slot_of = {s.dqs_t: i for i, s in enumerate(self.slots)}
        order = tuple(slot_of.get(pinout[f"DQS{k}_T"], -1) for k in range(4))
        if order not in self.byte_orders():
            bad.append(f"byte to slot order {order} is not an allowed byte swap")
        return bad


OPTIMUM_X32 = PinLayout(
    nibbles=OPTIMUM_CH0,
    slots=(
        ByteSlot(A, 1, 4),  # byte 0: PG313 Table 2, MxP78 to MxP89
        ByteSlot(A, 0, 2),  # byte 1: PG313 Table 2, MxP12 to MxP23
        ByteSlot(B, 1, 0),  # byte 2: rule 12 nibbles; DQS on N0 from the boards
        ByteSlot(B, 0, 1),  # byte 3: PG313 Table 1, MxP0 to MxP11
    ),
    fixed={
        # First bank N7 and N6: channel A AC (boards)
        "CA2_A": Pos(0, 7, 0),
        "CS1_A": Pos(0, 7, 1),
        "CA1_A": Pos(0, 7, 2),
        "CA0_A": Pos(0, 7, 3),
        "CS0_A": Pos(0, 7, 4),
        "CA3_A": Pos(0, 7, 5),
        "CK_T_A": Pos(0, 6, 0),
        "CK_C_A": Pos(0, 6, 1),
        "CA4_A": Pos(0, 6, 2),
        "CA5_A": Pos(0, 6, 3),
        "CKE_A": Pos(0, 6, 4),
        # First bank N5 and N4: channel B AC (boards)
        "CA0_B": Pos(0, 5, 2),
        "CA3_B": Pos(0, 5, 4),
        "CA2_B": Pos(0, 5, 5),
        "CK_T_B": Pos(0, 4, 0),
        "CK_C_B": Pos(0, 4, 1),
        "CA5_B": Pos(0, 4, 2),
        "CA4_B": Pos(0, 4, 3),
        "CKE_B": Pos(0, 4, 4),
        "CA1_B": Pos(0, 4, 5),
        # P1 of the DMI nibbles: PG313 Table 1 (MxP1) and Table 2 (MxP19)
        "CS0_B": Pos(0, 0, 1),
        "CS1_B": Pos(0, 3, 1),
        # First bank N8, the sys_clk nibble (rule 10; pins from the boards)
        "SYS_CLK_P": Pos(0, 8, 0),
        "SYS_CLK_N": Pos(0, 8, 1),
        "RESET_N": Pos(0, 8, 2),
    },
)
"""Rule 12 taken to pin level: single channel x32, non-flipped, on the first
and second banks. Not the kit's layout. 23 of the 25 fixed positions, and
byte slot 2's DQS_T, DQS_C and DMI positions, are inferred by mirroring the
boards."""

OPTIMUM_X32_FLIPPED = OPTIMUM_X32.mirrored()
"""The kit's layout: :py:data:`OPTIMUM_X32` flipped (rule 15), on the third
and second banks. Every position is where channel 0 of VMK180, VCK190 and
VPK120 puts it (VCK190, single rank, has no CS1). Slot ``k`` still holds byte ``k`` before any byte swap."""


def assignment_count(layout: PinLayout = OPTIMUM_X32_FLIPPED) -> int:
    """Number of distinct pin assignments the layout allows (rules 3 and 4)."""
    return len(layout.byte_orders()) * factorial(8) ** len(layout.slots)

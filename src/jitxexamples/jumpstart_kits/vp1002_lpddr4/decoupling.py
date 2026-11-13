"""Decoupling for a Micron MT53E1G32D2FW's three supplies and every supply
rail of the VP1002, netted and tied to their balls, for placement in the
layout. Run as LPDDR4, the memory's VDD2 and VDDQ share one 1.1 V net with
the VCCO of XPIO banks 700 to 702 (:py:mod:`.power`); each set still ties
to the balls of the supply it was sized for.

Neither vendor gives a count to cite. Micron's data sheet Rev. I gives no
decoupling guidance for VDD1, VDD2 or VDDQ. AMD UG863 v1.12, "Recommended
Decoupling Capacitor Quantities for Versal Devices", says the quantities "can
be obtained via the PDM tool" (AMD Power Design Manager) from the design's own
resource use, and DS959 v1.8 Table 1 defers to the same tool. The memory's
set is therefore sized to TI's LPDDR4 layout guideline, SPRAD66B, and each
FPGA set is trimmed from a published reference board's set for the same rail
of another Versal device.

Every capacitor is netted and tied to one ball of its rail, picked by the
ball's name: each rail's set is spread over that rail's balls
in (row, column) order, and each XPIO bank's set over its own bank's VCCO
balls (:py:func:`ball_grid`). A capacitor below 10 uF
(:py:data:`BULK_CAPACITANCE`) is tied by a ShortTrace, for placement at its
ball; a bulk capacitor, 10 uF and up, by a plain net, since it sits outside
the ball field on its own via to the plane and no route runs back to a
ball. Nothing here places a capacitor: placing them,
under or beside each package, is a layout step, and SPRAD66B's distance and
via rules (Sources) apply there.

A layout can say, before any capacitor is created, how it treats some of an
FPGA rail's set (:py:class:`RailLayout`, by rail name, :py:func:`fpga_sets`):
a capacitor below 10 uF it places away from its ball, tied by a plain net,
and a capacitor it leaves out of the design. The balls are spread over the
whole set either way, so each capacitor kept ties to the same ball, and each
keeps its place in the set as its key in the FPGA sets' ``caps``, so
``caps[2]`` is the set's third capacitor whatever is left out.

Sources
-------

- TI SK-AM62A-LP starter kit, https://www.ti.com/tool/SK-AM62A-LP, design
  files SPRCAM0: schematic PROC135A1 rev A1 (2025-07-24), sheet 16 of 44 "SOC
  LPDDR4 INTERFACE", block "LPDDR4 POWER DECAPS"; its BOM
  ``PROC135A1_BOM_With_Design_Updates..Notes_V1.0.xlsx``; and its assembly
  drawings. U26 there is an MT53E1G32D2FW-046 AUT:B, the same Micron part
  number as this design's memory in another temperature grade, in the same
  200-ball package. Its 10 uF and 0.1 uF memory capacitors are the parts
  this design's memory set queries for. The board's 48 memory capacitors
  are not copied: the set here is smaller (Approximations).
- TI SPRAD66B, *AM62Ax, AM62Px, AM62Dx LPDDR4 Board Design and Layout
  Guidelines*, February 2023, revised December 2024,
  https://www.ti.com/lit/pdf/sprad66: Table 1-3 "High-Speed Bypass
  Capacitors", per DDR device at least 12 capacitors and at least 0.85 uF in
  total, 0201 typical and 0402 at most, at most 150 mil from the device.
- Trenz Electronic TE0950 schematic SCH-TE0950-03-MAKE21C, rev 03,
  2023-12-19,
  https://shop.trenz-electronic.de/trenzdownloads/Trenz_Electronic/Development_Boards/TE0950/REV03/Documents/SCH-TE0950-03-MAKE21C.PDF,
  an XCVM1102 board: page 7 "PMC/MIO" (VCCO_500 to VCCO_503), pages 8 to 10
  (V_XPIO_700 to V_XPIO_702), page 12 "V_GTY" (GTYP_AVCC, GTYP_AVCC_AUX,
  GTYP_AVTT) and page 13 "V_Power" (VCCINT, VCC_SOC, VCC_IO, VCC_RAM, VCCAUX,
  VCCAUX_PMC, VCCAUX_SMON, VCC_PMC, VCC_PSLP, VCC_PSFP). The schematic gives
  value, voltage and dielectric, no case.
- AMD AM006 v1.5, 2025-06-03,
  https://docs.amd.com/r/en-US/am006-versal-sysmon, Figure 1 "SYSMON Pinout
  Requirements": 470 nF and 100 nF on VCCAUX_SMON, the pair TE0950 page 13
  also uses (C108, C109).
- Rated voltage: Eric Bogatin, "Seven Habits of Successful 2-Layer Board
  Designers", Signal Integrity Journal, 2019-04-23,
  https://www.signalintegrityjournal.com/blogs/12-fundamentals/post/1207-seven-habits-of-successful-2-layer-board-designers,
  habit 5: "a voltage rating at least 2x the intended rail application".
  Applied here to each rail's maximum (:py:mod:`.power`), the stricter
  reading.

Approximations
--------------

- The memory set is a choice sized to SPRAD66B Table 1-3, at least 12
  bypass capacitors and 0.85 uF per DDR device: twelve 0.1 uF (1.2 uF),
  split across the rails by supply ball count (20 VDDQ, 24 VDD2 and 8 VDD1
  balls give five, five and two), and one 10 uF bulk capacitor per rail.
  SK-AM62A-LP places 48, with 1000 pF and 0.01 uF parts as well; a set that
  size takes about a hundred vias under the package (SPRAD66B asks two per
  capacitor), in the field the byte lanes escape through.
- The FPGA sets are trimmed from TE0950's, for an XCVM1102, a smaller device
  than the VP1002 with fewer balls on most rails. The trim is this design's
  choice, one rule applied to each rail's TE0950 set. Drop every part of
  100 uF and up: such parts serve a regulator's control loop and belong at
  its output, and this design models no regulators yet (each rail is a net
  a regulator can join, :py:mod:`.power`). Of the parts of 10 uF and up
  that are left, keep one, the largest, as the rail's bulk. Halve the count
  of each smaller value, rounding up, so every value below 10 uF that
  TE0950 uses on the rail stays, in fewer parts competing for the room
  near the balls. Two kinds of set are kept whole: VCCAUX_SMON's 470 nF and
  100 nF, the pair AM006 Figure 1 asks for, and each XPIO bank's one 47 uF
  and two 4.7 uF, since the bank's VCCO carries the memory interface's I/O
  switching. TE0950 has
  no GTM transceivers and no VCCINT_GT: each GTM rail (L and RN sides alike)
  takes the trimmed set of the GTYP rail of the same function, and
  VCCINT_GT_L and VCCINT_GT_R, the GTM primary supply in DS959 Table 1, take
  the trimmed GTYP_AVCC set, the transceiver primary supply nearest it in
  function. The VP1002's GTY_*_RS rails take the trimmed GTYP sets too.
  VCC_IO and VCC_SOC share a net (DS959 note 8) and carry both their trimmed
  TE0950 sets; VCCAUX_SMON and VCCAUX_PMC share one too (note 4) and carry
  the trimmed VCCAUX_PMC set and the SMON pair.
- Parts: each kind is queried by value, case, dielectric and rated voltage,
  so any catalogue part that meets them serves. Where the source gives no
  case, the case is the smallest the example catalogue
  carries for the value and the rating twice the rail maximum needs.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from jitx.component import Component
from jitx.container import Container
from jitx.inspect import visit
from jitx.landpattern import Pad, PadMapping
from jitx.net import Net, Port, ShortTrace
from jitx.proxy import origin
from jitx.refpath import Item
from jitx.units import F, V
from jitxlib.parts import AtLeast, Capacitor

from jitxexamples.components.memories.MT53E1G32D2FW_046_WT_B import (
    MT53E1G32D2FW_046_WT_B,
)

from ..js1_stackup_components.versal_fpga.tools.generate_pinout import ball_to_rc
from .circuit import VP1002LPDDR4
from .power import (
    AUX_MAX,
    CORE_MAX,
    GT_AVTT_MAX,
    GTM_AVCC_MAX,
    GTY_AVCC_MAX,
    PSIO_VCCO_MAX,
    VCCO_MAX,
    VDD1_MAX,
    VDD2_MAX,
    VDDQ_MAX,
)

BULK_CAPACITANCE = 10e-6
"""Farads. A capacitor of this value or more is bulk: tied to its ball by a
plain net, not a ShortTrace (module docstring)."""

RATED_VOLTAGE_FACTOR = 2.0
"""Rated DC voltage at least this times the rail maximum (Bogatin 2019,
habit 5)."""


@dataclass(frozen=True)
class CapacitorKind:
    """One value of a reference board's decoupling set."""

    capacitance: float
    "Farads."
    case: str
    dielectric: str
    "Temperature coefficient code."


C_10U = CapacitorKind(10e-6, "0402", "X5R")
"""10 uF 0402 X5R. SK-AM62A-LP BOM: Murata GRM155R61A106ME11D (10 V, 20%,
X5R, 0402)."""

C_100N = CapacitorKind(100e-9, "0201", "X5R")
"""0.1 uF 0201 X5R. SK-AM62A-LP BOM: Murata GRM033R61C104KE14D (16 V, 10%,
X5R, 0201); TE0950 C109: 100 nF, 6.3 V, X5R. The query asks for twice the
rail maximum, not the board's rating."""

C_470N = CapacitorKind(470e-9, "0402", "X5R")
"""470 nF X5R. TE0950: 470 nF, 6.3 V, X5R."""

C_4U7 = CapacitorKind(4.7e-6, "0402", "X5R")
"""4.7 uF X5R. TE0950: 4.7 uF, 6.3 V, X5R."""

C_22U = CapacitorKind(22e-6, "0603", "X5R")
"""22 uF X5R. TE0950: 22 uF, 25 V, X5R."""

C_47U = CapacitorKind(47e-6, "0805", "X5R")
"""47 uF X5R. TE0950: 47 uF, 6.3 V, X5R."""

MEMORY_VDDQ_SET = (C_10U,) + (C_100N,) * 5
"""VDDQ, 20 balls: one 10 uF bulk and five of the memory's twelve 0.1 uF
(Approximations)."""

MEMORY_VDD2_SET = (C_10U,) + (C_100N,) * 5
"""VDD2, 24 balls: one 10 uF bulk and five of the twelve 0.1 uF."""

MEMORY_VDD1_SET = (C_10U,) + (C_100N,) * 2
"""VDD1, 8 balls: one 10 uF bulk and two of the twelve 0.1 uF."""

XPIO_BANK_SET = (C_4U7, C_4U7, C_47U)
"""TE0950 page 8, bank 700: C20, C21 (4.7 uF) and C19 (47 uF); page 9, bank
701: C23, C24 and C22; page 10, bank 702: C29, C30 and C28."""

VCCINT_SET = (C_47U,) + (C_4U7,) * 3 + (C_470N,) * 4
"""TE0950 page 13, VCCINT, trimmed (Approximations): one of its three 47 uF
(C81, C82, C83), three of its six 4.7 uF (C68, C69, C70, C76, C77, C78) and
four of its eight 470 nF (C87, C88, C89, C90, C94, C95, C96, C97). Its two
330 uF (C66, C67) and three 100 uF (C71, C72, C73) are dropped."""

VCC_SOC_SET = (C_47U, C_4U7)
"""TE0950 page 13, VCC_SOC, trimmed: C84 (47 uF) and one of C85, C86
(4.7 uF). Its 330 uF (C74) and 100 uF (C75) are dropped."""

VCC_IO_SET = (C_47U, C_4U7)
"""TE0950 page 13, VCC_IO, trimmed: C104 (47 uF) and one of C105, C106
(4.7 uF)."""

VCC_RAM_SET = (C_47U,)
"""TE0950 page 13, VCC_RAM: C107 (47 uF), its whole set."""

VCCAUX_SET = (C_47U, C_4U7)
"""TE0950 page 13, VCCAUX, trimmed: C98 (47 uF) and one of C99, C100
(4.7 uF)."""

VCCAUX_PMC_SET = (C_47U, C_4U7)
"""TE0950 page 13, VCCAUX_PMC: C79 (47 uF) and C80 (4.7 uF), its whole set;
half of one 4.7 uF rounds up to one."""

VCCAUX_SMON_SET = (C_470N, C_100N)
"""TE0950 page 13, VCCAUX_SMON: C108 (470 nF), C109 (100 nF); AM006 v1.5
Figure 1: 470 nF and 100 nF. Kept whole (Approximations)."""

VCC_PMC_SET = (C_47U, C_4U7)
"""TE0950 page 13, VCC_PMC, trimmed: C63 (47 uF) and one of C64, C65
(4.7 uF)."""

VCC_PSLP_SET = (C_47U, C_4U7)
"""TE0950 page 13, VCC_PSLP, trimmed: C91 (47 uF) and one of C92, C93
(4.7 uF)."""

VCC_PSFP_SET = (C_47U, C_4U7)
"""TE0950 page 13, VCC_PSFP, trimmed: C101 (47 uF) and one of C102, C103
(4.7 uF)."""

VCCO_500_SET = (C_47U, C_4U7)
"""TE0950 page 7, VCCO_500, trimmed: C5 (47 uF) and one of C6, C7
(4.7 uF)."""

VCCO_501_SET = (C_4U7,)
"""TE0950 page 7, VCCO_501, trimmed: one of C12, C13 (4.7 uF). The set has
no bulk part."""

VCCO_502_SET = (C_47U, C_4U7)
"""TE0950 page 7, VCCO_502, trimmed: C15 (47 uF) and one of C16, C17
(4.7 uF)."""

VCCO_503_SET = (C_47U, C_4U7)
"""TE0950 page 7, VCCO_503, trimmed: C8 (47 uF) and one of C9, C10
(4.7 uF)."""

GT_AVCC_SET = (C_47U, C_4U7, C_470N)
"""TE0950 page 12, GTYP_AVCC, trimmed: C41 (47 uF), one of C43, C44
(4.7 uF) and one of C45, C46 (470 nF). Its 100 uF (C40) is dropped, and its
22 uF (C42) gives way to the larger 47 uF."""

GT_AVCCAUX_SET = (C_22U, C_470N)
"""TE0950 page 12, GTYP_AVCC_AUX, trimmed: C37 (22 uF) and one of C38, C39
(470 nF)."""

GT_AVTT_SET = (C_47U, C_4U7, C_470N)
"""TE0950 page 12, GTYP_AVTT, trimmed: C47 (47 uF), one of C49, C50
(4.7 uF) and one of C51, C52 (470 nF). Its 22 uF (C48) gives way to the
larger 47 uF."""


def make_capacitor(kind: CapacitorKind, rail_max: float) -> Capacitor:
    """The catalogue capacitor for ``kind`` on a rail whose maximum is
    ``rail_max`` volts."""
    return Capacitor(
        capacitance=kind.capacitance * F,
        case=kind.case,
        temperature_coefficient_code=kind.dielectric,
        rated_voltage_dc=AtLeast(RATED_VOLTAGE_FACTOR * rail_max * V),
    )


type GridPosition = tuple[int, int]
"Zero-indexed ``(row, column)`` of a ball in its package's grid."


def ball_grid(component: Component) -> dict[Port, GridPosition]:
    """The grid position of the ball each single-ball port of a BGA part maps
    to, read from the ball's name with :py:func:`ball_to_rc` (JEDEC row
    letters, so ``"AB34"`` is row 21, column 33).

    The name is the pad's place in the BGA landpattern: pad
    ``landpattern.AB[34]`` is ball AB34. A port mapped to several balls (the
    memory's DNU and NC) is left out. Positions come from names alone, so the
    part need not be placed.
    """
    names: dict[int, str] = {}
    for trace, pad in visit(component, Pad):
        *_, row, column = trace.path
        number = column.value if isinstance(column, Item) else column
        names[id(origin(pad))] = f"{row}{number}"
    out: dict[Port, GridPosition] = {}
    for _, mapping in visit(component, PadMapping, opaque=()):
        for port, pads in mapping.items():
            group = [pads] if isinstance(pads, Pad) else list(pads)
            if len(group) == 1:
                out[port] = ball_to_rc(names[id(origin(group[0]))])
    return out


@dataclass(frozen=True)
class RailLayout:
    """How a layout treats some of one rail's set, each capacitor named by
    its place in the set: ``ring``, capacitors below 10 uF placed away from
    their ball, tied to it by a plain net rather than a ShortTrace; ``omit``,
    capacitors not created at all. The default treats none so."""

    ring: frozenset[int] = frozenset()
    omit: frozenset[int] = frozenset()


def _build(
    kinds: Sequence[CapacitorKind],
    rail_max: float,
    balls: Sequence[Port],
    grid: Mapping[Port, GridPosition],
    layout: RailLayout,
) -> tuple[dict[int, Capacitor], list[ShortTrace], list[Net]]:
    """A set's capacitors by their place in the set, less those ``layout``
    omits, each with its ``p1`` tied to its ball: a ShortTrace below
    :py:data:`BULK_CAPACITANCE` unless ``layout`` puts it in the ring, a
    plain net otherwise. The set is spread over ``balls`` whole
    (:py:func:`_spread`) before any is omitted, so each capacitor kept ties
    to the ball it would in the whole set and keeps its place."""
    places = range(len(kinds))
    if not layout.ring <= set(places) or not layout.omit <= set(places):
        raise ValueError(f"a layout names a capacitor the set lacks: {layout}")
    if layout.ring & layout.omit:
        raise ValueError(f"a layout both rings and omits a capacitor: {layout}")
    caps: dict[int, Capacitor] = {}
    short: list[ShortTrace] = []
    bulk: list[Net] = []
    for place, (kind, ball) in enumerate(
        zip(kinds, _spread(balls, len(kinds), grid), strict=True)
    ):
        if place in layout.omit:
            continue
        cap = make_capacitor(kind, rail_max)
        caps[place] = cap
        if kind.capacitance >= BULK_CAPACITANCE or place in layout.ring:
            bulk.append(Net([cap.p1, ball]))
        else:
            short.append(ShortTrace(cap.p1, ball))
    return caps, short, bulk


def _spread(
    balls: Sequence[Port], n: int, grid: Mapping[Port, GridPosition]
) -> list[Port]:
    """``n`` of ``balls`` spread evenly over them in (row, column) order;
    ``grid`` gives each ball's position."""
    ordered = sorted(balls, key=lambda b: grid[b])
    m = len(ordered)
    return [ordered[min(m - 1, int((i + 0.5) * m / n))] for i in range(n)]


class MemoryDecoupling(Container):
    """The memory's VDDQ, VDD2 and VDD1 capacitors, each tied to one ball of
    its rail (:py:func:`_build`), each rail's set spread over its balls in
    (row, column) order."""

    def __init__(self, memory: MT53E1G32D2FW_046_WT_B) -> None:
        grid = ball_grid(memory)
        self.short_traces: list[ShortTrace] = []
        self.bulk_nets: list[Net] = []
        rails = (
            (memory.VDDQ, MEMORY_VDDQ_SET, VDDQ_MAX),
            (memory.VDD2, MEMORY_VDD2_SET, VDD2_MAX),
            (memory.VDD1, MEMORY_VDD1_SET, VDD1_MAX),
        )
        sets: list[list[Capacitor]] = []
        for balls, kinds, rail_max in rails:
            caps, short, bulk = _build(kinds, rail_max, balls, grid, RailLayout())
            sets.append(list(caps.values()))
            self.short_traces += short
            self.bulk_nets += bulk
        self.vddq, self.vdd2, self.vdd1 = sets

    def capacitors(self) -> list[Capacitor]:
        """Every capacitor, for netting their return pads to ground."""
        return [*self.vddq, *self.vdd2, *self.vdd1]


class XpioBankDecoupling(Container):
    """One XPIO bank's VCCO capacitors, :py:data:`XPIO_BANK_SET`, each tied
    to one of the bank's own VCCO balls (:py:func:`_build`), spread over
    them in (row, column) order, less any ``layout`` omits. ``caps`` holds
    each by its place in the set.

    ``grid`` gives each FPGA ball's position (:py:func:`ball_grid`).
    """

    def __init__(
        self,
        balls: Sequence[Port],
        grid: Mapping[Port, GridPosition],
        layout: RailLayout | None = None,
    ) -> None:
        self.caps, self.short_traces, self.bulk_nets = _build(
            XPIO_BANK_SET, VCCO_MAX, balls, grid, layout or RailLayout()
        )

    def capacitors(self) -> list[Capacitor]:
        """Every capacitor, for netting their return pads to ground."""
        return list(self.caps.values())


class FpgaRailDecoupling(Container):
    """One FPGA rail's set, each capacitor tied to one of the rail's balls
    (:py:func:`_build`), the set spread over the balls in (row, column)
    order, less any ``layout`` omits. ``caps`` holds each by its place in
    the set.

    ``grid`` gives each ball's position (:py:func:`ball_grid`).
    """

    def __init__(
        self,
        balls: Sequence[Port],
        grid: Mapping[Port, GridPosition],
        kinds: Sequence[CapacitorKind],
        rail_max: float,
        layout: RailLayout | None = None,
    ) -> None:
        self.caps, self.short_traces, self.bulk_nets = _build(
            kinds, rail_max, balls, grid, layout or RailLayout()
        )

    def capacitors(self) -> list[Capacitor]:
        """Every capacitor, for netting their return pads."""
        return list(self.caps.values())


@dataclass(frozen=True)
class RailSet:
    """An FPGA rail: its name (the FPGA's port name), its balls, its
    reference-board set and its maximum."""

    name: str
    balls: Sequence[Port]
    kinds: Sequence[CapacitorKind]
    rail_max: float
    "V."


def fpga_rail_sets(fpga: VP1002LPDDR4) -> list[RailSet]:
    """Every FPGA supply rail whose capacitors return to the main ground.

    Not here: the XPIO banks, which :py:class:`XpioBankDecoupling` covers;
    VCCAUX_SMON, which returns to GND_SMON (:py:class:`FpgaDecoupling`);
    VCC_BATT and VCC_FUSE, tied to ground (:py:class:`~.power.FpgaStraps`);
    the AVTTRCAL supplies, each tied to its AVTT rail and decoupled by that
    rail's set (:py:class:`~.power.GtCalibration`); and VCCINT_SENSE, a sense
    pin, not a supply.
    """
    f = fpga.fpga
    return [
        RailSet("VCCINT", f.VCCINT, VCCINT_SET, CORE_MAX),
        RailSet("VCC_SOC", f.VCC_SOC, VCC_SOC_SET, CORE_MAX),
        RailSet("VCC_IO", f.VCC_IO, VCC_IO_SET, CORE_MAX),
        RailSet("VCC_RAM", f.VCC_RAM, VCC_RAM_SET, CORE_MAX),
        RailSet("VCCAUX", f.VCCAUX, VCCAUX_SET, AUX_MAX),
        RailSet("VCCAUX_PMC", f.VCCAUX_PMC, VCCAUX_PMC_SET, AUX_MAX),
        RailSet("VCC_PMC", f.VCC_PMC, VCC_PMC_SET, CORE_MAX),
        RailSet("VCC_PSLP", f.VCC_PSLP, VCC_PSLP_SET, CORE_MAX),
        RailSet("VCC_PSFP", f.VCC_PSFP, VCC_PSFP_SET, CORE_MAX),
        RailSet("VCCO_500", f.VCCO_500, VCCO_500_SET, PSIO_VCCO_MAX),
        RailSet("VCCO_501", f.VCCO_501, VCCO_501_SET, PSIO_VCCO_MAX),
        RailSet("VCCO_502", f.VCCO_502, VCCO_502_SET, PSIO_VCCO_MAX),
        RailSet("VCCO_503", f.VCCO_503, VCCO_503_SET, PSIO_VCCO_MAX),
        RailSet("GTY_AVCC_RS", f.GTY_AVCC_RS, GT_AVCC_SET, GTY_AVCC_MAX),
        RailSet("GTY_AVCCAUX_RS", f.GTY_AVCCAUX_RS, GT_AVCCAUX_SET, AUX_MAX),
        RailSet("GTY_AVTT_RS", f.GTY_AVTT_RS, GT_AVTT_SET, GT_AVTT_MAX),
        RailSet("GTM_AVCC_L", f.GTM_AVCC_L, GT_AVCC_SET, GTM_AVCC_MAX),
        RailSet("GTM_AVCC_RN", f.GTM_AVCC_RN, GT_AVCC_SET, GTM_AVCC_MAX),
        RailSet("GTM_AVCCAUX_L", f.GTM_AVCCAUX_L, GT_AVCCAUX_SET, AUX_MAX),
        RailSet("GTM_AVCCAUX_RN", f.GTM_AVCCAUX_RN, GT_AVCCAUX_SET, AUX_MAX),
        RailSet("GTM_AVTT_L", f.GTM_AVTT_L, GT_AVTT_SET, GT_AVTT_MAX),
        RailSet("GTM_AVTT_RN", f.GTM_AVTT_RN, GT_AVTT_SET, GT_AVTT_MAX),
        RailSet("VCCINT_GT_L", f.VCCINT_GT_L, GT_AVCC_SET, CORE_MAX),
        RailSet("VCCINT_GT_R", f.VCCINT_GT_R, GT_AVCC_SET, CORE_MAX),
    ]


XPIO_BANKS = ("VCCO_700", "VCCO_701", "VCCO_702")
"The XPIO banks' VCCO rails, by the FPGA's port names."


def fpga_sets(fpga: VP1002LPDDR4) -> dict[str, Sequence[CapacitorKind]]:
    """Every FPGA set by rail name: each XPIO bank's
    (:py:data:`XPIO_BANKS`), each of :py:func:`fpga_rail_sets` and
    VCCAUX_SMON's. These are the names a :py:class:`RailLayout` mapping
    takes."""
    return {
        **dict.fromkeys(XPIO_BANKS, XPIO_BANK_SET),
        **{r.name: r.kinds for r in fpga_rail_sets(fpga)},
        "VCCAUX_SMON": VCCAUX_SMON_SET,
    }


class FpgaDecoupling(Container):
    """Every FPGA supply rail's set but the XPIO banks'.

    ``grid`` gives each FPGA ball's position (:py:func:`ball_grid`).
    ``layouts`` maps a rail name of :py:func:`fpga_sets` to how a layout
    treats some of its set; a rail it does not name gets every capacitor.
    It may name the XPIO banks too, whose sets
    :py:class:`XpioBankDecoupling` builds.
    """

    def __init__(
        self,
        fpga: VP1002LPDDR4,
        grid: Mapping[Port, GridPosition],
        layouts: Mapping[str, RailLayout] | None = None,
    ) -> None:
        ic = fpga.fpga
        layouts = layouts or {}
        unknown = set(layouts) - set(fpga_sets(fpga))
        if unknown:
            raise ValueError(f"no FPGA set for rails {sorted(unknown)}")
        self.rails = [
            FpgaRailDecoupling(r.balls, grid, r.kinds, r.rail_max, layouts.get(r.name))
            for r in fpga_rail_sets(fpga)
        ]
        self.smon = FpgaRailDecoupling(
            (ic.VCCAUX_SMON,),
            grid,
            VCCAUX_SMON_SET,
            AUX_MAX,
            layouts.get("VCCAUX_SMON"),
        )

    def capacitors(self) -> list[Capacitor]:
        """The capacitors that return to the main ground: all but VCCAUX_SMON's."""
        return [c for rail in self.rails for c in rail.capacitors()]

    def smon_capacitors(self) -> list[Capacitor]:
        """VCCAUX_SMON's capacitors, which return to GND_SMON (AM006 v1.5
        Figure 1)."""
        return self.smon.capacitors()

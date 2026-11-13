"""18-layer reference substrate, transcribed from a production fabrication drawing.

Ground truth
------------
The stackup, copper weights, impedance table, drill charts, backdrill charts
and fabrication notes come from the fabrication drawing of a production FPGA
evaluation board: 18 copper layers on Elite Material EM-890, 65.83 mil
finished, built to IPC-6012 class 2 and inspected to IPC-A-600 class 2. The
drawing itself is not part of this package; its numbers are transcribed here
row by row, and each constant says which table it comes from.

The drawing gives no dielectric constant, loss tangent, via pad size or
general design rule. The section "Design values" below gives each of those
and the method it comes from.

Unit conversions
----------------
JITX is millimetres throughout. The drawing is in mils, so every thickness,
width, gap and drill size is converted at 0.0254 mm per mil (:py:func:`mil`).
Thicknesses are the drawing's finished values: the outer layers are its
"0.5 oz copper plus plating" row at 2.35 mil, not the 0.5 oz foil weight.
Drill sizes are finished sizes (drawing note 19).

What JITX cannot hold
---------------------
Drawing requirements with no field in the API, recorded here only:

* Copper weight and foil class. ``Conductor`` has a thickness and no weight
  or foil type; the foil class (STD, H-VLP, RTF) is in each copper material's
  name and docstring. The drawing states no roughness, so ``roughness`` is
  left unset.
* Minimum copper weight of 0.5 oz on every layer, 100% electrical test,
  UL 94V-0 rating, and the IPC class.
* Finish: selective hard gold flash, 2 to 10 microinches over 125 microinches
  minimum nickel; hard gold edge fingers, 30 microinches gold over 150
  microinches nickel minimum.
* Bake at 225 degrees for 4 hours after fabrication.
* Copper thieving: none on the top layer in the BGA area or under text;
  30 mil square pads at 50 mil spacing on internal layers, 150 mil clear of
  copper features.
* Artwork rotated 10 degrees on the working panel against fiber-weave skew.
* Via fill material. Every via drill of 15.0 mil and under is filled with
  non-conductive epoxy, planarized and plated over, at least 0.0007 in of
  plating on the surface, with via-in-pad wrap plating per IPC-6012.
  ``Via.filled`` is a boolean.
* Backdrill must-not-cut layer and manufacturing stub length. Each backdrill
  chart names the signal layer the backdrill must not cut and an 8.0 mil
  manufacturing stub. ``Backdrill`` holds diameters only; the must-not-cut
  layer is the via's own end layer, and the stub length is in the via
  docstrings.
* Drill tolerances: +2.0 mil / minus the full drill size on via drills.
* Thickness tolerance. The drawing's only thickness tolerance is at the edge
  fingers: 1.57 mm +/- 0.127 mm (0.062 in +/- 0.005 in) over plating. It gives
  none on the 65.83 mil stackup total. ``Material.thickness`` is a scalar.
* Impedance tolerance. The impedance table gives targets and widths only.
* The 87 ohm "FPGA differential neck width" row names a neck geometry with no
  parent pair; see ``DRS_87_Neck``.

Design values
-------------
* Dk and Df. Elite Material's EM-890 datasheet (:py:data:`EM890_DATASHEET`)
  gives Dk and Df at 10 GHz at two resin contents, 55% and 70%, and no
  per-glass-style table. Each prepreg takes the value linearly interpolated
  at its resin content from the drawing (RC71% is extrapolated 1 point past
  the datasheet's 70%). The drawing gives no resin content for the cores, so
  they take the datasheet's 55% column. See :py:func:`em890_10ghz`.
* Soldermask Dk 3.8 and Df 0.02, typical of LPI soldermask.
* Effective permittivity. Stripline: the mean of the two dielectrics' Dk,
  the substrate-modeler skill's mixed-dielectric rule. Outer microstrip: the
  quasi-static closed form in Pozar, *Microwave Engineering*, 4th ed.,
  section 3.8, with soldermask left out.
* Insertion loss: dielectric loss at 10 GHz, Pozar 4th ed. section 3.1 for
  stripline and section 3.8 for microstrip.
* Clearance: 2x the trace width single-ended and 4x differential, except the
  87 ohm FPGA neck, whose clearance is its own 2.8 mil pair gap so it fits
  between the FPGA's vias (see ``DRS_87_Neck``), and the ball-field
  structure below.
* Ball-field structure (``DRS_85_FIELD``): a narrower form of DIFF-85 for
  the segment of a pair's route inside a 0.92 mm ball field, from another
  Versal board's breakout at that pitch (see "Ball-field geometry" in the
  source). The field pair comes to about 85 ohm on this stackup (see
  ``DRS_85_FIELD``).
* Uncoupled regions. The drawing gives no uncoupled geometry, but a pair
  splits at its pads, and without an uncoupled region JITX reports the
  split legs as "Missing routing structure". Each differential structure's
  uncoupled region keeps the coupled width on the same layers, with the
  differential clearance (each leg is still half of a pair), and declares
  half the differential target as its impedance. On the inner layers that
  value sits within 3 ohm of the drawing's single-ended rows at the same
  width, interpolated linearly between the two nearest rows (extrapolated
  for the 75 and 100 ohm widths, which fall outside them). See
  :py:func:`_uncoupled`.
* Reference-plane width: 3x the dielectric height between the line and each
  plane, the substrate-modeler skill's default.
* Via pad diameters: the finished hole plus twice IPC-2221B's 0.050 mm
  minimum external annular ring (section 9.1.1). A removed unused pad
  (note 9) is modeled at the hole size.
* Tenting. Every via is filled and plated over (note 18), so tented.
* Via type per structure. The drawing names no drilling method for its blind
  vias, and the substrate laser drills every one: through one prepreg (TOP
  to L2, L17 to BOTTOM) and two dielectrics deep (TOP to L3, L16 to BOTTOM),
  as a production FPGA evaluation board with this layer order laser drills
  its TOP to L3 span. That is a design choice; controlled-depth mechanical
  drilling would also reach L3. Through and backdrilled vias are mechanical,
  with a 10.0 mil drill for the backdrilled vias, the TOP to BOTTOM chart's
  most used size.
* Backdrill start pad (two annular rings over the backdrill), soldermask
  opening (two registrations) and copper clearance (two copper-to-hole
  spaces).
* Via delay models. Every via carries a model for each pair of copper
  layers its plated barrel joins (:py:func:`via_models`): the barrel's
  transit time from the middle of one copper to the middle of the other,
  each dielectric on the way at its own Dk (:py:func:`via_delay`). A
  backdrilled via's model covers its plated span. Vias are lossless.
* :py:class:`Reference18FabRules`: the minimum drill and the soldermask
  registration are the drawing's; each other field gives its method.

Conductor-index map
-------------------
Indices count copper layers only. ``0`` is TOP and ``-1`` is BOTTOM::

    TOP      = 0     L7_SIG3      = 6     L13_GND  = 12
    L2_GND   = 1     L8_GND_1OZ   = 7     L14_SIG5 = 13
    L3_SIG1  = 2     L9_PWR1_2OZ  = 8     L15_GND  = 14
    L4_GND   = 3     L10_PWR2_2OZ = 9     L16_SIG6 = 15
    L5_SIG2  = 4     L11_GND_1OZ  = 10    L17_GND  = 16 = -2
    L6_GND   = 5     L12_SIG4     = 11    BOTTOM   = 17 = -1

The stackup is not symmetric (the prepreg thicknesses differ between the two
halves), so it is an explicit :py:class:`~jitx.stackup.Stackup`.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log, pi, sqrt

from jitx.board import Board
from jitx.layerindex import Side
from jitx.shapes.composites import rectangle
from jitx.si import DifferentialRoutingStructure, PinModel, RoutingStructure
from jitx.stackup import Conductor, Dielectric, Material, Stackup
from jitx.substrate import FabricationConstraints, Substrate
from jitx.units import ohm
from jitx.via import Backdrill, BackdrillSet, Via, ViaDiameter, ViaType
from jitxlib.physics import phase_velocity

MM_PER_MIL = 0.0254
"Millimetres per mil."

C_MM_PER_S = 299_792_458_000.0
"Speed of light in mm per second."


def mil(value: float) -> float:
    """``value`` mils in millimetres."""
    return value * MM_PER_MIL


# ---------------------------------------------------------------------------
# Dielectric data
# ---------------------------------------------------------------------------

EM890_DATASHEET = (
    "Elite Material Co., EM-890 / EM-89B datasheet, Rev 2024 July, "
    "https://www.emctw.com/upload/website/item/"
    "EM-890%20Datasheet%2020240716_24081910973.pdf"
)
"""Source of the EM-890 Dk and Df: cavity resonator at 10 GHz, C-24/23/50."""

EM890_10GHZ: tuple[tuple[float, float, float], ...] = (
    (0.55, 3.4, 0.0043),
    (0.70, 3.0, 0.0036),
)
"""(resin content, Dk, Df) at 10 GHz, the two columns of :py:data:`EM890_DATASHEET`."""


def em890_10ghz(resin_content: float) -> tuple[float, float]:
    """Dk and Df at 10 GHz for EM-890 at ``resin_content`` (0 to 1), linear
    in resin content through the datasheet's two points (the datasheet has
    no per-glass-style table)."""
    (rc0, dk0, df0), (rc1, dk1, df1) = EM890_10GHZ
    f = (resin_content - rc0) / (rc1 - rc0)
    return dk0 + f * (dk1 - dk0), df0 + f * (df1 - df0)


# ---------------------------------------------------------------------------
# Materials, one class per material the stackup table names
# ---------------------------------------------------------------------------
# Thickness is passed per layer from STACKUP_ROWS, never set on the class.


class Soldermask(Dielectric):
    """Soldermask, "SOLDERMASK_PSR4000_MPHF" in the stackup table, 1.3 mil.

    Dk 3.8 and Df 0.02, typical of LPI soldermask."""

    material_name = "PSR-4000 MP-HF soldermask"
    dielectric_coefficient = 3.8
    loss_tangent = 0.02


class EM890Prepreg1035RC69(Dielectric):
    """ "EM-890_PP_1035(RC69%)X1": one ply of 1035 glass prepreg at 69% resin.

    Dk and Df: :py:func:`em890_10ghz` at 69%."""

    material_name = "EM-890 prepreg 1035 RC69%"
    dielectric_coefficient, loss_tangent = em890_10ghz(0.69)


class EM890Prepreg1035RC71(Dielectric):
    """ "EM-890_PP_1035(RC71%)X2": two plies of 1035 glass prepreg at 71% resin.

    Dk and Df: :py:func:`em890_10ghz` at 71%, one point past the datasheet's
    70% column."""

    material_name = "EM-890 prepreg 1035 RC71% x2"
    dielectric_coefficient, loss_tangent = em890_10ghz(0.71)


class EM890Prepreg1078RC63(Dielectric):
    """ "EM-890_PP_1078(RC63%)X1": one ply of 1078 glass prepreg at 63% resin.

    Dk and Df: :py:func:`em890_10ghz` at 63%."""

    material_name = "EM-890 prepreg 1078 RC63%"
    dielectric_coefficient, loss_tangent = em890_10ghz(0.63)


class EM890Core1078(Dielectric):
    """ "EM-890_CORE_1078X1": core of one ply of 1078 glass.

    Dk and Df: the datasheet's 55% column."""

    material_name = "EM-890 core 1078"
    dielectric_coefficient, loss_tangent = em890_10ghz(0.55)


class EM890Core1035(Dielectric):
    """ "EM-890_CORE_1035X1": core of one ply of 1035 glass.

    Dk and Df: the datasheet's 55% column."""

    material_name = "EM-890 core 1035"
    dielectric_coefficient, loss_tangent = em890_10ghz(0.55)


class OuterCopper(Conductor):
    """ "0.5OZ_STD_COPPER_+_PLATING": 0.5 oz standard foil plus plating, 2.35 mil
    finished. TOP and BOTTOM."""

    material_name = "0.5 oz STD copper + plating"


class HVLPCopperHalfOz(Conductor):
    """ "0.5OZ_H-VLP_COPPER": 0.5 oz H-VLP foil, 0.62 mil. The signal layers and
    the 0.5 oz ground planes."""

    material_name = "0.5 oz H-VLP copper"


class HVLPCopper1Oz(Conductor):
    """ "1OZ_H-VLP_COPPER": 1 oz H-VLP foil, 1.2 mil. L8_GND_1OZ and L11_GND_1OZ."""

    material_name = "1 oz H-VLP copper"


class HVLPCopper2Oz(Conductor):
    """ "2OZ_H-VLP_COPPER": 2 oz H-VLP foil, 2.4 mil. L9_PWR1_2OZ."""

    material_name = "2 oz H-VLP copper"


class RTFCopper2Oz(Conductor):
    """ "2OZ_RTF_COPPER": 2 oz reverse-treated foil, 2.4 mil. L10_PWR2_2OZ."""

    material_name = "2 oz RTF copper"


# ---------------------------------------------------------------------------
# Stackup table
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StackupRow:
    """One row of the drawing's stackup table."""

    name: str
    "Layer name: the drawing's for copper, glass style and neighboring layers for a dielectric."
    material: type[Material]
    thickness_mil: float
    "Finished thickness from the drawing, in mils."

    @property
    def thickness(self) -> float:
        """Thickness in mm."""
        return mil(self.thickness_mil)


STACKUP_ROWS: tuple[StackupRow, ...] = (
    StackupRow("Soldermask-Top", Soldermask, 1.3),
    StackupRow("TOP", OuterCopper, 2.35),
    StackupRow("PP 1035 RC69% TOP-L2", EM890Prepreg1035RC69, 2.32),
    StackupRow("L2_GND", HVLPCopperHalfOz, 0.62),
    StackupRow("Core 1078 L2-L3", EM890Core1078, 2.5),
    StackupRow("L3_SIG1", HVLPCopperHalfOz, 0.62),
    StackupRow("PP 1078 RC63% L3-L4", EM890Prepreg1078RC63, 2.63),
    StackupRow("L4_GND", HVLPCopperHalfOz, 0.62),
    StackupRow("Core 1078 L4-L5", EM890Core1078, 2.5),
    StackupRow("L5_SIG2", HVLPCopperHalfOz, 0.62),
    StackupRow("PP 1078 RC63% L5-L6", EM890Prepreg1078RC63, 2.64),
    StackupRow("L6_GND", HVLPCopperHalfOz, 0.62),
    StackupRow("Core 1078 L6-L7", EM890Core1078, 2.5),
    StackupRow("L7_SIG3", HVLPCopperHalfOz, 0.62),
    StackupRow("PP 1078 RC63% L7-L8", EM890Prepreg1078RC63, 2.62),
    StackupRow("L8_GND_1OZ", HVLPCopper1Oz, 1.2),
    StackupRow("Core 1035 L8-L9", EM890Core1035, 2.0),
    StackupRow("L9_PWR1_2OZ", HVLPCopper2Oz, 2.4),
    StackupRow("PP 1035 RC71% x2 L9-L10", EM890Prepreg1035RC71, 4.24),
    StackupRow("L10_PWR2_2OZ", RTFCopper2Oz, 2.4),
    StackupRow("Core 1035 L10-L11", EM890Core1035, 2.0),
    StackupRow("L11_GND_1OZ", HVLPCopper1Oz, 1.2),
    StackupRow("PP 1078 RC63% L11-L12", EM890Prepreg1078RC63, 2.64),
    StackupRow("L12_SIG4", HVLPCopperHalfOz, 0.62),
    StackupRow("Core 1078 L12-L13", EM890Core1078, 2.5),
    StackupRow("L13_GND", HVLPCopperHalfOz, 0.62),
    StackupRow("PP 1078 RC63% L13-L14", EM890Prepreg1078RC63, 2.73),
    StackupRow("L14_SIG5", HVLPCopperHalfOz, 0.62),
    StackupRow("Core 1078 L14-L15", EM890Core1078, 2.5),
    StackupRow("L15_GND", HVLPCopperHalfOz, 0.62),
    StackupRow("PP 1078 RC63% L15-L16", EM890Prepreg1078RC63, 2.75),
    StackupRow("L16_SIG6", HVLPCopperHalfOz, 0.62),
    StackupRow("Core 1078 L16-L17", EM890Core1078, 2.5),
    StackupRow("L17_GND", HVLPCopperHalfOz, 0.62),
    StackupRow("PP 1035 RC69% L17-BOTTOM", EM890Prepreg1035RC69, 2.32),
    StackupRow("BOTTOM", OuterCopper, 2.35),
    StackupRow("Soldermask-Bottom", Soldermask, 1.3),
)
"""The drawing's stackup table, top to bottom, thicknesses in mils.

The stackup and the via delay models both read this table, so the two cannot
drift apart."""

_COPPER_ROWS: tuple[int, ...] = tuple(
    i for i, row in enumerate(STACKUP_ROWS) if issubclass(row.material, Conductor)
)


def stackup_span(start: int, stop: int) -> tuple[StackupRow, ...]:
    """The rows from copper layer ``start`` through copper layer ``stop``,
    both included, top to bottom. Indices count copper layers only and may be
    negative, as for a via."""
    a, b = sorted((_COPPER_ROWS[start], _COPPER_ROWS[stop]))
    return STACKUP_ROWS[a : b + 1]


def via_delay(start: int, stop: int) -> float:
    """First-order delay in seconds of a via barrel from the middle of copper
    layer ``start`` to the middle of copper layer ``stop``. Each dielectric
    between contributes its thickness plus half of each copper beside it, at
    its own Dk: the sum of D * sqrt(Dk) / c."""
    rows = stackup_span(start, stop)
    delay = 0.0
    for i, row in enumerate(rows):
        material = row.material
        if not issubclass(material, Dielectric):
            continue
        dk = material.dielectric_coefficient
        if dk is None:
            raise ValueError(f"{row.name} has no Dk")
        span = rows[i - 1].thickness / 2 + row.thickness + rows[i + 1].thickness / 2
        delay += span * sqrt(dk) / C_MM_PER_S
    return delay


def via_models(start: int, stop: int) -> dict[tuple[int, int], PinModel]:
    """A model for every pair of copper layers a via's plated barrel joins,
    from copper layer ``start`` to ``stop`` (negative counts from BOTTOM):
    :py:func:`via_delay` between the two, and no loss. A route may enter and
    leave the via on any two layers it spans, so every pair has a model."""
    n = len(_COPPER_ROWS)
    a, b = sorted((start % n, stop % n))
    return {
        (i, j): PinModel(via_delay(i, j), 0.0)
        for i in range(a, b + 1)
        for j in range(i + 1, b + 1)
    }


class Reference18Stackup(Stackup):
    """18 copper layers, 17 dielectrics and 2 soldermask layers: 37 entries.

    Thickness accounting, in mils, against the drawing's TOTAL THICKNESS::

        soldermask         2 x 1.30           =  2.60
        outer copper       2 x 2.35           =  4.70
        0.5 oz H-VLP      12 x 0.62           =  7.44
        1 oz H-VLP         2 x 1.20           =  2.40
        2 oz H-VLP and RTF 2 x 2.40           =  4.80
        PP 1035 RC69%      2 x 2.32           =  4.64
        PP 1078 RC63%      2.63 + 2.64 + 2.62
                           + 2.64 + 2.73 + 2.75 = 16.01
        PP 1035 RC71% x2   1 x 4.24           =  4.24
        core 1078          6 x 2.50           = 15.00
        core 1035          2 x 2.00           =  4.00
                                      total   = 65.83 mil (drawing: 65.83)
    """

    name = "18-layer reference"
    layers = [
        row.material(name=row.name, thickness=row.thickness) for row in STACKUP_ROWS
    ]


# ---------------------------------------------------------------------------
# Fabrication constraints
# ---------------------------------------------------------------------------

IPC_MIN_ANNULAR_RING = 0.050
"""IPC-2221B section 9.1.1 minimum external annular ring, in mm. Every via
pad is the hole plus two of these."""

BACKDRILL_OVERSIZE_MIL = 6.0
"""Backdrill charts' note: "BACKDRILL SIZE IS DRILL+6 MIL"."""

SOLDER_MASK_REGISTRATION = mil(2.0)
"""Drawing note 10: soldermask registration within diametrical true position
of +/- 0.002 in."""

_SMALLEST_VIA_PAD = mil(6.0) + 2 * IPC_MIN_ANNULAR_RING


class Reference18FabRules(FabricationConstraints):
    """The 19 fields JITX requires. Only the four ``min_copper_*`` rules are
    engine-enforced.

    From the drawing: ``min_drill_diameter`` (6.0 mil, the smallest drill on
    any drill chart) and ``solder_mask_registration`` (note 10). Every other
    field gives its method on its line. Capability limits JITX has no field
    for: blind vias two dielectrics deep need a laser that reaches L3 or
    L16 through 5.44 mil of PP 1035, L2 or L17 copper and 1078 core under
    the outer foil (stackup table), under the 6.9 mil drill, so under 1:1
    before the foil; backdrilled depths need controlled-depth drilling; and
    note 20 says "VENDOR IS REQUIRED TO SELECT TOOLING FOR OVERDRILLING".
    """

    # The narrowest width and the smallest gap in the impedance table.
    min_copper_width = mil(2.6)
    min_copper_copper_space = mil(2.8)
    # The backdrill's radial oversize, half of drill + 6 mil.
    min_copper_hole_space = mil(BACKDRILL_OVERSIZE_MIL / 2)
    # Twice the drawing's +/-0.005 in linear dimension tolerance, so copper
    # stays inside the outline at that tolerance with as much again to spare.
    min_copper_edge_space = mil(10.0)
    # IPC-2221B 9.1.1.
    min_annular_ring = IPC_MIN_ANNULAR_RING
    # Drawing: the smallest drill on any drill chart.
    min_drill_diameter = mil(6.0)
    # Two annular rings plus the smallest copper gap.
    min_hole_to_hole = 2 * IPC_MIN_ANNULAR_RING + mil(2.8)
    # The smallest via pad plus the smallest copper gap.
    min_pitch_leaded = _SMALLEST_VIA_PAD + mil(2.8)
    min_pitch_bga = _SMALLEST_VIA_PAD + mil(2.8)
    # The usable area of an 18 x 24 in production panel, 1 in of border on
    # each side: 22 x 16 in.
    max_board_width = 22 * 25.4
    max_board_height = 16 * 25.4
    # Legend: 5 mil lines, 32 mil text.
    min_silkscreen_width = mil(5.0)
    min_silkscreen_text_height = mil(32.0)
    # Drawing: note 10.
    solder_mask_registration = SOLDER_MASK_REGISTRATION
    # One or two registrations, or the smallest via pad plus two.
    min_silk_solder_mask_space = SOLDER_MASK_REGISTRATION
    min_soldermask_bridge = 2 * SOLDER_MASK_REGISTRATION
    min_soldermask_opening = _SMALLEST_VIA_PAD + 2 * SOLDER_MASK_REGISTRATION
    min_pth_pin_solder_clearance = SOLDER_MASK_REGISTRATION
    # IPC-2221B 9.1.1.
    min_th_pad_expand_outer = IPC_MIN_ANNULAR_RING


# ---------------------------------------------------------------------------
# Vias
# ---------------------------------------------------------------------------


def via_pad(hole_mil: float) -> float:
    """Pad diameter in mm for a finished hole of ``hole_mil`` mils: the hole
    plus twice IPC-2221B's minimum external annular ring."""
    return mil(hole_mil) + 2 * IPC_MIN_ANNULAR_RING


def via_diameter(hole_mil: float) -> ViaDiameter:
    """The pad of :py:func:`via_pad`, with unused internal pads removed:
    drawing note 9, "REMOVE ALL UNUSED PADS FROM INTERNAL LAYERS". JITX uses
    ``nfp`` on every layer except the start layer when the via has no top
    backdrill, the stop layer when it has no bottom backdrill, and any
    intermediate layer with a trace or pour connected. A backdrilled via's
    signal layer is its start or stop layer on the backdrilled side, so each
    backdrilled via sets that layer's full pad in ``diameters`` and no reading
    of ``nfp`` removes it. A removed pad is modeled as a pad the size of the
    finished hole, leaving no copper ring."""
    return ViaDiameter(via_pad(hole_mil), nfp=mil(hole_mil))


BACKDRILLED_VIA_HOLE_MIL = 10.0
"""Drill of the backdrilled through vias: 10.0 mil, the most used plated size
on the TOP to BOTTOM drill chart."""


def backdrill_for(hole_mil: float) -> Backdrill:
    """The backdrill for a via of ``hole_mil`` mils: diameter drill + 6 mil
    from the backdrill charts, with a start pad of the diameter plus two IPC
    rings, a soldermask opening of the diameter plus two registrations and a
    copper clearance of the diameter plus two ``min_copper_hole_space``."""
    diameter = mil(hole_mil + BACKDRILL_OVERSIZE_MIL)
    return Backdrill(
        diameter=diameter,
        startpad_diameter=diameter + 2 * IPC_MIN_ANNULAR_RING,
        solder_mask_opening=diameter + 2 * SOLDER_MASK_REGISTRATION,
        copper_clearance=diameter + 2 * Reference18FabRules.min_copper_hole_space,
    )


# ---------------------------------------------------------------------------
# Routing structures
# ---------------------------------------------------------------------------

MICROSTRIP_LAYERS: tuple[int, ...] = (0, -1)
"""TOP and BOTTOM: microstrip over L2_GND and under L17_GND."""

STRIPLINE_LAYERS: tuple[int, ...] = (2, 4, 6, 11, 13, 15)
"""L3_SIG1, L5_SIG2, L7_SIG3, L12_SIG4, L14_SIG5 and L16_SIG6: stripline
between two ground planes, each with a 1078 core on one side and 1078 RC63%
prepreg on the other.

Only SE_50, DRS_87_Neck and DRS_100 cover all six; the drawing strikes the
other structures on some of them. A caller filters by ``structure.layers``
before using a structure on these layers."""

REFERENCE_PLANES: dict[int, tuple[int, ...]] = {
    0: (1,),  # TOP over L2_GND
    2: (1, 3),  # L3_SIG1 between L2_GND and L4_GND
    4: (3, 5),  # L5_SIG2 between L4_GND and L6_GND
    6: (5, 7),  # L7_SIG3 between L6_GND and L8_GND_1OZ
    11: (10, 12),  # L12_SIG4 between L11_GND_1OZ and L13_GND
    13: (12, 14),  # L14_SIG5 between L13_GND and L15_GND
    15: (14, 16),  # L16_SIG6 between L15_GND and L17_GND
    -1: (-2,),  # BOTTOM under L17_GND
}
"""Reference planes of each routing layer: the adjacent ground layers in the
drawing's layer list. A design supplies :py:class:`~jitx.si.ReferencePlanes`
covering these for any topology on one of these structures."""

LOSS_FREQUENCY_HZ = 10e9
"""Frequency of the insertion loss: the datasheet's Dk and Df frequency."""

_DB_PER_NEPER = 20 / log(10)


def _dielectric(row: StackupRow) -> tuple[float, float, float]:
    """(Dk, Df, thickness in mm) of a dielectric row."""
    material = row.material
    if not issubclass(material, Dielectric):
        raise TypeError(f"{row.name} is not a dielectric")
    dk, df = material.dielectric_coefficient, material.loss_tangent
    if dk is None or df is None:
        raise ValueError(f"{row.name} has no Dk or Df")
    return dk, df, row.thickness


def _neighbors(layer: int) -> tuple[StackupRow, StackupRow]:
    """The rows above and below copper layer ``layer``."""
    i = _COPPER_ROWS[layer]
    return STACKUP_ROWS[i - 1], STACKUP_ROWS[i + 1]


def _signal_dielectric(layer: int) -> tuple[float, float, float]:
    """(Dk, Df, height in mm) of a microstrip layer's dielectric to its plane."""
    above, below = _neighbors(layer)
    return _dielectric(below if layer == 0 else above)


def _eps_and_loss(layer: int, width: float) -> tuple[float, float]:
    """Effective permittivity and insertion loss (dB/mm) of a trace of
    ``width`` mm on ``layer``; see the module docstring.

    Stripline: eps_eff = (Dk_above + Dk_below) / 2, the substrate-modeler
    skill's mixed-dielectric rule, with Df averaged the same way; dielectric
    loss k tan(delta) / 2 (Pozar, 4th ed., section 3.1).

    Microstrip: eps_eff = (Dk + 1) / 2 + (Dk - 1) / 2 / sqrt(1 + 12 h / w) and
    dielectric loss k0 Dk (eps_eff - 1) tan(delta) / (2 sqrt(eps_eff) (Dk - 1))
    (Pozar, 4th ed., section 3.8), soldermask left out.
    """
    k0 = 2 * pi * LOSS_FREQUENCY_HZ / C_MM_PER_S
    if layer in MICROSTRIP_LAYERS:
        dk, df, h = _signal_dielectric(layer)
        eps = (dk + 1) / 2 + (dk - 1) / 2 / sqrt(1 + 12 * h / width)
        alpha = k0 * dk * (eps - 1) * df / (2 * sqrt(eps) * (dk - 1))
    else:
        above, below = (_dielectric(row) for row in _neighbors(layer))
        eps = (above[0] + below[0]) / 2
        alpha = k0 * sqrt(eps) * (above[1] + below[1]) / 2 / 2
    return eps, alpha * _DB_PER_NEPER


def reference_plane_widths(layer: int) -> dict[int, float]:
    """Desired width of each reference plane of ``layer``: 3x the dielectric
    height between the line and that plane."""
    widths: dict[int, float] = {}
    for plane in REFERENCE_PLANES[layer]:
        rows = stackup_span(layer, plane)
        widths[plane] = 3 * sum(
            row.thickness for row in rows if issubclass(row.material, Dielectric)
        )
    return widths


def nearest_plane_height(layer: int) -> float:
    """Height in mm from routing layer ``layer`` to its nearest reference
    plane: the dielectric between the line and that plane, the smaller of
    the two for a stripline. UG863 states LPDDR4 spacing in multiples of
    this height ("H is the distance to the nearest ground return plane")."""
    return min(
        sum(
            row.thickness
            for row in stackup_span(layer, plane)
            if issubclass(row.material, Dielectric)
        )
        for plane in REFERENCE_PLANES[layer]
    )


def _se_layers(
    layers: tuple[int, ...], width_mil: float, clearance_mil: float | None = None
) -> dict[int, RoutingStructure.Layer]:
    """One single-ended impedance-table row across its layers: the table's
    width, a clearance of 2x width unless ``clearance_mil`` is given, and the
    velocity, loss and plane widths of the module docstring."""
    width = mil(width_mil)
    clearance = 2 * width if clearance_mil is None else mil(clearance_mil)
    out: dict[int, RoutingStructure.Layer] = {}
    for layer in layers:
        eps, loss = _eps_and_loss(layer, width)
        out[layer] = RoutingStructure.Layer(
            trace_width=width,
            clearance=clearance,
            velocity=phase_velocity(eps),
            insertion_loss=loss,
        ).reference(reference_plane_widths(layer))
    return out


def _diff_layers(
    layers: tuple[int, ...],
    width_mil: float,
    gap_mil: float,
    clearance_mil: float | None = None,
) -> dict[int, DifferentialRoutingStructure.Layer]:
    """One differential impedance-table row (width/space/width) across its
    layers: the table's width and edge-to-edge gap, a clearance of 4x width
    unless ``clearance_mil`` is given, and the plane widths of the module
    docstring, with velocity and loss from the single-line formulas."""
    width = mil(width_mil)
    clearance = 4 * width if clearance_mil is None else mil(clearance_mil)
    out: dict[int, DifferentialRoutingStructure.Layer] = {}
    for layer in layers:
        eps, loss = _eps_and_loss(layer, width)
        out[layer] = DifferentialRoutingStructure.Layer(
            trace_width=width,
            pair_spacing=mil(gap_mil),
            clearance=clearance,
            velocity=phase_velocity(eps),
            insertion_loss=loss,
        ).reference(reference_plane_widths(layer))
    return out


def _uncoupled(
    name: str,
    target_ohm: float,
    rows: tuple[tuple[tuple[int, ...], float], ...],
    clearance_mil: float | None = None,
) -> RoutingStructure:
    """Uncoupled region of a differential structure: each
    ``(layers, width_mil)`` row keeps the coupled trace width, with the
    differential clearance (4x width unless ``clearance_mil`` is given, as for
    the pair), the single-line velocity and loss, and the same plane widths.
    The impedance is half the differential target."""
    layers: dict[int, RoutingStructure.Layer] = {}
    for row_layers, width_mil in rows:
        width = mil(width_mil)
        clearance = 4 * width if clearance_mil is None else mil(clearance_mil)
        for layer in row_layers:
            eps, loss = _eps_and_loss(layer, width)
            layers[layer] = RoutingStructure.Layer(
                trace_width=width,
                clearance=clearance,  # the pair's clearance
                velocity=phase_velocity(eps),
                insertion_loss=loss,
            ).reference(reference_plane_widths(layer))
    return RoutingStructure(
        name=f"{name}, uncoupled",
        impedance=target_ohm / 2 * ohm,
        layers=layers,
    )


TOP, BOTTOM = MICROSTRIP_LAYERS
L3, L5, L7, L12, L14, L16 = STRIPLINE_LAYERS


# ---------------------------------------------------------------------------
# Ball-field geometry
# ---------------------------------------------------------------------------
# Not on this substrate's drawing. The values are a production Versal
# evaluation board's, with LPDDR4 at the same 0.92 mm ball pitch: its
# fabrication drawing's "BREAK OUT WIDTHS" row for the 82 ohm
# pairs, and the line-to-line and line-to-via spacing of its constraint set
# for the 0.92 mm BGA, both matched on its routed copper.

FIELD_PAIR_WIDTH_MIL = 3.4
"""Trace width of a differential pair inside a 0.92 mm ball field."""

FIELD_PAIR_GAP_MIL = 3.4
"""Edge-to-edge gap of a differential pair inside a 0.92 mm ball field."""

FIELD_CLEARANCE_MIL = 3.5
"""Clearance inside a 0.92 mm ball field: the reference board's line-to-via
spacing (its line-to-line spacing is 3.4 mil, and a structure holds one
clearance for every object, so the larger of the two)."""


# ---------------------------------------------------------------------------
# Substrate
# ---------------------------------------------------------------------------


class Reference18Substrate(Substrate):
    """The stackup, fab rules, the vias the drill charts offer, and one routing
    structure per impedance-table column.

    Every nested ``Via`` class is registered on the board. All vias are
    15.0 mil or smaller, so all are filled, plated over and allowed in pads
    (drawing note 18), and tented: a filled, plated-over via has no open hole
    for soldermask to clear. Every pad is :py:func:`via_diameter`, with unused
    internal pads removed.
    """

    stackup = Reference18Stackup()
    constraints = Reference18FabRules()

    # --- Drill chart TOP to L2 and L17 to BOTTOM: 6.0 mil -----------------
    # One dielectric (2.32 mil PP 1035) per via, so laser drilled.

    class MicroVia_TOP_L2(Via):
        """Drill chart "TOP to L2", 6.0 mil. Laser drilled through one 2.32 mil
        prepreg."""

        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 1
        diameter = via_diameter(6.0)
        hole_diameter = mil(6.0)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(0, 1)

    class MicroVia_L17_BOTTOM(Via):
        """Drill chart "L17 to BOTTOM", 6.0 mil. Laser drilled through one
        2.32 mil prepreg."""

        type = ViaType.LaserDrill
        start_layer = -2
        stop_layer = -1
        diameter = via_diameter(6.0)
        hole_diameter = mil(6.0)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(-2, -1)

    # --- Drill charts TOP to L3 and L16 to BOTTOM -------------------------
    # Two dielectrics deep. The drawing names no drilling method; laser
    # drilled, a design choice: a production FPGA evaluation board with this
    # layer order laser drills its TOP to L3 span. L16 to BOTTOM mirrors it.

    class BlindVia_TOP_L3_6p9(Via):
        """Drill chart "TOP to L3", 6.9 mil. Laser drilled through two
        dielectrics, a design choice."""

        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = L3
        diameter = via_diameter(6.9)
        hole_diameter = mil(6.9)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(0, L3)

    class BlindVia_TOP_L3_8p0(Via):
        """Drill chart "TOP to L3", 8.0 mil. Laser drilled through two
        dielectrics, a design choice."""

        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = L3
        diameter = via_diameter(8.0)
        hole_diameter = mil(8.0)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(0, L3)

    class BlindVia_TOP_L3_10p0(Via):
        """Drill chart "TOP to L3", 10.0 mil. Laser drilled through two
        dielectrics, a design choice."""

        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = L3
        diameter = via_diameter(10.0)
        hole_diameter = mil(10.0)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(0, L3)

    class BlindVia_L16_BOTTOM_6p9(Via):
        """Drill chart "L16_SIG6 to BOTTOM", 6.9 mil. Laser drilled through
        two dielectrics, a design choice."""

        type = ViaType.LaserDrill
        start_layer = L16
        stop_layer = -1
        diameter = via_diameter(6.9)
        hole_diameter = mil(6.9)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(L16, -1)

    class BlindVia_L16_BOTTOM_10p0(Via):
        """Drill chart "L16_SIG6 to BOTTOM", 10.0 mil. Laser drilled through
        two dielectrics, a design choice."""

        type = ViaType.LaserDrill
        start_layer = L16
        stop_layer = -1
        diameter = via_diameter(10.0)
        hole_diameter = mil(10.0)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(L16, -1)

    # --- Drill chart TOP to BOTTOM ----------------------------------------
    # The chart lists plated drills from 6.0 to 15.0 mil for vias and larger
    # holes for pressfit pins and components. These are its smallest size and
    # its most used one.

    class THVia_6p0(Via):
        """Drill chart "TOP to BOTTOM", 6.0 mil, the smallest plated drill."""

        type = ViaType.MechanicalDrill
        start_layer = Side.Top
        stop_layer = Side.Bottom
        diameter = via_diameter(6.0)
        hole_diameter = mil(6.0)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(0, -1)

    class THVia_10p0(Via):
        """Drill chart "TOP to BOTTOM", 10.0 mil, the most used plated drill."""

        type = ViaType.MechanicalDrill
        start_layer = Side.Top
        stop_layer = Side.Bottom
        diameter = via_diameter(10.0)
        hole_diameter = mil(10.0)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(0, -1)

    # --- Backdrill charts -------------------------------------------------
    # A through drill whose stub past the signal layer is drilled out at
    # drill + 6 mil. The via's end layer is the chart's must-not-cut layer;
    # the drawing leaves an 8.0 mil manufacturing stub, which no field holds.
    # The drill is BACKDRILLED_VIA_HOLE_MIL.

    class BackdrilledVia_TOP_L3(Via):
        """Backdrill chart "BOTTOM to L4_GND", must not cut L3_SIG1."""

        type = ViaType.MechanicalDrill
        start_layer = 0
        stop_layer = L3
        diameter = via_diameter(BACKDRILLED_VIA_HOLE_MIL)
        diameters = {L3: via_pad(BACKDRILLED_VIA_HOLE_MIL)}
        hole_diameter = mil(BACKDRILLED_VIA_HOLE_MIL)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(0, L3)
        backdrill = BackdrillSet(bottom=backdrill_for(BACKDRILLED_VIA_HOLE_MIL))

    class BackdrilledVia_TOP_L5(Via):
        """Backdrill chart "BOTTOM to L6_GND", must not cut L5_SIG2."""

        type = ViaType.MechanicalDrill
        start_layer = 0
        stop_layer = L5
        diameter = via_diameter(BACKDRILLED_VIA_HOLE_MIL)
        diameters = {L5: via_pad(BACKDRILLED_VIA_HOLE_MIL)}
        hole_diameter = mil(BACKDRILLED_VIA_HOLE_MIL)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(0, L5)
        backdrill = BackdrillSet(bottom=backdrill_for(BACKDRILLED_VIA_HOLE_MIL))

    class BackdrilledVia_TOP_L7(Via):
        """Backdrill chart "BOTTOM to L8_GND_1OZ", must not cut L7_SIG3."""

        type = ViaType.MechanicalDrill
        start_layer = 0
        stop_layer = L7
        diameter = via_diameter(BACKDRILLED_VIA_HOLE_MIL)
        diameters = {L7: via_pad(BACKDRILLED_VIA_HOLE_MIL)}
        hole_diameter = mil(BACKDRILLED_VIA_HOLE_MIL)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(0, L7)
        backdrill = BackdrillSet(bottom=backdrill_for(BACKDRILLED_VIA_HOLE_MIL))

    class BackdrilledVia_TOP_L12(Via):
        """Backdrill chart "BOTTOM to L13_GND", must not cut L12_SIG4."""

        type = ViaType.MechanicalDrill
        start_layer = 0
        stop_layer = L12
        diameter = via_diameter(BACKDRILLED_VIA_HOLE_MIL)
        diameters = {L12: via_pad(BACKDRILLED_VIA_HOLE_MIL)}
        hole_diameter = mil(BACKDRILLED_VIA_HOLE_MIL)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(0, L12)
        backdrill = BackdrillSet(bottom=backdrill_for(BACKDRILLED_VIA_HOLE_MIL))

    class BackdrilledVia_TOP_L14(Via):
        """Backdrill chart "BOTTOM to L15_GND", must not cut L14_SIG5."""

        type = ViaType.MechanicalDrill
        start_layer = 0
        stop_layer = L14
        diameter = via_diameter(BACKDRILLED_VIA_HOLE_MIL)
        diameters = {L14: via_pad(BACKDRILLED_VIA_HOLE_MIL)}
        hole_diameter = mil(BACKDRILLED_VIA_HOLE_MIL)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(0, L14)
        backdrill = BackdrillSet(bottom=backdrill_for(BACKDRILLED_VIA_HOLE_MIL))

    class BackdrilledVia_L3_BOTTOM(Via):
        """Backdrill chart "TOP to L2_GND", must not cut L3_SIG1."""

        type = ViaType.MechanicalDrill
        start_layer = L3
        stop_layer = -1
        diameter = via_diameter(BACKDRILLED_VIA_HOLE_MIL)
        diameters = {L3: via_pad(BACKDRILLED_VIA_HOLE_MIL)}
        hole_diameter = mil(BACKDRILLED_VIA_HOLE_MIL)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(L3, -1)
        backdrill = BackdrillSet(top=backdrill_for(BACKDRILLED_VIA_HOLE_MIL))

    class BackdrilledVia_L5_BOTTOM(Via):
        """Backdrill chart "TOP to L4_GND", must not cut L5_SIG2."""

        type = ViaType.MechanicalDrill
        start_layer = L5
        stop_layer = -1
        diameter = via_diameter(BACKDRILLED_VIA_HOLE_MIL)
        diameters = {L5: via_pad(BACKDRILLED_VIA_HOLE_MIL)}
        hole_diameter = mil(BACKDRILLED_VIA_HOLE_MIL)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(L5, -1)
        backdrill = BackdrillSet(top=backdrill_for(BACKDRILLED_VIA_HOLE_MIL))

    class BackdrilledVia_L7_BOTTOM(Via):
        """Backdrill chart "TOP to L6_GND", must not cut L7_SIG3."""

        type = ViaType.MechanicalDrill
        start_layer = L7
        stop_layer = -1
        diameter = via_diameter(BACKDRILLED_VIA_HOLE_MIL)
        diameters = {L7: via_pad(BACKDRILLED_VIA_HOLE_MIL)}
        hole_diameter = mil(BACKDRILLED_VIA_HOLE_MIL)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(L7, -1)
        backdrill = BackdrillSet(top=backdrill_for(BACKDRILLED_VIA_HOLE_MIL))

    class BackdrilledVia_L12_BOTTOM(Via):
        """Backdrill chart "TOP to L11_GND_1OZ", must not cut L12_SIG4."""

        type = ViaType.MechanicalDrill
        start_layer = L12
        stop_layer = -1
        diameter = via_diameter(BACKDRILLED_VIA_HOLE_MIL)
        diameters = {L12: via_pad(BACKDRILLED_VIA_HOLE_MIL)}
        hole_diameter = mil(BACKDRILLED_VIA_HOLE_MIL)
        filled = True
        tented = True
        via_in_pad = True
        models = via_models(L12, -1)
        backdrill = BackdrillSet(top=backdrill_for(BACKDRILLED_VIA_HOLE_MIL))

    # --- Routing structures -----------------------------------------------
    # One structure per impedance-table column, holding only the layers the
    # drawing gives it; struck entries ("CROSSED IMPEDANCE CALL OUTS DO NOT
    # EXIST IN PROVIDED DATA") are left out. Impedance is the column's target,
    # width and pair gap (edge to edge) are the table's, and the rest comes
    # from _se_layers, _diff_layers and _uncoupled.

    SE_40 = RoutingStructure(
        name="40 ohm single-ended (SE-40)",
        impedance=40 * ohm,
        layers={
            **_se_layers(MICROSTRIP_LAYERS, 6.0),
            **_se_layers((L3, L5, L7, L12, L14), 4.0),
        },
    )
    "40 ohm single-ended: TOP and BOTTOM 6.0 mil, L3 to L14 4.0 mil."

    SE_45 = RoutingStructure(
        name="45 ohm single-ended (SE-45)",
        impedance=45 * ohm,
        layers=_se_layers(MICROSTRIP_LAYERS, 4.8),
    )
    "45 ohm single-ended: TOP and BOTTOM 4.8 mil; every inner entry is struck."

    SE_46 = RoutingStructure(
        name="46 ohm single-ended (SE-46)",
        impedance=46 * ohm,
        layers={
            **_se_layers((TOP,), 4.5),
            **_se_layers((L3, L5, L7, L12, L14), 3.1),
        },
    )
    "46 ohm single-ended: TOP 4.5 mil, L3 to L14 3.1 mil; BOTTOM and L16 struck."

    SE_50 = RoutingStructure(
        name="50 ohm single-ended (SE-50)",
        impedance=50 * ohm,
        layers={
            **_se_layers(MICROSTRIP_LAYERS, 3.8),
            **_se_layers(STRIPLINE_LAYERS, 2.8),
        },
    )
    "50 ohm single-ended: TOP and BOTTOM 3.8 mil, all six inner layers 2.8 mil."

    DRS_75 = DifferentialRoutingStructure(
        name="75 ohm differential (DIFF-75)",
        impedance=75 * ohm,
        layers=_diff_layers((L3, L5, L7, L12, L14), 4.4, 6.45),
        uncoupled_region=_uncoupled("DIFF-75", 75, (((L3, L5, L7, L12, L14), 4.4),)),
    )
    "75 ohm differential: L3 to L14 4.4/6.45/4.4 mil; outer and L16 struck."

    DRS_85 = DifferentialRoutingStructure(
        name="85 ohm differential (DIFF-85)",
        impedance=85 * ohm,
        layers={
            **_diff_layers(MICROSTRIP_LAYERS, 4.5, 7.1),
            **_diff_layers((L3, L5, L7), 3.55, 6.45),
        },
        uncoupled_region=_uncoupled(
            "DIFF-85", 85, ((MICROSTRIP_LAYERS, 4.5), ((L3, L5, L7), 3.55))
        ),
    )
    "85 ohm differential: TOP and BOTTOM 4.5/7.1/4.5 mil, L3, L5 and L7 3.55/6.45/3.55 mil."

    DRS_87_Neck = DifferentialRoutingStructure(
        name="87 ohm differential FPGA neck (DIFF-87-NECK)",
        impedance=87 * ohm,
        layers=_diff_layers(STRIPLINE_LAYERS, 3.2, 2.8, clearance_mil=2.8),
        uncoupled_region=_uncoupled(
            "DIFF-87-NECK", 87, ((STRIPLINE_LAYERS, 3.2),), clearance_mil=2.8
        ),
    )
    """The table's "FPGA differential neck width" column, 87 ohm: 3.2/2.8/3.2 mil
    on all six inner layers. A neck structure of its own, as a design applies
    it to the short necked span under the FPGA. The column names no parent
    pair, so no structure carries it as a neck-down.

    Clearance is the neck's own 2.8 mil pair gap, not 4x width, so
    the neck fits between two 10.0 mil vias at the FPGA's 0.92 mm (36.2 mil)
    pitch: their full 13.9 mil pads leave a 22.3 mil gap, and the pair with
    its clearance on both sides needs 2.8 + 3.2 + 2.8 + 3.2 + 2.8 = 14.8 mil.
    At 4x width (12.8 mil) it would need 34.8 mil."""

    DRS_90 = DifferentialRoutingStructure(
        name="90 ohm differential (DIFF-90)",
        impedance=90 * ohm,
        layers={
            **_diff_layers(MICROSTRIP_LAYERS, 3.9, 7.1),
            **_diff_layers((L3, L5, L7, L12), 3.2, 6.45),
        },
        uncoupled_region=_uncoupled(
            "DIFF-90", 90, ((MICROSTRIP_LAYERS, 3.9), ((L3, L5, L7, L12), 3.2))
        ),
    )
    "90 ohm differential: TOP and BOTTOM 3.9/7.1/3.9 mil, L3 to L12 3.2/6.45/3.2 mil."

    DRS_92 = DifferentialRoutingStructure(
        name="92 ohm differential (DIFF-92)",
        impedance=92 * ohm,
        layers={
            **_diff_layers(MICROSTRIP_LAYERS, 3.7, 7.1),
            **_diff_layers((L3, L5, L7, L12), 3.05, 6.45),
        },
        uncoupled_region=_uncoupled(
            "DIFF-92", 92, ((MICROSTRIP_LAYERS, 3.7), ((L3, L5, L7, L12), 3.05))
        ),
    )
    "92 ohm differential: TOP and BOTTOM 3.7/7.1/3.7 mil, L3 to L12 3.05/6.45/3.05 mil."

    DRS_100 = DifferentialRoutingStructure(
        name="100 ohm differential (DIFF-100)",
        impedance=100 * ohm,
        layers={
            **_diff_layers(MICROSTRIP_LAYERS, 3.0, 7.1),
            **_diff_layers(STRIPLINE_LAYERS, 2.6, 6.65),
        },
        uncoupled_region=_uncoupled(
            "DIFF-100", 100, ((MICROSTRIP_LAYERS, 3.0), (STRIPLINE_LAYERS, 2.6))
        ),
    )
    "100 ohm differential: TOP and BOTTOM 3.0/7.1/3.0 mil, inner 2.6/6.65/2.6 mil."

    # --- Ball-field structure ---------------------------------------------
    # For the segment of a pair's route inside a 0.92 mm ball field, applied
    # by a tag on that segment's Route at a priority above the net's
    # structure (see "Ball-field geometry" above). The pair necks and
    # carries the impedance of the structure it narrows. An impedance lookup
    # at 85 ohm returns the open-field structure, which is declared first.

    DRS_85_FIELD = DifferentialRoutingStructure(
        name="DIFF-85 inside a 0.92 mm ball field",
        impedance=85 * ohm,
        layers=_diff_layers(
            (L3, L5, L7),
            FIELD_PAIR_WIDTH_MIL,
            FIELD_PAIR_GAP_MIL,
            clearance_mil=FIELD_CLEARANCE_MIL,
        ),
        uncoupled_region=_uncoupled(
            "DIFF-85-FIELD",
            85,
            (((L3, L5, L7), FIELD_PAIR_WIDTH_MIL),),
            clearance_mil=FIELD_CLEARANCE_MIL,
        ),
    )
    """DIFF-85's ball-field neck, 3.4/3.4/3.4 mil with 3.5 mil clearance, on
    DIFF-85's inner layers. The pair fits between two adjacent THVia_10p0
    pads at 0.92 mm pitch: 2 x 3.5 + 3 x 3.4 = 17.2 mil against a 22.3 mil
    gap. Full DIFF-85 (3.55/6.45/3.55 with 4x width clearance) needs 41.95.

    Impedance on this stackup: about 85 ohm. IPC-2141A's edge-coupled
    stripline formula, scaled to the impedance table's rows on the same
    layers, gives 85.6 ohm from the 87 ohm neck row (3.2/2.8/3.2, the
    nearest geometry) and 83.3 ohm from the 85 ohm DIFF-85 row."""


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------

BOARD_WIDTH = 80.0
BOARD_HEIGHT = 80.0
BOARD_CORNER_RADIUS = 4.0
"""Board outline in mm: sized for the JS4 LPDDR4 design's parts, not the
source board's outline."""

_EDGE_KEEPOUT = Reference18FabRules.min_copper_edge_space


class Reference18Board(Board):
    """80 x 80 mm board for the 18-layer reference substrate, sized for the
    JS4 LPDDR4 design's parts. The signal area is inset by the fab rules'
    copper-to-edge space."""

    shape = rectangle(BOARD_WIDTH, BOARD_HEIGHT, radius=BOARD_CORNER_RADIUS)
    signal_area = rectangle(
        BOARD_WIDTH - 2 * _EDGE_KEEPOUT,
        BOARD_HEIGHT - 2 * _EDGE_KEEPOUT,
        radius=BOARD_CORNER_RADIUS - _EDGE_KEEPOUT,
    )

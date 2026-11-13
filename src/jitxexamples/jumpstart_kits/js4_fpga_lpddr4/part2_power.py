"""JS4 Part 2: power, in code: the decoupling placed, the plane pours drawn and
the rules for the two 2 oz power layers.

:py:class:`JS4PowerCircuit` takes Part 1's fanned-out board
(:py:mod:`.part1_fanout_escape`) and adds, on BOTTOM, every decoupling
capacitor and the ZQ, IO_VR and RREF resistors, each in the circuit of the
part it serves so it moves with that part; one plane pour per planed rail
per layer; and the power rules. The design models no power source: each
rail ends at its pours and its capacitors.

Placement order, each step clear of what the earlier ones placed: the
resistors; the small capacitors, rails with the fewest balls first, so a
small rail gets its sites before a large one takes the room around them;
the bulk capacitors, and any small one that found no free site, in the
ring; then the pours.

Resistors (:py:class:`PowerFpga`, :py:class:`PowerMemory`). Each straddles
two of its part's ball vias where its two nets sit one pitch apart, so its
pads lie on the vias and it needs no route:

- each ``r_zq`` over its ZQ ball and the VDD2 ball beside it in row A (the
  memory's ZQ0 at A5 beside A4, ZQ1 at A8 beside A9; ZQ's resistor goes to
  the 1.1 V net, which VDD2 is on);
- each ``r_rref`` over its group's AVTTRCAL ball and the RREF ball beside it
  in the same row (GTY at AB6 and AB7, GTM_L at W28 and W27, GTM_RN at T10
  and T11).

IO_VR_700 (AJ12) has no ball of the 1.1 V net beside it: its nearest
VCCO_700 ball is three rows away. ``r_io_vr`` puts its IO_VR pad on the
ball's via and its other pad on a through via of its own at the centre of
the square of four balls beside it, toward bank 700's VCCO balls; that via
joins the 1.1 V plane on L9, whose outline reaches it.

Small capacitors, below 10 uF (:py:func:`place_straddles`). Each sits on
BOTTOM across a one-pitch pair of ball vias, its rail pad over a ball via of
its rail and its return pad over a ground ball via beside it, with no route:
the pads lie on the vias. It takes the pair nearest the ball its
``ShortTrace`` names (:py:mod:`..vp1002_lpddr4.decoupling`) whose courtyard
overlaps no part placed before it, trying that ball's neighbours in the
order +x, -x, +y, -y. What fits, as a one-pitch straddle on the
``THVia_6p0`` fanout vias (pad 0.252 mm), each pad reaching its via and
keeping 2.8 mil (0.071 mm, the substrate's copper space floor) from every
other via pad, with the example catalogue's lands:

==========  ==============  ==================  ==================
Land        FPGA, 0.92 mm   Memory, 0.8 mm (x)  Memory, 0.65 mm (y)
==========  ==============  ==================  ==================
0201        fits, 0.629 mm  fits, 0.359 mm      fits, 0.334 mm
0402        fits, 0.494 mm  fits, 0.224 mm      fits, 0.099 mm
0603        fails, 0.029    fails, pad on via   fails
0805        fails, on via   fails               fails
==========  ==============  ==================  ==================

Each figure is the gap from the cap's pads to the nearest other via pad.
Every capacitor below 10 uF in the design is an 0201 or an 0402, so each one
fits a pair by size. Across the pair, an 0201's courtyard (0.83 mm) fits
between FPGA rows (0.92 mm); an 0402's (1.10 mm) does not, nor does either
at the memory, so the courtyard check keeps those a row apart. What runs
out is room: all 12 of the memory's small capacitors straddle, and 34 of
the FPGA's 37. The other three (:py:data:`UNPAIRED`), one each of XPIO
banks 700, 701 and 702, belong to rails of three balls whose few
rail/return pairs are already taken. They go to the ring as a bulk
capacitor does, on the 1.1 V plane, tied to their ball by a plain net, not
a ``ShortTrace``, since a ring capacitor has no trace back to a ball. Eight
more small capacitors of the base design's sets find no pair either, on
rails with no plane here; Part 1 never creates them (below).

Bulk capacitors, 10 uF and up, and the small capacitors with no free site
(:py:func:`place_ring`). No bulk capacitor fits between the vias, and a
production FPGA evaluation board puts every part of 10 uF and up outside
the ball field, each on its own via to the plane. Each goes in a ring just
outside its part's field, axis across the field's edge with its rail pad
toward the field and its courtyard starting half a pitch outside
the outermost ball centres, on the edge nearest its rail's balls (ties in
the order right, left, top, bottom), slid along that edge from the point
nearest those balls until its courtyard is clear. Each pad has a
``THVia_6p0`` through via at its centre, so the rail pad reaches its plane
and the return pad the ground pours with no route; the evaluation board's
ring traces reach at most 47.9 mil (1.22 mm), and a via in the pad is
within that. The memory's edge facing the FPGA takes no ring capacitor,
and the FPGA's edge facing the memory takes only the XPIO banks' (the 1.1
V net): the channel between the parts is where the LPDDR4 routes run.
Those also keep out of the corridor where Part 4 routes channel B's two
byte lanes (:py:data:`BYTE_LANE_CORRIDOR`), so bank 702's two slide along
the edge to x -11.04 and -12.88 mm. In a capture of the built design, the
nearest of those vias, at (-2.76, -5.51), keeps 153.22 mil (3.89 mm) from
its pad edge to the copper of Part 1's L3 escape routes. A ring
capacitor carries no ``ShortTrace``, so no route runs back to a ball.
In the ring: the FPGA's seven bulk capacitors on planed rails (VCCINT,
VCC_SOC, VCC_IO, VCCAUX and one per XPIO bank) and the three small ones of
the XPIO banks; the memory's three (VDDQ, VDD2 and VDD1).

Left out, by Part 1. A ring capacitor on a rail with no plane here would
sit on its two vias with nothing joining its rail via to its rail's balls,
so it would decouple nothing. Part 1's FPGA circuit never creates one
(:py:meth:`.part1_fanout_escape.FanoutFpga.decoupling_layouts`): 27 of the
base design's 71 FPGA capacitors, 19 bulk capacitors, one each on VCC_RAM,
VCCAUX_PMC, VCC_PMC, VCC_PSLP, VCC_PSFP, VCCO_500, VCCO_502, VCCO_503,
GTY_AVCC_RS, GTY_AVCCAUX_RS, GTY_AVTT_RS, GTM_AVCC_L, GTM_AVCC_RN,
GTM_AVCCAUX_L, GTM_AVCCAUX_RN, GTM_AVTT_L, GTM_AVTT_RN, VCCINT_GT_L and
VCCINT_GT_R, and the eight small ones above. Part 2 places every capacitor
it inherits. Its FPGA circuit adds one thing to Part 1's
:py:class:`~..vp1002_lpddr4.decoupling.RailLayout` per rail, read before
any capacitor is created (:py:meth:`PowerFpga.decoupling_layouts`): the
XPIO banks' unpaired capacitors tied by a plain net. A small capacitor in
a field stays whatever its rail: it sits on its rail's ball via. The
design holds 59 capacitors: 46 in the fields (34 FPGA, 12 memory) and 13
in the ring (10 FPGA, 3 memory).

Rail to layer (:py:data:`PLANES`), after the split of the same evaluation
board's planes, a design choice:

- L9_PWR1_2OZ: VCCINT under the FPGA, as on the evaluation board; and the
  1.1 V net (the VCCO of XPIO banks 700 to 702 and the memory's VDD2 and
  VDDQ), one piece from bank 700 to 702's VCCO balls to the whole memory
  field, as the evaluation board's VCC1V1_LP4 sits alone on L9 under its
  memory. It is the rail's only copper joining its balls, since the design
  has no source.
- L10_PWR2_2OZ: VCC_SOC (with VCC_IO, one net) and VCCAUX under the FPGA,
  as on the evaluation board.
- L12_SIG4: the memory's VDD1, 1.8 V, alone under the memory, as the
  evaluation board puts its memory 1.8 V rail on a signal layer. Nothing of
  Parts 1 and 3 uses L12: Part 1's escapes are on L3 and its pours on the
  ground layers, and the runbooks give channel A L5 and the command,
  address and clock L7.

The other FPGA rails (VCC_RAM, the PMC, PSLP, PSFP and VCCO_50x rails, the
GTY and GTM rails and VCCINT_GT) get no plane here, so Part 1 creates no
ring capacitor on them. :py:data:`FPGA_PLANES` names the same FPGA rails
as Part 1's :py:data:`~.part1_fanout_escape.POURED_RAILS`.

Pours (:py:func:`rail_outline`, :py:func:`split_layers`). One polygon per
rail per layer, from the part's ball grid: a cell one pitch square on each
of the rail's balls; the cells' bounding box per contiguous cluster (balls
at most two pitches apart, so VCCINT's checkerboard is one cluster and the
other-net vias inside it are voids in the pour); clusters joined by the
hull of each pair, the next cluster to the nearest one already joined; and
each ring capacitor's or resistor's rail via joined to the rail ball
nearest it by a link (:py:func:`channel_link`), :py:data:`LINK_WIDTH` wide
once the layer is split. The link runs midway between ball rows and
columns, never along one: a strip one cell wide along a row has the voids
of that row's other-net vias in it, and the webs left beside them fall
under the width floor (rules, below), so the via ends up on an island.
Under the memory a ring via is joined by the hull of its cell and its
nearest ball's. On a layer, a rail earlier in :py:data:`PLANES` keeps any
overlap, and every outline then shrinks by half of :py:data:`PLANE_GAP`,
so two rails on a layer stay that far apart.
Under the memory each rail has its layer to itself, so its outline is the
memory's whole field, with no subtraction.

The pours sit in :py:class:`JS4PowerCircuit`, computed from where the parts'
circuits sit, so they do not follow a part that moves; the capacitors,
resistors and their vias do.

Rules. The substrate's L9_PWR1_2OZ and L10_PWR2_2OZ are 2 oz copper,
2.4 mil finished (the stackup table,
:py:data:`~jitxexamples.substrates.reference_18layer.STACKUP_ROWS`). The
substrate's drawing gives no width or gap on either: its impedance table
covers only the signal layers. The values come from a fabricator's
published capability, PCBWay's "PCB Capabilities" page, Advanced PCB item
14, "Inner layer min width/spacing (before compensation)", 70 um row
(https://www.pcbway.com/capabilities.html, read 2026-11-10; the page
carries no revision): 6/8 mil in the normal process, 6/7 mil at medium
difficulty. The 70 um row is 2 oz nominal; the drawing's layers finish at
61 um, so the row is the conservative one.

- Width floor, :py:data:`HEAVY_MIN_WIDTH`: 6.0 mil on each plane layer.
- Clearance floor, :py:data:`HEAVY_MIN_CLEARANCE`: 7.0 mil on each plane
  layer, the medium column, a design choice: the board already builds its
  0.5 oz layers at the fabricator's finest column (2.6 mil lines, 2.8 mil
  gaps), so the medium column on 2 oz does not raise its build class. A
  plane keeps ``6.0 + 2 x 7.0`` mil clear across two other-net vias, each a
  6.0 mil hole on L9 and L10 (drawing note 9 removes their unused pads):
  20.0 mil. A capture of the built design agrees: each void around another
  net's via on L9 and L10 is 0.51 mm (20.1 mil) across. That leaves a web
  of 16.22 mil between FPGA balls (36.22 mil pitch) and 11.50 mil between
  memory columns (31.50 mil); between memory rows (25.59 mil) it leaves
  5.59 mil, under the width floor, so the sliver rule removes it and the
  1.1 V plane joins its memory balls along the columns. A strip one FPGA
  pitch wide centred on a ball row leaves 8.11 mil of copper each side of
  a void in that row, and 3.11 mil once the layer split takes half of
  :py:data:`PLANE_GAP` off each edge, under the floor: hence the links
  between rows (pours, above).

Both floors go on each plane layer through
:py:func:`~jitxexamples.patterns.layout_heavy_copper_layer.heavy_layer_rules`
at priority 1, with the trace to pour rule's form on the layer at the
clearance floor. Every other layer keeps the substrate's fabrication floor.

Power width. Each planed rail's net carries :py:class:`PowerTag`, with
:py:data:`POWER_WIDTH`, 6.0 mil, for any trace on it, at priority 2. The
design gives no rail current, so the value is a design choice: the plane
layers' width floor, so it needs no copy there, and narrow enough to pass
between two of the memory's fanout vias in adjacent rows (10.07 mil
between their pads at the 2.8 mil floor). No trace in this part takes it:
every capacitor and resistor sits on its vias.

Pours join every via and pad of their own net solid: the design has no
relief rule. The vias are filled and plated over (drawing note 18) and no
inner layer is soldered, so a relief would buy no solderability and put
its spokes in series with every via's current. A pour drops any part
narrower than its layer's width floor, :py:data:`POUR_FEATURE` (2.6 mil) on
every layer and :py:data:`HEAVY_MIN_WIDTH` on L9 and L10.

The design applies no SI constraints. It needs the parts chain
:py:mod:`.base` describes.
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from enum import Enum

import shapely
from shapely.geometry import LineString, Polygon, box
from shapely.geometry.base import BaseGeometry

from jitx.circuit import Circuit
from jitx.component import Component
from jitx.constraints import DesignConstraint, IsPour, OnLayer, Tag, design_constraint
from jitx.copper import Pour
from jitx.design import Design
from jitx.feature import Courtyard
from jitx.inspect import visit
from jitx.landpattern import Pad
from jitx.net import Net, Port, PortAttachment
from jitx.placement import Side
from jitx.shapes.shapely import ShapelyGeometry
from jitx.units import F
from jitx.via import Via
from jitxlib.parts import Capacitor

from jitxexamples.patterns.layout_heavy_copper_layer import heavy_layer_rules
from jitxexamples.substrates.reference_18layer import (
    Reference18Board,
    Reference18FabRules,
    Reference18Substrate,
    mil,
)

from ..vp1002_lpddr4.decoupling import (
    BULK_CAPACITANCE,
    XPIO_BANKS,
    RailLayout,
    ball_grid,
    fpga_rail_sets,
)
from .base import JS4Fpga, JS4Memory
from .part1_fanout_escape import (
    POURED_RAILS,
    THROUGH_VIA,
    FanoutFpga,
    FanoutMemory,
    JS4FanoutCircuit,
    pad_centres,
    via_in_pad,
)

type Point = tuple[float, float]

L9 = 8
"L9_PWR1_2OZ, by the substrate's conductor-index map."

L10 = 9
"L10_PWR2_2OZ, by the substrate's conductor-index map."

L12 = 11
"L12_SIG4, by the substrate's conductor-index map."

PLANE_LAYERS_2OZ = (L9, L10)
"The two 2 oz plane layers the heavy copper rules apply to."

HEAVY_MIN_WIDTH = mil(6.0)
"""Trace width floor on a 2 oz plane layer, mm: PCBWay Advanced PCB item 14,
70 um row, normal and medium columns (module docstring)."""

HEAVY_MIN_CLEARANCE = mil(7.0)
"""Copper clearance floor on a 2 oz plane layer, mm: PCBWay Advanced PCB item
14, 70 um row, the medium column, a design choice (module docstring)."""

POWER_WIDTH = mil(6.0)
"""Width of a trace on a planed rail, mm. A design choice: no rail current is
given (module docstring)."""

POUR_FEATURE = Reference18FabRules.min_copper_width
"""Narrowest pour feature kept on any layer, mm: the substrate's fabrication
floor, 2.6 mil."""

PLANE_GAP = mil(10.0)
"""Gap between two rails' pours on one layer, mm. A design choice above the
7.0 mil floor: the smallest gap between rails on the production FPGA
evaluation board's L9 and L10 under its FPGA is 10.0 mil."""

LINK_WIDTH = 0.46
"""Width of a ring via's link to its rail's balls, once the layer is split,
mm: half the FPGA's ball pitch, so it holds the whole channel between two
rows of via voids (module docstring, pours)."""

FPGA_PITCH = (0.92, 0.92)
"""The VP1002's ball pitch, x and y, mm: AMD's NFVI1369 package drawing,
e = 0.92."""

MEMORY_PITCH = (0.8, 0.65)
"""The memory's ball pitch, mm: 0.8 between columns (x) and 0.65 between rows
(y), Micron's 200-ball package drawing."""

CLUSTER_LINK = 2
"""Two balls of a rail are in one cluster when at most this many pitches
apart in row and in column, so a rail whose balls alternate with ground
(VCCINT's checkerboard) is one cluster."""

RING_EDGES = ("right", "left", "top", "bottom")
"""The edges of a ball field, in the order that breaks a tie for the
nearest edge."""

BYTE_LANE_CORRIDOR = (-0.360, -10.227, 10.910, -5.020)
"""Where channel B's byte lanes run between the two ball fields, as
``(x0, y0, x1, y1)``, mm, in the board's frame: across the gap from the
memory field's FPGA-facing edge (y -10.227) to the FPGA field's
memory-facing edge (y -5.020), over the span that the reference layout
Part 4 routes along (:py:mod:`.part4_reference_routes`) and Part 1's strobe
escapes occupy there. It runs from byte lane 1's DQ3, where it crosses the
FPGA field's edge (x -0.360), to byte lane 0's DQ3 at its memory field exit
(x 10.910); Part 1's two FPGA escape pair points lie inside it (x 1.382 and
7.931)."""

CORRIDOR_MARGIN = mil(3.1) / 2 + mil(6.2)
"""How far, mm, a ring capacitor's courtyard keeps outside
:py:data:`BYTE_LANE_CORRIDOR`: half the width of a byte lane's open-field
line, the substrate's 46 ohm structure on L3_SIG1 (3.1 mil), plus that
structure's clearance (6.2 mil, twice the width), so a line along the
corridor's edge keeps its clearance from everything under the courtyard."""


class PowerTag(Tag):
    """The net of a rail with a plane in this part."""


class Plane(Enum):
    """Each planed rail, in the order its layer is split: on a layer, an
    earlier rail keeps any overlap."""

    VCCINT = "VCCINT"
    LP4_1V1 = "LP4_1V1"
    VCCAUX = "VCCAUX"
    VCC_SOC = "VCC_SOC"
    LP4_VDD1 = "LP4_VDD1"


PLANES: dict[Plane, int] = {
    Plane.VCCINT: L9,
    Plane.LP4_1V1: L9,
    Plane.VCCAUX: L10,
    Plane.VCC_SOC: L10,
    Plane.LP4_VDD1: L12,
}
"The layer of each planed rail's pour (module docstring, rail to layer)."


FPGA_PLANES: dict[str, Plane] = {
    "VCCO_700": Plane.LP4_1V1,
    "VCCO_701": Plane.LP4_1V1,
    "VCCO_702": Plane.LP4_1V1,
    "VCCINT": Plane.VCCINT,
    "VCC_SOC": Plane.VCC_SOC,
    "VCC_IO": Plane.VCC_SOC,
    "VCCAUX": Plane.VCCAUX,
}
"""The plane of each FPGA rail that has one, by the rail names of
:py:func:`~..vp1002_lpddr4.decoupling.fpga_sets`; VCC_IO is on VCC_SOC's
net."""

UNPAIRED: dict[str, frozenset[int]] = {
    "VCCO_700": frozenset({1}),
    "VCCO_701": frozenset({1}),
    "VCCO_702": frozenset({1}),
}
"""The FPGA's capacitors below 10 uF on a planed rail that find no free pair
of ball vias, by rail name and place in the rail's set
(:py:func:`~..vp1002_lpddr4.decoupling.fpga_sets`): the second 4.7 uF of
each XPIO bank. Those with no pair on rails with no plane are Part 1's
:py:data:`~.part1_fanout_escape.NO_FIELD_PAIR`, never created. Whether a
capacitor finds a pair is known only once the field is placed, but the
decoupling sets read the layout before any capacitor is created
(:py:meth:`PowerFpga.decoupling_layouts`). The placement
(:py:func:`place_straddles`) is deterministic, so the result is worked out
once and written here as data. If it goes stale,
:py:meth:`PowerParts.place_decoupling` fails when a capacitor not listed
here finds no pair. A listed one that would now find a pair is never tried
here, since it is in the ring; the repository's Part 2 tests place every
set whole and check that the capacitors with no pair are exactly these and
Part 1's."""


@dataclass
class RailCaps:
    """One decoupling set to place: its rail's balls, the balls its return
    pads may sit on, each capacitor with the ball its net names (by
    ShortTrace, to sit at the ball, or by plain net, to go in the ring), the
    plane its rail joins and the field edges its ring may use."""

    balls: Sequence[Port]
    returns: Sequence[Port]
    small: list[tuple[Capacitor, Port]]
    bulk: list[tuple[Capacitor, Port]]
    plane: Plane | None
    edges: Sequence[str]


class Field:
    """A placed BGA part's balls in the frame of the circuit that holds it:
    their pad centres, grid positions and pitch, and the courtyards of the
    parts placed on BOTTOM so far."""

    def __init__(self, part: Component, pitch: tuple[float, float]) -> None:
        self.centres = pad_centres(part)
        self.grid = ball_grid(part)
        self.at = {g: p for p, g in self.grid.items()}
        self.pitch = pitch
        xs = [x for x, _ in self.centres.values()]
        ys = [y for _, y in self.centres.values()]
        self.bounds = (min(xs), min(ys), max(xs), max(ys))
        self.courtyards: list[BaseGeometry] = []

    def xy(self, ball: Port) -> Point:
        """A ball's pad centre."""
        return self.centres[ball]

    def cell(self, at: Point) -> Polygon:
        """A box one pitch square centred on ``at``."""
        hx, hy = self.pitch[0] / 2, self.pitch[1] / 2
        return box(at[0] - hx, at[1] - hy, at[0] + hx, at[1] + hy)

    def outline(self) -> Polygon:
        """The whole field: the box of every ball's cell."""
        x0, y0, x1, y1 = self.bounds
        hx, hy = self.pitch[0] / 2, self.pitch[1] / 2
        return box(x0 - hx, y0 - hy, x1 + hx, y1 + hy)

    def neighbours(self, ball: Port) -> list[Port]:
        """The balls one pitch from ``ball`` along a row or column, in the
        order +x, -x, +y, -y in this frame."""
        r, c = self.grid[ball]
        near = [
            self.at.get(g) for g in ((r, c + 1), (r, c - 1), (r + 1, c), (r - 1, c))
        ]
        x, y = self.xy(ball)
        return sorted(
            (b for b in near if b is not None),
            key=lambda b: direction_rank(self.xy(b)[0] - x, self.xy(b)[1] - y),
        )

    def free(self, part: Component) -> bool:
        """Whether ``part``, as placed, overlaps no courtyard kept so far."""
        shape = courtyard(part)
        return all(shape.intersection(c).area < 1e-9 for c in self.courtyards)

    def keep(self, part: Component) -> None:
        """Keep ``part``'s courtyard, as placed, clear of later parts."""
        self.courtyards.append(courtyard(part))

    def clusters(self, balls: Sequence[Port]) -> list[list[Port]]:
        """``balls`` split into clusters, single linkage at
        :py:data:`CLUSTER_LINK` pitches."""
        groups: list[list[Port]] = []
        for ball in sorted(balls, key=lambda b: self.grid[b]):
            r, c = self.grid[ball]
            joined = [
                g
                for g in groups
                if any(
                    max(abs(r - self.grid[b][0]), abs(c - self.grid[b][1]))
                    <= CLUSTER_LINK
                    for b in g
                )
            ]
            merged = [ball] + [b for g in joined for b in g]
            groups = [g for g in groups if all(g is not j for j in joined)] + [merged]
        return groups


def direction_rank(dx: float, dy: float) -> int:
    """Order of a neighbour's direction: +x, -x, +y, -y."""
    if abs(dx) > abs(dy):
        return 0 if dx > 0 else 1
    return 2 if dy > 0 else 3


def courtyard(part: Component) -> BaseGeometry:
    """A placed part's courtyard in the frame of the circuit that holds it."""
    if part.transform is None:
        raise ValueError(f"{part} is not placed")
    shapes: list[BaseGeometry] = []
    for trace, feature in visit(part, Courtyard):
        placement = part.transform
        if trace.transform is not None:
            placement = placement * trace.transform
        shapes.append(ShapelyGeometry.from_shape(placement * feature.shape).g)
    return shapely.union_all(shapes)


def pad_points(part: Component) -> list[Point]:
    """The centre of each of a placed part's pads in the frame of the
    circuit that holds it."""
    if part.transform is None:
        raise ValueError(f"{part} is not placed")
    points: list[Point] = []
    for trace, pad in visit(part, Pad):
        placement = part.transform
        if trace.transform is not None:
            placement = placement * trace.transform
        if pad.transform is not None:
            placement = placement * pad.transform
        x, y = placement * (0.0, 0.0)
        points.append((float(x), float(y)))
    return points


def straddle(part: Component, p1_at: Point, p2_at: Point) -> None:
    """Place a two-pad part on BOTTOM centred between two points, its axis
    along the line joining them and its ``p1`` pad toward ``p1_at``. ``p1``
    is on the land's first pad: the part declares no pad mapping, so JITX
    pairs its ports with its pads in declaration order."""
    part.at(0, 0, on=Side.Bottom)
    vx, vy = pad_points(part)[0]
    mid = ((p1_at[0] + p2_at[0]) / 2, (p1_at[1] + p2_at[1]) / 2)
    ux, uy = p1_at[0] - mid[0], p1_at[1] - mid[1]
    turn = math.degrees(math.atan2(uy, ux) - math.atan2(vy, vx))
    part.at(mid, rotate=round(turn % 360.0, 6), on=Side.Bottom)


def place_straddles(
    field: Field, rail: RailCaps
) -> tuple[list[tuple[Capacitor, Port, Port]], list[tuple[Capacitor, Port]]]:
    """Place each small capacitor of ``rail`` across a free rail/return
    pair, the pair nearest the ball its net names; return each placed
    capacitor with its two balls, and those that found no free pair."""
    back = {id(b) for b in rail.returns}
    placed: list[tuple[Capacitor, Port, Port]] = []
    unfit: list[tuple[Capacitor, Port]] = []
    for cap, named in rail.small:
        nx, ny = field.xy(named)
        order = sorted(
            rail.balls,
            key=lambda b: math.hypot(field.xy(b)[0] - nx, field.xy(b)[1] - ny),
        )
        site = next(
            (
                (b, n)
                for b in order
                for n in field.neighbours(b)
                if id(n) in back and fits(field, cap, b, n)
            ),
            None,
        )
        if site is None:
            unfit.append((cap, named))
            continue
        straddle(cap, field.xy(site[0]), field.xy(site[1]))
        field.keep(cap)
        placed.append((cap, site[0], site[1]))
    return placed, unfit


def fits(field: Field, part: Component, a: Port, b: Port) -> bool:
    """Whether ``part``, straddling balls ``a`` and ``b``, is clear of every
    courtyard kept so far."""
    straddle(part, field.xy(a), field.xy(b))
    return field.free(part)


def place_ring(
    field: Field, part: Component, balls: Sequence[Port], edges: Sequence[str]
) -> tuple[Point, Point]:
    """Place a capacitor in the ring outside the field, its axis across the
    edge of ``edges`` nearest ``balls`` and its ``p1`` pad toward the field,
    its courtyard starting half a pitch outside the outermost ball centres,
    slid along the edge one pitch at a time from the point nearest those
    balls until its courtyard is clear. Return its ``p1`` and ``p2`` pad
    centres."""
    x0, y0, x1, y1 = field.bounds
    reach: dict[str, Callable[[Point], float]] = {
        "right": lambda p: x1 - p[0],
        "left": lambda p: p[0] - x0,
        "top": lambda p: y1 - p[1],
        "bottom": lambda p: p[1] - y0,
    }
    edge = min(
        (e for e in RING_EDGES if e in edges),
        key=lambda e: min(reach[e](field.xy(b)) for b in balls),
    )
    px, py = field.xy(min(balls, key=lambda b: reach[edge](field.xy(b))))
    across = edge in ("left", "right")
    part.at(0, 0, on=Side.Bottom)
    cx0, cy0, cx1, cy1 = courtyard(part).bounds
    depth = field.pitch[0 if across else 1] / 2 + max(cx1 - cx0, cy1 - cy0) / 2
    (ax, ay), (bx, by) = pad_points(part)
    half = math.hypot(ax - bx, ay - by) / 2
    step = field.pitch[1 if across else 0]
    inward = {"right": (-1.0, 0.0), "left": (1.0, 0.0), "top": (0.0, -1.0)}.get(
        edge, (0.0, 1.0)
    )
    for k in (0, *(s * i for i in range(1, 80) for s in (1, -1))):
        if across:
            centre = (x1 + depth if edge == "right" else x0 - depth, py + k * step)
        else:
            centre = (px + k * step, y1 + depth if edge == "top" else y0 - depth)
        p1_at = (centre[0] + inward[0] * half, centre[1] + inward[1] * half)
        p2_at = (centre[0] - inward[0] * half, centre[1] - inward[1] * half)
        straddle(part, p1_at, p2_at)
        if field.free(part):
            field.keep(part)
            return p1_at, p2_at
    raise ValueError(f"no free ring position for {part}")


def farads(cap: Capacitor) -> float:
    """``cap``'s capacitance in farads."""
    return float(cap.value.to(F).magnitude)


def tied(
    nets: Sequence[Net], caps: Sequence[Capacitor]
) -> list[tuple[Capacitor, Port]]:
    """Each of ``caps`` whose ``p1`` is in one of ``nets`` (a decoupling
    set's ``short_traces`` or ``bulk_nets``), with the ball the net ties it
    to, in the order of ``nets``."""
    found: list[tuple[Capacitor, Port]] = []
    for net in nets:
        ports = [p for p in net if isinstance(p, Port)]
        for cap in caps:
            if any(p is cap.p1 for p in ports):
                found.append((cap, next(p for p in ports if p is not cap.p1)))
    return found


class PowerParts:
    """What :py:class:`PowerFpga` and :py:class:`PowerMemory` share: the
    vias they add, and where each via that joins a plane sits, with that
    plane. Each part is held once, by the decoupling set or straps that
    made it, so nothing here lists the parts."""

    power_vias: list[Via]
    power_attachments: list[PortAttachment]
    plane_vias: list[tuple[Plane, Point]]

    def start_power(self) -> None:
        self.power_vias = []
        self.power_attachments = []
        self.plane_vias = []

    def add_via(self, at: Point, port: Port) -> None:
        """A fanout-size through via at ``at``, attached to ``port``."""
        via, attachment = via_in_pad(at, port, THROUGH_VIA)
        self.power_vias.append(via)
        self.power_attachments.append(attachment)

    def place_field(
        self, field: Field, rails: Sequence[RailCaps]
    ) -> list[tuple[Capacitor, Port]]:
        """The small capacitors in the field, rails with the fewest balls
        first, so a small rail gets its sites before a large one takes the
        room around them. Return those that found no free pair."""
        unfit: list[tuple[Capacitor, Port]] = []
        for rail in sorted(rails, key=lambda r: len(r.balls)):
            unfit += place_straddles(field, rail)[1]
        return unfit

    def place_decoupling(
        self,
        field: Field,
        rails: Sequence[RailCaps],
        keepouts: Sequence[BaseGeometry] = (),
    ) -> None:
        """The small capacitors in the field (:py:meth:`place_field`). Then
        the ring capacitors, clear of ``keepouts``, the bulk ones first and
        then any small one the layout sends there (:py:data:`UNPAIRED`),
        each pad on its own via and no trace back to a ball. Fails if a
        small capacitor finds no pair or a rail with no plane has a ring
        capacitor: :py:data:`UNPAIRED` no longer agrees with the placement."""
        unfit = self.place_field(field, rails)
        if unfit:
            raise ValueError(f"no free pair for {[str(c) for c, _ in unfit]}")
        field.courtyards += keepouts
        for rail in rails:
            if rail.plane is None:
                if rail.bulk:
                    raise ValueError(
                        f"ring capacitors on a rail with no plane: {rail.bulk}"
                    )
                continue
            ring = sorted(rail.bulk, key=lambda cb: farads(cb[0]) < BULK_CAPACITANCE)
            for cap, _ in ring:
                p1_at, p2_at = place_ring(field, cap, rail.balls, rail.edges)
                self.add_via(p1_at, cap.p1)
                self.add_via(p2_at, cap.p2)
                self.plane_vias.append((rail.plane, p1_at))


class PowerFpga(FanoutFpga, PowerParts):
    """Part 1's FPGA circuit with its resistors and capacitors placed on
    BOTTOM, and their vias."""

    def __init__(self) -> None:
        super().__init__()
        self.start_power()
        ic = self.fpga
        field = Field(ic, FPGA_PITCH)

        # Resistors first. Each RREF resistor straddles its group's AVTTRCAL
        # ball (p1, the AVTT side) and the RREF ball beside it (p2).
        groups = (
            (ic.GTY_AVTTRCAL_RS, ic.GTY_RREF_RS),
            (ic.GTM_AVTTRCAL_L, ic.GTM_RREF_L),
            (ic.GTM_AVTTRCAL_RN, ic.GTM_RREF_RN),
        )
        for r, (rcal, rref) in zip(self.gt_cal.r_rref, groups, strict=True):
            straddle(r, field.xy(rcal), field.xy(rref))
            field.keep(r)
        # IO_VR_700's resistor: p1 on the IO_VR ball's via, p2 on a via of its
        # own at the centre of the square of balls beside it toward bank
        # 700's VCCO balls (-x, -y here), which joins the 1.1 V plane.
        io_x, io_y = field.xy(ic.IO_VR_700)
        self.io_vr_via_at = (io_x - FPGA_PITCH[0] / 2, io_y - FPGA_PITCH[1] / 2)
        r_io = self.straps.r_io_vr
        straddle(r_io, (io_x, io_y), self.io_vr_via_at)
        field.keep(r_io)
        self.add_via(self.io_vr_via_at, r_io.p2)
        self.plane_vias.append((Plane.LP4_1V1, self.io_vr_via_at))

        # The ring keeps out of the corridor the byte lanes take between the
        # two fields; the FPGA's circuit sits at the board's origin, so the
        # corridor's board frame is this field's frame.
        x0, y0, x1, y1 = BYTE_LANE_CORRIDOR
        corridor = box(x0, y0, x1, y1).buffer(CORRIDOR_MARGIN, join_style="mitre")
        self.place_decoupling(field, self.rail_caps(), [corridor])

    def decoupling_layouts(self) -> dict[str, RailLayout]:
        """Part 1's layouts, which leave out the capacitors a rail with no
        plane could not use (module docstring, "Left out"), with the small
        capacitors of :py:data:`UNPAIRED` sent to the ring. Fails if
        :py:data:`FPGA_PLANES` and Part 1's
        :py:data:`~.part1_fanout_escape.POURED_RAILS` name different
        rails."""
        if set(FPGA_PLANES) != POURED_RAILS:
            raise ValueError(
                f"Part 2 planes {sorted(FPGA_PLANES)}, Part 1 keeps the ring "
                f"capacitors of {sorted(POURED_RAILS)}"
            )
        layouts = dict(super().decoupling_layouts())
        for name, ring in UNPAIRED.items():
            layouts[name] = replace(layouts.get(name, RailLayout()), ring=ring)
        return layouts

    def rail_caps(self) -> list[RailCaps]:
        """Each decoupling set of the FPGA: the XPIO banks', every other
        rail's and VCCAUX_SMON's. Only the XPIO banks' ring may use the
        bottom edge, which faces the memory, and there only outside
        :py:data:`BYTE_LANE_CORRIDOR`, a design choice: the byte lanes and
        Part 1's strobe escapes leave the field there, and a ring via in
        their way leaves them no room (a build of Part 4's reference
        with a 1.1 V ring via at (0.92, -5.51) reported a route there as
        unrealizable for lack of space). A capacitor whose nearest position
        falls in the corridor slides along the edge to the nearest free one
        outside it (:py:func:`place_ring`)."""
        ic = self.fpga
        ground = list(ic.GND)
        sides = ("right", "left", "top")
        sets: list[RailCaps] = []
        for name, balls, bank in zip(
            XPIO_BANKS,
            (ic.VCCO_700, ic.VCCO_701, ic.VCCO_702),
            self.vcco_decoupling,
            strict=True,
        ):
            caps = bank.capacitors()
            sets.append(
                RailCaps(
                    balls,
                    ground,
                    tied(bank.short_traces, caps),
                    tied(bank.bulk_nets, caps),
                    FPGA_PLANES[name],
                    (*sides, "bottom"),
                )
            )
        for rail, dec in zip(fpga_rail_sets(self), self.decoupling.rails, strict=True):
            caps = dec.capacitors()
            sets.append(
                RailCaps(
                    rail.balls,
                    ground,
                    tied(dec.short_traces, caps),
                    tied(dec.bulk_nets, caps),
                    FPGA_PLANES.get(rail.name),
                    sides,
                )
            )
        # VCCAUX_SMON's capacitors return to GND_SMON (AM006 v1.5 Figure 1):
        # their return pads take a ball of that net.
        smon = self.decoupling.smon
        caps = smon.capacitors()
        sets.append(
            RailCaps(
                (ic.VCCAUX_SMON,),
                (ic.GND_SMON, ic.VREFP_500, ic.VREFN_500, ic.VP_500, ic.VN_500),
                tied(smon.short_traces, caps),
                tied(smon.bulk_nets, caps),
                None,
                sides,
            )
        )
        return sets


class PowerMemory(FanoutMemory, PowerParts):
    """Part 1's memory circuit with its ZQ resistors and capacitors placed on
    BOTTOM, and their vias."""

    def __init__(self) -> None:
        super().__init__()
        self.start_power()
        mem = self.memory
        field = Field(mem, MEMORY_PITCH)

        # Each ZQ resistor straddles its ZQ ball (p1) and the VDD2 ball beside
        # it in row A (p2, on the 1.1 V net).
        vdd2 = {id(b) for b in mem.VDD2}
        for r, zq in zip(self.straps.r_zq, (mem.ZQ0, mem.ZQ1), strict=True):
            beside = next(n for n in field.neighbours(zq) if id(n) in vdd2)
            straddle(r, field.xy(zq), field.xy(beside))
            field.keep(r)

        # The capacitors, each set on its own rail's balls. The edge facing
        # the FPGA (+y here) is where the LPDDR4 routes run.
        dec = self.decoupling
        caps = dec.capacitors()
        small = tied(dec.short_traces, caps)
        bulk = tied(dec.bulk_nets, caps)
        sides = ("right", "left", "bottom")
        rails = (
            (mem.VDDQ, Plane.LP4_1V1),
            (mem.VDD2, Plane.LP4_1V1),
            (mem.VDD1, Plane.LP4_VDD1),
        )
        sets = [
            RailCaps(
                balls,
                list(mem.VSS),
                [(c, b) for c, b in small if any(b is x for x in balls)],
                [(c, b) for c, b in bulk if any(b is x for x in balls)],
                plane,
                sides,
            )
            for balls, plane in rails
        ]
        self.place_decoupling(field, sets)


def to_board(shape: BaseGeometry, circuit: Circuit) -> BaseGeometry:
    """``shape``, in the frame of ``circuit``, in the frame of the circuit
    that holds it."""
    if circuit.transform is None:
        return shape
    return ShapelyGeometry(shape).apply(circuit.transform).g


def rail_outline(
    field: Field, balls: Sequence[Port], attachments: Sequence[Point] = ()
) -> BaseGeometry:
    """One rail's outline on its layer, in the field's frame, before the
    layer is split: each cluster's box of one-pitch cells, the clusters
    joined (:py:func:`join_boxes`), and each attachment point (a capacitor's
    or resistor's rail via) joined to the rail ball nearest it by
    :py:func:`channel_link`."""
    boxes = [
        box(*shapely.union_all([field.cell(field.xy(b)) for b in group]).bounds)
        for group in field.clusters(balls)
    ]
    shape = join_boxes(boxes)
    for at in attachments:
        nearest = min(balls, key=lambda b: math.dist(field.xy(b), at))
        shape = shape.union(channel_link(field, at, field.xy(nearest)))
    return shape


def channel_line(field: Field, axis: int, v: float, toward: float) -> float:
    """A coordinate along ``axis`` (1 for y, across ball rows; 0 for x,
    across columns) for a link to run on: ``v`` itself when it is more than
    a quarter pitch from every ball row or column, else ``v`` moved half a
    pitch toward ``toward``, which is midway between two rows or columns
    when ``v`` lies on one."""
    pitch = field.pitch[axis]
    steps = (v - field.bounds[axis]) / pitch
    if abs(steps - round(steps)) > 0.25:
        return v
    return v + (pitch / 2 if toward >= v else -pitch / 2)


def channel_link(field: Field, at: Point, ball: Point) -> BaseGeometry:
    """A strip joining ``at`` to ``ball`` that runs between ball rows and
    columns, never along one, so the vias of other nets beside it leave it
    the full channel between their voids (module docstring, pours). From a
    point beyond the field's left or right edge it runs along the channel
    beside ``at``'s row, then along the channel beside ``ball``'s column;
    otherwise along the channel beside ``at``'s column, then beside
    ``ball``'s row. Its width is :py:data:`LINK_WIDTH` plus
    :py:data:`PLANE_GAP`, the part :py:func:`split_layers` shrinks away."""
    x0, _, x1, _ = field.bounds
    if at[0] > x1 or at[0] < x0:
        cy = channel_line(field, 1, at[1], ball[1])
        cx = channel_line(field, 0, ball[0], at[0])
        path = [at, (at[0], cy), (cx, cy), (cx, ball[1]), ball]
    else:
        cx = channel_line(field, 0, at[0], ball[0])
        cy = channel_line(field, 1, ball[1], at[1])
        path = [at, (cx, at[1]), (cx, cy), (ball[0], cy), ball]
    return LineString(path).buffer(
        (LINK_WIDTH + PLANE_GAP) / 2, cap_style="square", join_style="mitre"
    )


def attach(
    field: Field,
    shape: BaseGeometry,
    balls: Sequence[Port],
    attachments: Sequence[Point],
) -> BaseGeometry:
    """``shape`` with each attachment point joined to it by the hull of the
    point's cell and the cell of the ball of ``balls`` nearest it."""
    for at in attachments:
        nearest = min(
            balls,
            key=lambda b: math.hypot(field.xy(b)[0] - at[0], field.xy(b)[1] - at[1]),
        )
        link = shapely.union_all([field.cell(at), field.cell(field.xy(nearest))])
        shape = shape.union(link.convex_hull)
    return shape


def join_boxes(boxes: Sequence[BaseGeometry]) -> BaseGeometry:
    """The boxes as one shape: each next box, the one nearest those already
    joined, joined by the hull of it and the joined box nearest it."""
    joined = [boxes[0]]
    rest = list(boxes[1:])
    shape = boxes[0]
    while rest:
        nxt, to = min(
            ((b, j) for b in rest for j in joined), key=lambda p: p[0].distance(p[1])
        )
        shape = shape.union(shapely.union_all([nxt, to]).convex_hull)
        joined.append(nxt)
        rest = [b for b in rest if b is not nxt]
    return shape


def split_layers(
    outlines: dict[Plane, BaseGeometry], gap: float
) -> dict[Plane, BaseGeometry]:
    """Each plane's pour: its outline less those of the planes before it
    on its layer, in :py:class:`Plane` order, then shrunk by half of
    ``gap``."""
    out: dict[Plane, BaseGeometry] = {}
    taken: dict[int, BaseGeometry] = {}
    for plane in Plane:
        layer = PLANES[plane]
        before = taken.get(layer, Polygon())
        own = outlines[plane].difference(before)
        taken[layer] = before.union(outlines[plane])
        out[plane] = own.buffer(-gap / 2, join_style="mitre")
    return out


class JS4PowerCircuit(JS4FanoutCircuit):
    """:py:class:`~.part1_fanout_escape.JS4FanoutCircuit` with Part 2's
    power: the resistors and capacitors placed with their vias (in the
    parts' circuits), the plane pours and the power rules."""

    def __init__(self) -> None:
        super().__init__()
        fpga, memory = self.fpga, self.memory
        if not isinstance(fpga, PowerFpga) or not isinstance(memory, PowerMemory):
            raise TypeError("Part 2 needs PowerFpga and PowerMemory")
        ic, mem = fpga.fpga, memory.memory

        # Each planed rail's net, which its pours join. LP4_1V1 already has
        # its name, from the base circuit.
        self.plane_nets = {
            Plane.VCCINT: Net([fpga.pwr_vccint.Vp], name="VCCINT"),
            Plane.LP4_1V1: Net([fpga.pwr_vcco_700.Vp]),
            Plane.VCCAUX: Net([fpga.pwr_vccaux.Vp], name="VCCAUX"),
            Plane.VCC_SOC: Net([fpga.pwr_vcc_soc.Vp], name="VCC_SOC"),
            Plane.LP4_VDD1: Net([mem.VDD1[0]], name="LP4_VDD1"),
        }
        PowerTag().assign(*self.plane_nets.values())

        fpga_field = Field(ic, FPGA_PITCH)
        memory_field = Field(mem, MEMORY_PITCH)

        def vias(part: PowerParts, plane: Plane) -> list[Point]:
            return [at for p, at in part.plane_vias if p is plane]

        def on_memory(balls: Sequence[Port], plane: Plane) -> BaseGeometry:
            # Under the memory each rail has its layer to itself: the whole
            # field, with each ring capacitor's rail via joined.
            shape = attach(
                memory_field, memory_field.outline(), balls, vias(memory, plane)
            )
            return to_board(shape, memory)

        vcco = [*ic.VCCO_700, *ic.VCCO_701, *ic.VCCO_702]
        xpio = to_board(rail_outline(fpga_field, vcco, vias(fpga, Plane.LP4_1V1)), fpga)
        under_memory = on_memory([*mem.VDDQ, *mem.VDD2], Plane.LP4_1V1)
        outlines = {
            Plane.VCCINT: rail_outline(fpga_field, ic.VCCINT, vias(fpga, Plane.VCCINT)),
            Plane.LP4_1V1: join_boxes([xpio, under_memory]),
            Plane.VCCAUX: rail_outline(fpga_field, ic.VCCAUX, vias(fpga, Plane.VCCAUX)),
            Plane.VCC_SOC: rail_outline(
                fpga_field, [*ic.VCC_SOC, *ic.VCC_IO], vias(fpga, Plane.VCC_SOC)
            ),
            Plane.LP4_VDD1: on_memory(mem.VDD1, Plane.LP4_VDD1),
        }
        for plane in (Plane.VCCINT, Plane.VCCAUX, Plane.VCC_SOC):
            outlines[plane] = to_board(outlines[plane], fpga)
        self.plane_shapes = split_layers(outlines, PLANE_GAP)
        self.plane_pours = {
            plane: Pour(ShapelyGeometry(shape).to_primitive(), layer=PLANES[plane])
            for plane, shape in self.plane_shapes.items()
        }
        for plane, pour in self.plane_pours.items():
            self.plane_nets[plane] += pour

        power_width = design_constraint(PowerTag(), priority=2).trace_width(POWER_WIDTH)
        # Priority ladder: 0 board defaults (the pour feature size); 1 each
        # plane layer's floors, its trace to pour form and its pour feature
        # size; 2 the power width; 3 a copy of the power width on a plane
        # layer, written by heavy_layer_rules only if the width were below
        # the floor. The board has no trace to pour rule, so the fabrication
        # floor stands in for it.
        self.power_rules: list[DesignConstraint] = [
            design_constraint(IsPour).pour_feature_size(POUR_FEATURE),
            power_width,
        ]
        for layer in PLANE_LAYERS_2OZ:
            self.power_rules += heavy_layer_rules(
                layer,
                HEAVY_MIN_WIDTH,
                HEAVY_MIN_CLEARANCE,
                Reference18FabRules.min_copper_copper_space,
                [power_width],
            )
            self.power_rules.append(
                design_constraint(
                    IsPour & OnLayer(layer), priority=1
                ).pour_feature_size(HEAVY_MIN_WIDTH)
            )

    def new_fpga(self) -> JS4Fpga:
        return PowerFpga()

    def new_memory(self) -> JS4Memory:
        return PowerMemory()


class JS4PowerDesign(Design):
    """Part 2's reference: Part 1's design with the resistors and capacitors
    placed, the plane pours and the power rules. No SI constraints."""

    board = Reference18Board()
    substrate = Reference18Substrate()
    circuit = JS4PowerCircuit()

"""The diplexer board: outline, holes, placement, code routes and copper.

Every coordinate below is the board frame: origin at the board centre, +x
right, +y up, mm. The element order is the approved rough path's. Nothing is
left to a placer: every part, route, via and pour is fixed in code.

Layout, from J1 (COMMON) to the junction tee and out along the two arms:

- COMMON: an ``RS_50`` line from J1's launch point along y = -0.125 to the tee.
- HIGH arm, along +x from the tee: C1 (series), node C with the C5 branch,
  C2 (series), node D with the C6 branch, then an ``RS_50`` line to J3's
  launch point. HIGH branches leave toward +y.
- LOW arm, along -y from the tee: L1 (series), node A with the C3 branch, L2
  (series), node B with the C4 branch, then an ``RS_50`` line to J2's
  launch point. LOW branches leave toward -x.

Geometry is derived from a small set of named constants (``*_CENTRE`` for the
series parts, ``NODE_*`` for the take-off points, ``*_LINE`` for the branch
lengths). Those are the numbers the run's HFSS campaign tuned.

Rules (one ladder, priorities in brackets; the line's four are
:py:mod:`.lines`'):

- [2] ``RFLineTag`` on the five signal nets applies a copy of the substrate's
  ``RS_50`` with a one-row via fence on each side (the substrate class is not
  ours to edit). The copy keeps RS_50's width, velocity and loss.
- [2] ``(RFLineTag, CoplanarGroundTag)`` sets the coplanar gap to the top
  pour. The runtime stands a pour ``POUR_GAP_OFFSET`` (0.01 mm, measured in
  ``layout_cpwg_two_row_fence``) past the winning clearance, so the copy and
  this rule ask for 0.12 mm and the realized gap is RS_50's 0.13 mm. No
  board-wide clearance above it exists, so nothing widens the gap
  (substrate docstring).
- [3] ``(LaunchPadTag, CoplanarGroundTag)``: the pour stands
  :py:data:`.lines.LAUNCH_PAD_GAP` (the line's 0.13 mm) off each jack's
  centre pad.
- [4] ``ExitNeckTag`` on each exit's neck: the neck structure and its gap
  (:py:mod:`.lines`, the run's launch tuning).
  The net's pair rule did not reach the pad: the pour stood at the 0.10 mm
  floor (0.11 realized) beside it.
- [4] ``BranchTag`` on each branch ``Route`` applies the 0.20 mm branch
  structure, beating the net's ``RS_50``.
- [5] ``(BranchTag, CoplanarGroundTag)`` at 0.8 mm holds the top pour off each
  branch line and each branch capacitor (the tag is on the part, so on its hot
  pad; its ground pad is on the pour's own net).
- The node A stub is node copper, not a branch line: it carries no
  ``BranchTag``, so its net's ``(RFLineTag, CoplanarGroundTag)`` rule holds the
  pour RS_50's coplanar gap off it, and its via keepout is that gap.
- ``StitchTag`` on the top pour: a ``StdVia`` grid stitching it to the bottom
  plane.

The branch keep-off rule measures from the whole branch route, which starts at
its node on the arm line's centreline, so on its own it pulls the top pour
back across the arm line too. Below node B the LOW line's far side (+x, away
from the C4 branch) carries its own GND pour (``low_line_ground``), untagged
for the branch rule, so ``RS_50``'s clearance alone sets its edge: the realized
gap is the line's 0.13 mm from node B to ``LOW_GAP_END_Y``. On the branch side
the 0.8 mm band under the C4 branch line reaches that same y, so the gap there
resumes at the band's end.

Via keepouts (``via=True`` only) cover each line's path and gap from the
board edge, each branch and its 0.8 mm keep-off, each jack ground pad (the
stitch grid's ``StdVia`` is not a via-in-pad via), and a disc round every
code-placed via, so no generated via lands where a line will route, in a
solder pad, or nearer a drill than ``min_hole_to_hole``.

Body keepouts (``pour=True, via=True``, top copper) sit under each of the
eight 0402 parts: its vendor body at the drawing's largest size
(:py:mod:`.bodies`) grown by ``BODY_CLEARANCE``, in the part's own frame.
Without them the ground pour, held off the signal pads only by the 0.12 mm
coplanar rule, filled the 0.54 mm gap between each series part's lands: a
ground strip under the body between two signal lands, a defect on a real
board (bridging risk under the part, a shunt path across it) and in the
run's solves (one of them shorted C2 and L2).

Each port is a Würth 60312202114514 edge-launch jack on its board edge,
launched as ``rf_connector_launch`` (``jitxexamples.patterns``) does: the
jack's origin on the edge with its +x into the board, a straight ``RS_50`` exit from the centre pad to a launch point on
the pad's axis, and a pour-and-via keepout cutting the bottom ground under the
centre pad and the start of the exit. Each jack's top and bottom ground pads
(the part straddles the edge) are joined by a row of open in-pad vias,
plated but not filled or capped, since JLCPCB fills no via on its Rogers
boards, and each pad lies in its layer's pour. The launch geometry and its
objects are :py:mod:`.launch`'s.

Top soldermask (``rf_mask_openings``): open over every signal conductor and
its coplanar slot. Each 50 ohm path, board edge to tee (the jack's centre
pad, exit and neck, the line, the series parts' lands, the node copper),
opens ``rf_slot_half_width()`` either side of its axis: the widest signal
copper on it plus the coplanar gap, plus ``mask_reach()`` onto the ground
beyond. Each branch line opens from its node to its capacitor's hot pad at
its own half width plus ``mask_reach()``; its 0.8 mm keep-off stays under
mask. The node A stub on C3's hot land opens at its own outline plus its
coplanar gap plus ``mask_reach()``. The lands keep their own openings.

Fabrication: the jacks' pads run to the board edge as the data sheet draws
them, an exemption from the 0.20 mm edge floor for those pads only, which the
runbook grants. The fab notes (``fab/fab-notes.txt`` beside this module) go to
JLCPCB with the exported packet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import shapely
from jitx import KeepOut, LayerSet
from jitx.board import Board
from jitx.circuit import Circuit, Route
from jitx.constraints import Tag, design_constraint
from jitx.controlpoint import RoutePoint
from jitx.copper import Copper, Pour
from jitx.design import Design
from jitx.feature import Cutout, Soldermask
from jitx.layerindex import Side
from jitx.net import Net, Port
from jitx.shapes import Shape
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle
from jitx.shapes.shapely import ShapelyGeometry
from jitx.si import RoutingStructure
from jitx.transform import Transform
from jitx.units import ohm
from jitxexamples.components.connectors.wurth_elektronik_60312202114514 import (
    CENTER_PAD_WIDTH,
)
from jitxlib.physics import phase_velocity

from .bodies import chip_body
from .launch import (
    JackPlacement,
    exit_route,
    ground_pad_keepouts,
    in_pad_via_keepoffs,
    in_pad_vias,
    launch_cutout,
    launch_point,
    neck_point,
    neck_route,
)
from .lines import (
    FLOOR_MARGIN,
    LAUNCH_PAD_GAP,
    PLANE_LAYER,
    RF_LAYER,
    CoplanarGroundTag,
    LaunchPadTag,
    RFLineTag,
    StitchTag,
    corridor,
    fenced_rs50,
    line_rules,
    via_keepoff,
)
from .network import Diplexer as DiplexerNetwork
from .substrate import DiplexerSubstrate

# ---------------------------------------------------------------- board

BOARD_SIZE = 31.75
"""Board outline, a square centred on the origin: the ZDPLX-592-S+ case
outline (runbook requirements)."""

MOUNTING_HOLE_DIAMETER = 3.18
"""Non-plated mounting holes (runbook requirements)."""

MOUNTING_HOLES = ((-12.700, 12.700), (12.700, -12.700))
"""Mounting hole centres: top-left and bottom-right, 25.40 mm apart each way
(runbook requirements)."""

J1_AT = JackPlacement(-BOARD_SIZE / 2, -0.125, 0)
"""COMMON jack: origin on the left edge, 16.00 mm from the top edge, +x into
the board (runbook requirements)."""
J2_AT = JackPlacement(0.125, -BOARD_SIZE / 2, 90)
"""LOW jack: origin on the bottom edge, 16.00 mm from the left edge, +x
(into the board) along board +y."""
J3_AT = JackPlacement(BOARD_SIZE / 2, -0.125, 180)
"""HIGH jack: origin on the right edge, 16.00 mm from the top edge."""

TEE = (0.125, -0.125)
"""The junction tee: where the COMMON line meets the LOW arm's axis."""

# ---------------------------------------------------------------- arms

PAD_OUTER = 0.75
"""0402 land pattern (jitxlib ``SMT("0402")``, as the passives resolve): each
pad's outer edge, from the part centre along its axis, mm."""

PAD_INNER = 0.27
"""0402 land pattern: each pad's inner edge, from the part centre, mm."""

PAD_HALF_WIDTH = 0.30
"""0402 land pattern: each pad's half width across the part axis, mm."""

MIN_BRANCH_SPACING = 3.0
"""Least distance between the two take-off points on one arm (the run's
layout assumption)."""

# source: the approved rough path, section 2
C3_LINE = 0.65
"""Branch line length at node A, arm-line copper edge to C3's pad edge, mm."""
# source: the user, reverting a campaign move whose solve failed every high-band floor
C4_LINE = 2.40
"""Branch line length at node B, to C4, mm."""
# source: the approved rough path, section 2
C5_LINE = 2.92
"""Branch line length at node C, to C5, mm."""
# source: the approved rough path, section 2
C6_LINE = 6.76
"""Branch line length at node D, to C6, mm."""

# Positions along each arm, measured from the tee, mm. The first series part
# sits as close to the tee as the 0402 pads allow: its tee-side pad starts
# the pad half width (0.30) + 0.10 / sqrt(2) past the tee, so its corner keeps the
# 0.10 mm minimum copper space to the other arm's first pad (1.121, rounded
# up to 1.125). Each first node sits where its 0.20 mm branch's near edge
# meets the end of that series part's far pad (1.125 + 0.75 + 0.10). The
# second node is MIN_BRANCH_SPACING further on, and the second series part
# sits midway between the two nodes.
L1_CENTRE = 1.125
"""L1 centre, from the tee along the LOW arm."""
NODE_A = 1.975
"""Node A take-off, from the tee along the LOW arm."""
L2_CENTRE = 3.475
"""L2 centre, from the tee along the LOW arm."""
NODE_B = 4.975
"""Node B take-off, from the tee along the LOW arm."""
C1_CENTRE = 1.125
"""C1 centre, from the tee along the HIGH arm."""
NODE_C = 1.975
"""Node C take-off, from the tee along the HIGH arm."""
C2_CENTRE = 3.475
"""C2 centre, from the tee along the HIGH arm."""
NODE_D = 4.975
"""Node D take-off, from the tee along the HIGH arm."""

BRANCH_WIDTH = 0.20
"""Branch line width (the approved rough path: 0.20 mm printed line)."""

BRANCH_EEFF = 2.55
"""Branch line effective permittivity (the approved rough path: 128 ohm,
eeff 2.55)."""

BRANCH_IMPEDANCE = 128
"""Branch line impedance (the approved rough path), a label on the width."""

BRANCH_POUR_CLEARANCE = 0.8
"""Top pour to each branch line and branch capacitor: at least 0.8 mm, so
the branch matches the microstrip model the rough path sized it with."""

# source: the run's campaign, approved by the user
NODE_A_STUB_LENGTH = 0.70
"""Node A shunt stub: how far it runs past C3's hot land, across the land's
axis toward L2 (board -y), mm. Its width is the land's length along the axis
(``PAD_OUTER - PAD_INNER``)."""

LOW_GAP_END_Y = TEE[1] - NODE_B - BRANCH_WIDTH / 2 - BRANCH_POUR_CLEARANCE
"""Board y where the C4 branch line's 0.8 mm band ends below the LOW line,
mm: node B less the branch half width and the keep-off (-6.0)."""

# ---------------------------------------------------------------- ground

TIP_VIA_HALF_PITCH = 0.40
"""Each branch capacitor's two ground vias sit this far either side of its
axis: centres 0.80 apart, so the 0.3 drills keep 0.50 apart, over the
substrate's 0.45 ``min_hole_to_hole``."""

TIP_VIA_SETBACK = 0.35
"""From the ground pad's outer edge to the tip vias' centres: the 0.4 via pad
stands 0.15 off the pad (StdVia is not for via-in-pad)."""

TIP_COPPER_HALF_WIDTH = 0.60
"""Half width of the ground copper joining the pad to its vias: it covers the
via pads (0.40 + 0.20)."""

BODY_CLEARANCE = DiplexerSubstrate.constraints.min_copper_copper_space
"""Body keepout margin past each chip body's largest outline, mm: the
fabricator's least copper-to-copper space (JLCPCB HF, 0.10 mm,
``jitxlib.jlcpcb.rules.JLCPCBRogersRules``), so no pour or via comes nearer the body than the board
lets any two foreign coppers stand."""


@dataclass(frozen=True)
class ArmGeometry:
    """One arm's layout from the tee: a unit direction along the arm, a unit
    direction for its branches, and distances along it."""

    direction: tuple[float, float]
    branch_direction: tuple[float, float]
    series_1: float
    node_1: float
    series_2: float
    node_2: float
    line_1: float
    line_2: float

    def __post_init__(self) -> None:
        if self.node_2 - self.node_1 < MIN_BRANCH_SPACING - 1e-9:
            raise ValueError(
                f"take-off points {self.node_1} and {self.node_2} are closer than "
                f"{MIN_BRANCH_SPACING} mm"
            )
        if not self.series_1 + PAD_OUTER <= self.node_1 - BRANCH_WIDTH / 2 + 1e-9:
            raise ValueError("node 1's branch overlaps the first series part")
        if not (
            self.node_1 + BRANCH_WIDTH / 2 <= self.series_2 - PAD_OUTER
            and self.series_2 + PAD_OUTER <= self.node_2 - BRANCH_WIDTH / 2
        ):
            raise ValueError("the second series part does not fit between the nodes")

    def point(self, s: float) -> tuple[float, float]:
        """The arm's centreline point ``s`` from the tee."""
        return (TEE[0] + s * self.direction[0], TEE[1] + s * self.direction[1])

    def series_rotation(self) -> float:
        """Rotation putting a two-pin part's p1 (its +y) toward the tee."""
        dx, dy = self.direction
        return math.degrees(math.atan2(-dy, -dx)) - 90

    def tip_rotation(self) -> float:
        """Rotation putting a branch capacitor's p1 (its +y) toward the arm."""
        bx, by = self.branch_direction
        return math.degrees(math.atan2(-by, -bx)) - 90

    def offset(self, node: float, reach: float) -> tuple[float, float]:
        """The point ``reach`` from the arm's centreline at ``node``, along
        the branch direction."""
        x, y = self.point(node)
        return (
            x + reach * self.branch_direction[0],
            y + reach * self.branch_direction[1],
        )

    def tip_centre(
        self, node: float, line: float, arm_half_width: float
    ) -> tuple[float, float]:
        """Centre of the branch capacitor at ``node``: past the arm copper
        edge by ``line``, then the hot pad's outer edge to the part centre."""
        x, y = self.point(node)
        reach = arm_half_width + line + PAD_OUTER
        return (
            x + reach * self.branch_direction[0],
            y + reach * self.branch_direction[1],
        )


HIGH_ARM = ArmGeometry(
    direction=(1.0, 0.0),
    branch_direction=(0.0, 1.0),
    series_1=C1_CENTRE,
    node_1=NODE_C,
    series_2=C2_CENTRE,
    node_2=NODE_D,
    line_1=C5_LINE,
    line_2=C6_LINE,
)
"""HIGH arm: along +x, branches toward +y."""

LOW_ARM = ArmGeometry(
    direction=(0.0, -1.0),
    branch_direction=(-1.0, 0.0),
    series_1=L1_CENTRE,
    node_1=NODE_A,
    series_2=L2_CENTRE,
    node_2=NODE_B,
    line_1=C3_LINE,
    line_2=C4_LINE,
)
"""LOW arm: along -y, branches toward -x."""


# ---------------------------------------------------------------- tags


class BranchTag(Tag):
    """Branch line routes and branch capacitors: 0.8 mm off the pour; the
    routes 0.20 mm."""


# ---------------------------------------------------------------- geometry


def node_bridge(arm: ArmGeometry, line_width: float) -> Shape:
    """The copper joining an arm's first series part to its first node, board
    frame: from the far pad's centre to the node, on the half of the line
    away from the branch. The router treats this copper as an obstacle, so any
    of it on the branch's side bends the branch round its corner."""
    pad_centre = arm.series_1 + (PAD_INNER + PAD_OUTER) / 2
    bx, by = arm.branch_direction
    off = -line_width / 4
    ax, ay = arm.point(pad_centre)
    nx, ny = arm.point(arm.node_1)
    return corridor(
        (ax + off * bx, ay + off * by), (nx + off * bx, ny + off * by), line_width / 4
    )


def mask_reach() -> float:
    """How far a top-mask opening runs past the edge of the copper or slot it
    exposes, mm: the fabricator's mask expansion
    (``solder_mask_registration``, 0 on JLCPCB's Rogers process, "Soldermask
    Expansion 1:1") plus ``FLOOR_MARGIN``, so the opening's edge never
    coincides with the slot's ground edge."""
    return DiplexerSubstrate.constraints.solder_mask_registration + FLOOR_MARGIN


def rf_slot_half_width() -> float:
    """Half width of the top-mask opening along each 50 ohm path, mm: the
    widest signal copper on it (the jack's centre pad, the ``RS_50`` trace
    or a 0402 land) plus the larger coplanar gap (line or launch pad), plus
    ``mask_reach()``."""
    top = DiplexerSubstrate.RS_50.layers[RF_LAYER]
    assert top.clearance is not None
    copper = max(top.trace_width / 2, CENTER_PAD_WIDTH / 2, PAD_HALF_WIDTH)
    return copper + max(top.clearance, LAUNCH_PAD_GAP) + mask_reach()


def node_a_stub(grow: float = 0.0) -> Shape:
    """The node A stub in a branch capacitor's land-pattern frame (lands'
    axis along y, hot land p1 at +y, width along x), grown by ``grow`` on
    every side. It covers the hot land from its centreline out to
    ``NODE_A_STUB_LENGTH`` past its +x edge (board -y once C3 is placed), so
    the copper beyond the land is ``PAD_OUTER - PAD_INNER`` by
    ``NODE_A_STUB_LENGTH`` and fused to the land."""
    far = PAD_HALF_WIDTH + NODE_A_STUB_LENGTH
    return rectangle(far + 2 * grow, PAD_OUTER - PAD_INNER + 2 * grow).at(
        far / 2, (PAD_INNER + PAD_OUTER) / 2
    )


def placed_at(xform: Transform, shape: Shape) -> Shape:
    """``shape`` moved into the frame ``xform``."""
    return xform * shape


# ---------------------------------------------------------------- circuits


class TipGround(Circuit):
    """A branch capacitor's ground: two ``StdVia`` beyond its ground pad (p2,
    the part's -y pad) and copper joining them to the pad. Placed with the
    capacitor's own transform.

    The copper starts ``start`` from the part centre, the end of the part's
    body keepout: it is wider than the pad, so nearer in it would lie beside
    the land under the body. It overlaps the pad's outer end from there."""

    gnd = Port()

    def __init__(self, start: float) -> None:
        overlap = PAD_OUTER - start
        if not (
            start > PAD_INNER
            and overlap >= DiplexerSubstrate.constraints.min_copper_width - 1e-9
        ):
            raise ValueError(
                f"tip copper start {start} leaves it no overlap with the pad"
            )
        y = -(PAD_OUTER + TIP_VIA_SETBACK)
        via = DiplexerSubstrate.StdVia
        sites = [(x, y) for x in (-TIP_VIA_HALF_PITCH, TIP_VIA_HALF_PITCH)]
        self.vias = [via().at(x, y) for x, y in sites]
        self.via_keepouts = [
            KeepOut(via_keepoff(xy, via), layers=LayerSet(RF_LAYER), via=True)
            for xy in sites
        ]
        far = PAD_OUTER + TIP_VIA_SETBACK + float(via.diameter) / 2
        self.copper = Copper(
            rectangle(2 * TIP_COPPER_HALF_WIDTH, far - start).at(
                0.0, -(start + far) / 2
            ),
            layer=RF_LAYER,
        )
        self.GND = Net([self.gnd, *self.vias, self.copper])


class DiplexerBoardCircuit(Circuit):
    """The network placed, routed and poured."""

    def __init__(self) -> None:
        n = DiplexerNetwork()
        self.network = n
        rs50 = DiplexerSubstrate.RS_50
        top = rs50.layers[RF_LAYER]
        assert top.clearance is not None
        arm_half = top.trace_width / 2
        gap = top.clearance
        fab = DiplexerSubstrate.constraints
        jacks_at = (J1_AT, J2_AT, J3_AT)

        # Jacks: origin on the board edge, +x into the board.
        for jack, at in zip((n.j1, n.j2, n.j3), jacks_at, strict=True):
            jack.at(at.transform)
            LaunchPadTag().assign(jack.landpattern.sig)

        # Series parts and branch capacitors.
        series = (
            (n.c1, HIGH_ARM, C1_CENTRE),
            (n.c2, HIGH_ARM, C2_CENTRE),
            (n.l1, LOW_ARM, L1_CENTRE),
            (n.l2, LOW_ARM, L2_CENTRE),
        )
        series_transforms = [
            Transform(arm.point(s), rotate=arm.series_rotation())
            for _, arm, s in series
        ]
        for (part, _, _), xf in zip(series, series_transforms, strict=True):
            part.at(xf)
        tips = (
            (n.c5, HIGH_ARM, NODE_C, C5_LINE),
            (n.c6, HIGH_ARM, NODE_D, C6_LINE),
            (n.c3, LOW_ARM, NODE_A, C3_LINE),
            (n.c4, LOW_ARM, NODE_B, C4_LINE),
        )
        tip_transforms = [
            Transform(arm.tip_centre(node, line, arm_half), rotate=arm.tip_rotation())
            for _, arm, node, line in tips
        ]
        for (part, _, _, _), xf in zip(tips, tip_transforms, strict=True):
            part.at(xf)
            BranchTag().assign(part)

        # Nothing but its own two lands under a chip part's body: no pour,
        # no generated via (body keepouts, module docstring).
        chips = [
            *zip((p for p, _, _ in series), series_transforms, strict=True),
            *zip((p for p, _, _, _ in tips), tip_transforms, strict=True),
        ]
        self.body_keepouts = [
            KeepOut(
                placed_at(xf, chip_body(part).keepout(BODY_CLEARANCE)),
                layers=LayerSet(RF_LAYER),
                pour=True,
                via=True,
            )
            for part, xf in chips
        ]

        # Control points: the tee, the four nodes, the three launch points.
        self.tee = RoutePoint(layer=RF_LAYER).at(TEE)
        self.node_a = RoutePoint(layer=RF_LAYER).at(LOW_ARM.point(NODE_A))
        self.node_b = RoutePoint(layer=RF_LAYER).at(LOW_ARM.point(NODE_B))
        self.node_c = RoutePoint(layer=RF_LAYER).at(HIGH_ARM.point(NODE_C))
        self.node_d = RoutePoint(layer=RF_LAYER).at(HIGH_ARM.point(NODE_D))
        # Fixed by the jack and the stated exit length (.launch).
        self.j1_launch = launch_point(J1_AT)
        self.j2_launch = launch_point(J2_AT)
        self.j3_launch = launch_point(J3_AT)
        self.j1_neck = neck_point(J1_AT)
        self.j2_neck = neck_point(J2_AT)
        self.j3_neck = neck_point(J3_AT)

        # Each first series part's far pad joins its node through fixed copper
        # (``node_bridge``): a route cannot, since the node's control point
        # already overlaps the pad ("Overlapping target shapes").
        self.c1_bridge = Copper(node_bridge(HIGH_ARM, top.trace_width), layer=RF_LAYER)
        self.l1_bridge = Copper(node_bridge(LOW_ARM, top.trace_width), layer=RF_LAYER)

        # Node A stub on C3's hot land, in C3's frame (``node_a_stub``): NODE_A
        # copper fused to the land's outer side; C3's body keepout is unchanged.
        # Node copper, not a branch: no ``BranchTag``, so the line's coplanar
        # rule sets its pour gap.
        c3_xf = dict(
            zip((part for part, _, _, _ in tips), tip_transforms, strict=True)
        )[n.c3]
        self.node_a_stub = Copper(placed_at(c3_xf, node_a_stub()), layer=RF_LAYER)

        # Signal nets, named as the network names them.
        self.COMMON = Net(
            [
                n.j1.sig,
                n.l1.p1,
                n.c1.p1,
                self.tee.port,
                self.j1_launch.port,
                self.j1_neck.port,
            ]
        )
        self.NODE_A = Net(
            [
                n.l1.p2,
                n.l2.p1,
                n.c3.p1,
                self.node_a.port,
                self.l1_bridge,
                self.node_a_stub,
            ]
        )
        self.LOW = Net(
            [
                n.l2.p2,
                n.c4.p1,
                n.j2.sig,
                self.node_b.port,
                self.j2_launch.port,
                self.j2_neck.port,
            ]
        )
        self.NODE_C = Net([n.c1.p2, n.c2.p1, n.c5.p1, self.node_c.port, self.c1_bridge])
        self.HIGH = Net(
            [
                n.c2.p2,
                n.c6.p1,
                n.j3.sig,
                self.node_d.port,
                self.j3_launch.port,
                self.j3_neck.port,
            ]
        )
        for net in (self.COMMON, self.NODE_A, self.LOW, self.NODE_C, self.HIGH):
            RFLineTag().assign(net)

        # Straight exits on each pad's axis: centre pad to neck point at
        # RS_50, then the neck to the launch point (.launch).
        self.exits = [
            exit_route(n.j1.sig, self.j1_neck),
            exit_route(n.j2.sig, self.j2_neck),
            exit_route(n.j3.sig, self.j3_neck),
        ]
        self.necks = [
            neck_route(self.j1_neck, self.j1_launch),
            neck_route(self.j2_neck, self.j2_launch),
            neck_route(self.j3_neck, self.j3_launch),
        ]

        # 50 ohm lines and arm sections.
        self.common_line = Route(self.tee, self.j1_launch, layer=RF_LAYER)
        self.high_routes = [
            Route(self.tee, n.c1.p1, layer=RF_LAYER),
            Route(self.node_c, n.c2.p1, layer=RF_LAYER),
            Route(self.node_d, n.c2.p2, layer=RF_LAYER),
            Route(self.node_d, self.j3_launch, layer=RF_LAYER),
        ]
        self.low_routes = [
            Route(self.tee, n.l1.p1, layer=RF_LAYER),
            Route(self.node_a, n.l2.p1, layer=RF_LAYER),
            Route(self.node_b, n.l2.p2, layer=RF_LAYER),
            Route(self.node_b, self.j2_launch, layer=RF_LAYER),
        ]

        # Branch lines: straight from each node to its capacitor's hot pad.
        self.branch_c5 = Route(self.node_c, n.c5.p1, layer=RF_LAYER)
        self.branch_c6 = Route(self.node_d, n.c6.p1, layer=RF_LAYER)
        self.branch_c3 = Route(self.node_a, n.c3.p1, layer=RF_LAYER)
        self.branch_c4 = Route(self.node_b, n.c4.p1, layer=RF_LAYER)
        for branch in (self.branch_c3, self.branch_c4, self.branch_c5, self.branch_c6):
            BranchTag().assign(branch)

        # Tip grounds, one per branch capacitor, in its own frame.
        self.tip_grounds = [
            TipGround(chip_body(part).keepout_reach(BODY_CLEARANCE)[1]).at(xf)
            for (part, _, _, _), xf in zip(tips, tip_transforms, strict=True)
        ]

        # Ground: the network's return, both pours, tip grounds, jack vias.
        self.GND = Net([n.gnd, *(t.gnd for t in self.tip_grounds)], name="GND")
        outline = rectangle(BOARD_SIZE, BOARD_SIZE)
        self.top_pour = Pour(outline, layer=RF_LAYER)
        self.bottom_pour = Pour(outline, layer=PLANE_LAYER)
        CoplanarGroundTag().assign(self.top_pour)
        StitchTag().assign(self.top_pour)
        self.GND += self.top_pour
        self.GND += self.bottom_pour

        # Line edge to past the branch rule's pull-back (branch half width plus
        # keep-off from node B's centre) by one gap, so the two pours join.
        node_b_x, node_b_y = LOW_ARM.point(NODE_B)
        far_x = node_b_x + BRANCH_WIDTH / 2 + BRANCH_POUR_CLEARANCE + gap
        top_y = node_b_y + BRANCH_WIDTH / 2
        self.low_line_ground = Pour(
            ShapelyGeometry(
                shapely.box(node_b_x + arm_half, LOW_GAP_END_Y, far_x, top_y)
            ),
            layer=RF_LAYER,
        )
        self.GND += self.low_line_ground

        # The bottom ground cut out under each centre pad and the start of its
        # exit (rf_connector_launch): no pour, no generated via.
        self.launch_cutouts = [launch_cutout(at) for at in jacks_at]

        # No generated via in a jack ground pad: StdVia is not a via-in-pad
        # via, and the shell's ground tabs are soldered there.
        self.ground_pad_keepouts = [
            ko for at in jacks_at for ko in ground_pad_keepouts(at)
        ]

        # No generated via on a line's path or in its gap. The stitch grid and
        # the fences are generated alongside the routes; without these, a
        # stitch or fence via placed before a line realized blocked it
        # ("Unable to find path"), differently from build to build. A via is
        # kept out when its pad touches the band, so a via held off it stands
        # at least the coplanar gap off the line, and the fence rows, whose
        # pads start past the gap, are untouched.
        line_band = arm_half + gap
        branch_band = BRANCH_WIDTH / 2 + BRANCH_POUR_CLEARANCE
        edges = [at.board(0.0, 0.0) for at in jacks_at]
        self.line_keepouts = [
            KeepOut(corridor(TEE, edge, line_band), layers=LayerSet(RF_LAYER), via=True)
            for edge in edges
        ] + [
            KeepOut(
                corridor(
                    arm.point(node), arm.tip_centre(node, line, arm_half), branch_band
                ),
                layers=LayerSet(RF_LAYER),
                via=True,
            )
            for _, arm, node, line in tips
        ]
        self.line_keepouts.append(
            KeepOut(
                placed_at(c3_xf, node_a_stub(gap)),
                layers=LayerSet(RF_LAYER),
                via=True,
            )
        )

        # The fenced RS_50 copy (.lines).
        self.rs50_fenced = fenced_rs50()
        self.branch_structure = RoutingStructure(
            {
                RF_LAYER: RoutingStructure.Layer(
                    trace_width=BRANCH_WIDTH,
                    clearance=fab.min_copper_copper_space,
                    velocity=phase_velocity(BRANCH_EEFF),
                    insertion_loss=top.insertion_loss,
                )
            },
            impedance=BRANCH_IMPEDANCE * ohm,
            name="Branch 0.20 mm",
        )

        # Jack ground: each top ground pad joined to the bottom one under it by
        # a row of open in-pad vias (.launch.in_pad_vias), each via
        # pad at least the edge floor plus FLOOR_MARGIN from the edge.
        self.jack_vias = [v for at in jacks_at for v in in_pad_vias(at)]
        for v in self.jack_vias:
            self.GND += v
        # Generated vias (stitch grid, fences) keep min_hole_to_hole from the
        # code-placed ones: the stitch grid does not see them.
        self.via_keepouts = [ko for at in jacks_at for ko in in_pad_via_keepoffs(at)]

        # Rule ladder: the line's (.lines), then the branches'.
        self.rules = [
            *line_rules(self.rs50_fenced, self.GND),
            design_constraint(BranchTag(), priority=4).routing_structure(
                self.branch_structure, ref_net=self.GND
            ),
            design_constraint(BranchTag(), CoplanarGroundTag(), priority=5).clearance(
                BRANCH_POUR_CLEARANCE
            ),
        ]

        # Top mask open over the signal copper and its slot (module docstring).
        branch_mask = BRANCH_WIDTH / 2 + mask_reach()
        self.rf_mask_openings = [
            Soldermask(corridor(TEE, edge, rf_slot_half_width()), side=Side.Top)
            for edge in edges
        ] + [
            Soldermask(
                corridor(
                    arm.point(node),
                    arm.offset(node, arm_half + line + mask_reach()),
                    branch_mask,
                ),
                side=Side.Top,
            )
            for _, arm, node, line in tips
        ]
        self.rf_mask_openings.append(
            Soldermask(placed_at(c3_xf, node_a_stub(gap + mask_reach())), side=Side.Top)
        )

        # Mounting holes.
        self.mounting_holes = [
            Cutout(Circle(diameter=MOUNTING_HOLE_DIAMETER).at(x, y))
            for x, y in MOUNTING_HOLES
        ]


class DiplexerBoard(Board):
    """31.75 mm square, centred on the origin."""

    shape = rectangle(BOARD_SIZE, BOARD_SIZE)


class Diplexer(Design):
    """The ZDPLX-592-S+ beater diplexer board."""

    substrate = DiplexerSubstrate()
    board = DiplexerBoard()
    circuit = DiplexerBoardCircuit()

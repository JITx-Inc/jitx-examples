"""Escape differential pairs from a hex-grid BGA: a narrow pair through the
ball field and the full pair outside it.

``HexBgaEscape`` takes two differential pairs out of a 7 by 8 hex-grid BGA
on a four-layer board to a two-lane chip 15 mm away. The BGA uses the
``HexBGA`` landpattern of the ``si_bga_optimization`` demo, at that demo's
1.0 mm ball pitch and 0.5 mm ball. Every ball that is not a signal is on
``GND``.

Vias. Each ``GND`` ball has a through via in its pad, ``GroundVia``, which
joins the ball to the ground planes on layers 1 and 3. Each signal ball has a
blind via in its pad, ``SignalVia``, from the top layer to layer 2, where the
pairs route as stripline between the two planes. Both are placed in code at
the ball centres, as the demo places them: they are via-in-pad on chosen
balls, which no via rule expresses. The far chip's pads take a ``SignalVia``
each the same way.

The ball field. On layer 2 the pair runs down the channel between two
columns of ground vias. Hex columns sit 1.0 mm x sqrt(3)/2 = 0.866 mm apart
and each via pad is 0.3 mm across, so the channel between pad edges is
0.866 - 0.3 = 0.566 mm. A pair needs its two traces, its pair gap and its
clearance on each side. The full pair takes 2 x 0.15 + 0.15 + 2 x 0.15 =
0.75 mm, which does not fit; the neck takes 2 x 0.08 + 0.1 + 2 x 0.08 =
0.42 mm, which does. So through the field the pair takes the neck structure
and outside it the full one. For another part, redo the sum with its pitch,
its via pad and your structures.

Narrowing by tag. Two routing structures do it, and the rules that apply
them are the ones ``layout_routing_structure_by_tag`` teaches, with that
pattern's tags:

1. ``design_constraint(SignalTag(), priority=2).routing_structure(full,
   ref_net=GND)`` on each pair's net gives every section the full structure.
2. A ``PairPoint`` just outside the field splits the coupled route in two.
   The inner section, from the ``PairInsertion`` below the pair's balls to
   that ``PairPoint``, carries ``EscapeNeckTag``, and
   ``design_constraint(EscapeNeckTag(), priority=4).routing_structure(neck,
   ref_net=GND)`` gives it the neck structure. The uncoupled legs from the
   two vias to the insertion carry the same tag, so they take the neck
   structure's uncoupled region. The higher priority wins where both rules
   match.

``layout_bga_escape`` passes a power trace between the balls of the same
``HexBGA`` with a narrower ``trace_width``. A differential pair needs its
trace width, pair gap and clearance to change together and the two traces
to stay coupled, which a routing structure carries and a ``trace_width``
rule does not, so this pattern narrows with structures.

The change happens at the ``PairPoint``. The point's own copper, centred on
it, changes from the neck's trace width to the full pair's, so the neck
route ends and the full route starts within about 0.1 mm of it. The
point sits ``TRANSITION_MARGIN`` below the field's lowest ball edge, far
enough that the full pair clears the last ground vias. Without the neck
rule, the routes through the field are not made: the issues report "Unable
to find path for requested route".

A ``DifferentialRoutingStructure`` with an ``uncoupled_region`` and a
``PairInsertion`` at the field edge also narrows the pair, but its legs run
uncoupled through the field and their gap drifts. A split at a ``PairPoint``
keeps the pair coupled at the neck structure's gap, which is why this
example uses it.

Fabrication limits. The neck, 0.08 mm traces 0.1 mm apart with 0.08 mm
clearance, is below the 0.127 mm floors of the sample fabrication
constraints, and a pair with all three at those floors, 5 x 0.127 =
0.635 mm, does not fit the 0.566 mm channel: the issues report "Unable to
find path for requested route". So the substrate states the limits of the
HDI fabricator this board assumes, ``HdiFabConstraints`` (0.075 mm line
and space, 0.15 mm drill), and every structure stays at or above them. A
routing structure takes precedence over the fabrication minimums and routes
at its own widths without raising an issue, so keeping it at or above the
floors is the designer's job; check realized copper with your fabricator's
design rule check.

Control points. The insertion point below each pair's balls and the
``PairPoint`` at the field edge are fixed by the ball geometry. The bend that
takes each full pair across to the chip's lane, and the insertion where the
pair splits for the chip's pads, are choices a designer would make in the
physical design view: they come from :py:func:`designer_placed_chip_side`,
in code so that the example builds complete. JITX's layout API refuses to
move a ``PairInsertion`` or ``PairPoint`` placed in code, so in a real
design leave these out of the code and place them in the view.

Structure labels. Each structure needs an impedance, and
``Substrate.differential_routing_structure`` looks structures up by it, as
jitxlib's protocol constraints do. The neck carries 0 ohm so that no
lookup for a real impedance returns it: a lookup for the pair's 100 ohm
returns the full pair.

The widths here are illustrative, not solved for an impedance.

The test, ``tests/test_hex_bga_escape.py``, checks the geometry offline: the
full pair does not fit the channel and the neck does, the transition clears
the field, and a ground via sits at every ground ball. With
``JITX_PATTERN_RUNTIME=1`` and a runtime started at the project root, it
builds the design and measures each section's width and gap, where the
transition falls, and that every route is made.
"""

from __future__ import annotations

from jitx.board import Board
from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.constraints import design_constraint
from jitx.controlpoint import PairInsertion, PairPoint
from jitx.copper import Pour
from jitx.inspect import visit
from jitx.landpattern import Pad, PadMapping
from jitx.layerindex import Side
from jitx.net import DiffPair, Net, Port, PortAttachment
from jitx.sample import SampleDesign, SampleFabConstraints, SampleStackup
from jitx.shapes.composites import rectangle
from jitx.si import DifferentialRoutingStructure, RoutingStructure
from jitx.substrate import Substrate
from jitx.toleranced import Toleranced
from jitx.units import ohm
from jitx.via import Via, ViaType
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import SMDPadConfig
from jitxlib.symbols.box import BoxSymbol

from jitxexamples.demos.si_bga_optimization.generic_bga import (
    BGA_BALL_DIAMETER,
    BGA_HPITCH,
    HexBGA,
)
from jitxexamples.patterns.layout_routing_structure_by_tag import (
    EscapeNeckTag,
    SignalTag,
)
from jitxexamples.patterns.si_parts import ExampleTwoLaneChip

BGA_ROWS = 7
BGA_COLS = 8

PAIR_BALLS = (((2, 4), (2, 3)), ((2, 6), (2, 5)))
"""Each pair's (P, N) balls as ``HexBGA.get_pad`` (row, column): rows counted
from 0, columns from 1. P is on the column offset half a pitch down, so P and
N are neighbours 1.0 mm apart across the channel the pair escapes down."""

ESCAPE_LAYER = 2
"""The stripline layer the pairs route on, between the planes on 1 and 3."""

PLANE_LAYERS = (1, 3)
"""The ground plane layers."""

BGA_ORIGIN = (0.0, 7.0)
CHIP_ORIGIN = (3.0, -8.0)

BOARD_WIDTH = 16.0
BOARD_HEIGHT = 30.0

INSERTION_DROP = 0.25
"""From the lower ball of a pair to the ``PairInsertion`` where its legs
join, in mm."""

TRANSITION_MARGIN = 0.5
"""From the field's lowest ball edge to the ``PairPoint`` where the neck
ends, in mm."""

CHIP_INSERTION_RISE = 2.0
"""From the far chip's pads to the ``PairInsertion`` above each lane, in mm:
a designer's choice, used by :py:func:`designer_placed_chip_side`."""

VELOCITY = 191335235228
"""Signal velocity for both structures, in mm/s: illustrative."""

INSERTION_LOSS = 0.0178
"""Insertion loss for both structures, in dB/mm: illustrative."""


class FourLayerStackup(SampleStackup):
    """The sample stackup with four copper layers."""

    def __init__(self) -> None:
        super().__init__(4)


class HdiFabConstraints(SampleFabConstraints):
    """The limits of the HDI fabricator this board assumes: 0.075 mm (3 mil)
    line and space, 0.15 mm drills with a 0.075 mm annular ring. Not any one
    fabricator's figures; take yours from its capability sheet."""

    min_copper_width = 0.075
    min_copper_copper_space = 0.075
    min_copper_hole_space = 0.15
    min_annular_ring = 0.075
    min_drill_diameter = 0.15
    min_hole_to_hole = 0.15


def _pair_layer(
    width: float, gap: float, clearance: float
) -> DifferentialRoutingStructure.Layer:
    return (
        DifferentialRoutingStructure.Layer(
            trace_width=width,
            pair_spacing=gap,
            clearance=clearance,
            velocity=VELOCITY,
            insertion_loss=INSERTION_LOSS,
        )
        .reference(PLANE_LAYERS[0], 1.0)
        .reference(PLANE_LAYERS[1], 1.0)
    )


def _leg_structure(name: str, width: float, clearance: float) -> RoutingStructure:
    layer = (
        RoutingStructure.Layer(
            trace_width=width,
            clearance=clearance,
            velocity=VELOCITY,
            insertion_loss=INSERTION_LOSS,
        )
        .reference(PLANE_LAYERS[0], 1.0)
        .reference(PLANE_LAYERS[1], 1.0)
    )
    return RoutingStructure(name=name, impedance=50 * ohm, layers={ESCAPE_LAYER: layer})


class HexEscapeSubstrate(Substrate):
    """Four copper layers, the HDI fabrication limits, the two vias and the
    two pair structures."""

    stackup = FourLayerStackup()
    constraints = HdiFabConstraints()

    class GroundVia(Via):
        """Through via in each ground ball's pad."""

        start_layer = 0
        stop_layer = -1
        diameter = 0.3
        hole_diameter = 0.15
        filled = True
        tented = Side.Top
        type = ViaType.MechanicalDrill
        via_in_pad = True

    class SignalVia(Via):
        """Blind via in each signal pad, from the top to the escape layer."""

        start_layer = 0
        stop_layer = ESCAPE_LAYER
        diameter = 0.3
        hole_diameter = 0.15
        filled = True
        tented = Side.Top
        type = ViaType.MechanicalDrill
        via_in_pad = True

    FULL_PAIR = DifferentialRoutingStructure(
        name="Full pair",
        impedance=100 * ohm,
        layers={ESCAPE_LAYER: _pair_layer(0.15, 0.15, 0.15)},
        uncoupled_region=_leg_structure("Full pair, uncoupled", 0.15, 0.15),
    )
    """The pair outside the field: 0.15 mm traces, 0.15 mm apart, 0.15 mm
    clearance."""

    NECK_PAIR = DifferentialRoutingStructure(
        name="Neck pair",
        impedance=0 * ohm,
        layers={ESCAPE_LAYER: _pair_layer(0.08, 0.1, 0.08)},
        uncoupled_region=_leg_structure("Neck pair, uncoupled", 0.08, 0.08),
    )
    """The pair in the field: 0.08 mm traces, 0.1 mm apart, 0.08 mm
    clearance. Its 0 ohm is a label that keeps impedance lookups on the full
    pair, not an impedance."""


class EscapeHexBGA(Component):
    """A placeholder 56-ball hex-grid BGA with two differential pairs. Not an
    orderable part.

    ``lanes[i]`` is on the balls ``PAIR_BALLS[i]``; every other ball is
    ``GND``.
    """

    manufacturer = "Fictional"
    mpn = "EXAMPLE-HEXBGA56"
    reference_designator_prefix = "U"

    lanes = [DiffPair() for _ in PAIR_BALLS]
    GND = [Port() for _ in range(BGA_ROWS * BGA_COLS - 2 * len(PAIR_BALLS))]

    landpattern = (
        HexBGA(
            num_rows=BGA_ROWS,
            num_cols=BGA_COLS,
            pitch=BGA_HPITCH,
            ball_diameter=BGA_BALL_DIAMETER,
        )
        .pad_config(SMDPadConfig())
        .package_body(
            RectanglePackage(
                width=Toleranced.exact(7.0),
                length=Toleranced.exact(7.5),
                height=Toleranced.min_max(0.8, 1.0),
            )
        )
    )
    symbol = BoxSymbol()

    def __init__(self) -> None:
        lp = self.landpattern
        entries: list[tuple[Port, Pad]] = []
        signal: list[Pad] = []
        for lane, (p_ball, n_ball) in zip(self.lanes, PAIR_BALLS, strict=True):
            p_pad, n_pad = lp.get_pad(*p_ball), lp.get_pad(*n_ball)
            entries += [(lane.p, p_pad), (lane.n, n_pad)]
            signal += [p_pad, n_pad]
        ground = [p for _, p in visit(lp, Pad) if all(p is not s for s in signal)]
        entries += list(zip(self.GND, ground, strict=True))
        self.mappings = [PadMapping(entries)]


def pad_centre(pad: Pad, origin: tuple[float, float]) -> tuple[float, float]:
    """A landpattern pad's centre in the circuit's frame, for a part placed
    at ``origin`` with no rotation."""
    assert pad.transform is not None
    x, y = pad.transform.translation
    return (origin[0] + float(x), origin[1] + float(y))


def designer_placed_chip_side(
    transitions: list[tuple[float, float]], lanes: list[tuple[float, float]]
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Each pair's bend and chip-side insertion, as (bend, insertion).

    ``lanes`` are the midpoints of each chip lane's two pads. A designer
    places these points in the physical design view, where the board's
    other routing shows what they have to clear. They are written here so
    the example builds complete: the insertion ``CHIP_INSERTION_RISE`` above
    the lane's pads, and the bend halfway down from the transition to it, on
    the lane's centreline.
    """
    points = []
    for start, lane in zip(transitions, lanes, strict=True):
        insertion = (lane[0], lane[1] + CHIP_INSERTION_RISE)
        points.append(((lane[0], (start[1] + insertion[1]) / 2), insertion))
    return points


class HexBgaEscape(Circuit):
    """Two pairs from a hex-grid BGA to a two-lane chip, narrowed in the
    ball field."""

    def __init__(self) -> None:
        self.bga = EscapeHexBGA().at(*BGA_ORIGIN)
        # Rotated 90 degrees so the pads lie along x, lane0 on the right.
        self.chip = ExampleTwoLaneChip().at(*CHIP_ORIGIN, rotate=90)
        lp = self.bga.landpattern

        self.gnd = Net(name="GND")
        for port in self.bga.GND:
            self.gnd += port
        self.planes = [
            Pour(rectangle(BOARD_WIDTH - 1, BOARD_HEIGHT - 1), layer=layer, rank=1)
            for layer in PLANE_LAYERS
        ]
        for plane in self.planes:
            self.gnd += plane

        signal_balls = {ball for pair in PAIR_BALLS for ball in pair}
        self.ground_vias = [
            HexEscapeSubstrate.GroundVia().at(*pad_centre(lp.get_pad(r, c), BGA_ORIGIN))
            for r in range(BGA_ROWS)
            for c in range(1, BGA_COLS + 1)
            if (r, c) not in signal_balls
        ]
        for via in self.ground_vias:
            self.gnd += via

        # The far chip's lanes, right to left, matched to the pairs left to
        # right so neither pair crosses the other. Its pads take its ports in
        # declaration order (``si_parts``).
        chip_lanes = [self.chip.lane1, self.chip.lane0]
        chip_ports = [self.chip.lane0.p, self.chip.lane0.n]
        chip_ports += [self.chip.lane1.p, self.chip.lane1.n]
        chip_placement = self.chip.transform
        assert chip_placement is not None
        chip_pad_xy: dict[int, tuple[float, float]] = {}
        for port, pad in zip(chip_ports, self.chip.landpattern.pads, strict=True):
            assert pad.transform is not None
            x, y = chip_placement * pad.transform.translation
            chip_pad_xy[id(port)] = (float(x), float(y))
        ball_field_bottom = min(
            pad_centre(p, BGA_ORIGIN)[1] for _, p in visit(lp, Pad)
        ) - (BGA_BALL_DIAMETER / 2)
        transition_y = ball_field_bottom - TRANSITION_MARGIN

        self.nets: list[Net] = []
        self.signal_vias: list[Via] = []
        self.attachments: list[PortAttachment] = []
        self.insertions: list[PairInsertion] = []
        self.transitions: list[PairPoint] = []
        self.bends: list[PairPoint] = []
        self.chip_insertions: list[PairInsertion] = []
        self.legs: list[Route] = []
        self.necks: list[Route] = []
        self.fulls: list[Route] = []
        self.chip_legs: list[Route] = []

        transition_xy: list[tuple[float, float]] = []
        chip_lane_xy: list[tuple[float, float]] = []
        for (p_ball, n_ball), far in zip(PAIR_BALLS, chip_lanes, strict=True):
            p_xy = pad_centre(lp.get_pad(*p_ball), BGA_ORIGIN)
            n_xy = pad_centre(lp.get_pad(*n_ball), BGA_ORIGIN)
            channel_x = (p_xy[0] + n_xy[0]) / 2
            transition_xy.append((channel_x, transition_y))
            far_p, far_n = chip_pad_xy[id(far.p)], chip_pad_xy[id(far.n)]
            chip_lane_xy.append(((far_p[0] + far_n[0]) / 2, far_p[1]))

        chip_side = designer_placed_chip_side(transition_xy, chip_lane_xy)

        for i, (lane, (p_ball, n_ball), far) in enumerate(
            zip(self.bga.lanes, PAIR_BALLS, chip_lanes, strict=True)
        ):
            net = Net([lane, far])
            SignalTag().assign(net)
            self.nets.append(net)

            p_xy = pad_centre(lp.get_pad(*p_ball), BGA_ORIGIN)
            n_xy = pad_centre(lp.get_pad(*n_ball), BGA_ORIGIN)
            vias = {
                "p": HexEscapeSubstrate.SignalVia().at(*p_xy),
                "n": HexEscapeSubstrate.SignalVia().at(*n_xy),
                "far_p": HexEscapeSubstrate.SignalVia().at(*chip_pad_xy[id(far.p)]),
                "far_n": HexEscapeSubstrate.SignalVia().at(*chip_pad_xy[id(far.n)]),
            }
            self.signal_vias += vias.values()
            self.attachments += [
                PortAttachment(lane.p, vias["p"]),
                PortAttachment(lane.n, vias["n"]),
                PortAttachment(far.p, vias["far_p"]),
                PortAttachment(far.n, vias["far_n"]),
            ]

            channel_x = transition_xy[i][0]
            insertion = PairInsertion(layer=ESCAPE_LAYER).at(
                (channel_x, min(p_xy[1], n_xy[1]) - INSERTION_DROP), rotate=-90
            )
            transition = PairPoint(layer=ESCAPE_LAYER).at(transition_xy[i], rotate=-90)
            bend_xy, chip_insertion_xy = chip_side[i]
            bend = PairPoint(layer=ESCAPE_LAYER).at(bend_xy, rotate=-90)
            chip_insertion = PairInsertion(layer=ESCAPE_LAYER, invert=True).at(
                chip_insertion_xy, rotate=90
            )
            self.insertions.append(insertion)
            self.transitions.append(transition)
            self.bends.append(bend)
            self.chip_insertions.append(chip_insertion)
            self.attachments += [
                PortAttachment([lane.p, lane.n], insertion),
                PortAttachment([lane.p, lane.n], transition),
                PortAttachment([lane.p, lane.n], bend),
                PortAttachment([far.p, far.n], chip_insertion),
            ]

            legs = [
                Route(vias["p"], insertion.uncoupled.p, ESCAPE_LAYER),
                Route(vias["n"], insertion.uncoupled.n, ESCAPE_LAYER),
            ]
            neck = Route(insertion.coupled, transition.back, ESCAPE_LAYER)
            for route in (*legs, neck):
                EscapeNeckTag().assign(route)
            self.legs += legs
            self.necks.append(neck)
            self.fulls += [
                Route(transition.front, bend.back, ESCAPE_LAYER),
                Route(bend.front, chip_insertion.coupled, ESCAPE_LAYER),
            ]
            self.chip_legs += [
                Route(chip_insertion.uncoupled.p, vias["far_p"], ESCAPE_LAYER),
                Route(chip_insertion.uncoupled.n, vias["far_n"], ESCAPE_LAYER),
            ]

        # Priority ladder of layout_routing_structure_by_tag: 2 for the net
        # tag, 4 for the escape sections.
        self.full_rule = design_constraint(SignalTag(), priority=2).routing_structure(
            HexEscapeSubstrate.FULL_PAIR, ref_net=self.gnd
        )
        self.neck_rule = design_constraint(
            EscapeNeckTag(), priority=4
        ).routing_structure(HexEscapeSubstrate.NECK_PAIR, ref_net=self.gnd)


class HexEscapeBoard(Board):
    """A 16 by 30 mm board."""

    shape = rectangle(BOARD_WIDTH, BOARD_HEIGHT, radius=1)


class hex_bga_escape_design(SampleDesign):
    """Two pairs escaping a hex-grid BGA on a four-layer HDI board."""

    substrate = HexEscapeSubstrate()
    board = HexEscapeBoard()
    circuit = HexBgaEscape()

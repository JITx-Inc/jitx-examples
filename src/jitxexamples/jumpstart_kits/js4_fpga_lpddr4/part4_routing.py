"""JS4 Part 4: channel B's two byte lanes routed, on Part 3's reference.

:py:class:`JS4RoutingCircuit` subclasses Part 3's
:py:class:`~.part3_si_constraints.JS4SIConstraintsCircuit`, which is built
on Part 2's :py:class:`~.part2_power.JS4PowerCircuit`, which is built on
Part 1's circuit. So it holds Part 2's decoupling, plane pours and power
rules (:py:mod:`.part2_power`) and Part 3's SI constraints and spacing
rules (:py:mod:`.part3_si_constraints`), and its parts' circuits are Part
2's.

Part 4 routes every DQ, DMI and DQS of channel B's byte lanes 0 and 1
(``ch[1].d[0]`` and ``ch[1].d[1]``) on :py:data:`~.part1_fanout_escape.CHANNEL_B_LAYER`,
along the paths of a reference layout (:py:mod:`.part4_reference_routes`):

- Each DQ and DMI: from its fanout via in the FPGA ball to its fanout via
  in the memory ball, untagged, so it keeps the 46 ohm structure inside
  the ball fields too (:py:mod:`.ball_field`). A line with a
  length-matching section has a route point at each end of it, attached
  to the line's memory ball; a line with none is one route from via to
  via.
- Each DQS: the coupled middle section from Part 1's FPGA pair point to its
  memory pair point, through two pair points of its own attached to the
  memory's DQS balls, which bound its length-matching section.

Control points sit only where they are needed: at a tag transition (Part
1's pair points, where a strobe's ball-field segment ends) and at each end
of a length-matching section. The paths' turns guide the router between
them.

The routes fix the pin assignment. The FPGA offers a byte swap within
channel B and a bit swap within a byte; a route between two balls is one of
those choices, and the runtime resolves the assignment to the one the routes
match. Byte lane 0 leaves the FPGA from byte slot 3 and byte lane 1 from
slot 2, where Part 1's strobe escapes leave them.

Length matching is by serpentines inside length-matching sections, which
the router lengthens to meet Part 3's timing constraints:

- A data line with a length-matching section has it where the reference
  layout matches that line's length.
- Each strobe pair has a length-matching section between its own two pair
  points, with a tighter serpentine pitch on the pair tag
  (:py:data:`PAIR_SERPENTINE_PITCH`) so it can take more length in its
  room.
"""

from jitx.circuit import Circuit, Route
from jitx.constraints import design_constraint
from jitx.controlpoint import PairPoint, RoutePoint
from jitx.design import Design
from jitx.net import Port, PortAttachment
from jitx.transform import Point
from jitx.via import Via

from jitxexamples.protocols.memory.lpddr4 import LPDDR4ConstraintParams
from jitxexamples.substrates.reference_18layer import (
    Reference18Board,
    Reference18FabRules,
    Reference18Substrate,
    mil,
)

from ..vp1002_lpddr4.pinout import LPDDR4_X32
from .constraint import KIT_PARAMS
from .part1_fanout_escape import (
    CHANNEL_B_LAYER,
    FPGA_INVERT,
    FanoutFpga,
    FanoutMemory,
)
from .part3_si_constraints import LOSS_LIMIT_DB, JS4SIConstraintsCircuit
from .part4_reference_routes import (
    BYTE_SLOTS,
    DMI_PATHS,
    DQ_BITS,
    DQ_PATHS,
    PAIR_PATHS,
    LinePath,
    PairPath,
    Turns,
)
from .rules import LPDDR4PairTag

LINE_ENVELOPE = 0.4
"""Envelope overhead, mm, of a data line's length-matching section unless its
path gives its own: the room its serpentines may take beyond its copper,
half each side. A design choice: the route points that end a section grow
to it, and 0.4 mm keeps those ends clear of the lines beside them at the
line structure's clearance."""

PAIR_ENVELOPE = 0.3
"""Envelope overhead, mm, of a strobe pair's length-matching section. A
design choice, the same way: at 0.3 mm the pair points that end each
section, and the serpentines between them, leave the lines beside them
room in the reference build (no ``Unrealizable`` group)."""

PAIR_SERPENTINE_PITCH = (
    2 * mil(3.55) + mil(6.45) + (Reference18FabRules.min_copper_copper_space)
)
"""Smallest serpentine pitch, mm, on a strobe or clock pair (0.415 mm): one
coupled segment of the 85 ohm differential structure on L3 (two 3.55 mil
traces 6.45 mil apart) plus the substrate's minimum copper to copper space,
so adjacent turns of a pair's serpentine sit at that minimum space. A design
choice: a tighter pitch than the router's default lets a pair take more
length in the same room."""


def board_position(part: Circuit, ob: Via | PairPoint) -> Point:
    """Board position of a via or pair point held by ``part``, a child
    circuit of the one that declares the routes."""
    if ob.transform is None:
        raise ValueError(f"{ob} is not placed")
    frame = ob.transform if part.transform is None else part.transform * ob.transform
    x, y = frame * (0.0, 0.0)
    return (float(x), float(y))


def sketch(start: Point, turns: Turns, end: Point) -> Route.Sketch | None:
    """A sketch through ``turns``, or none for a leg with no turns."""
    if not turns:
        return None
    return Route.Sketch(
        Route.Sketch.Terminal(start), list(turns), Route.Sketch.Terminal(end)
    )


class JS4RoutingCircuit(JS4SIConstraintsCircuit):
    """Part 3's circuit, with channel B's two byte lanes routed."""

    def __init__(
        self,
        params: LPDDR4ConstraintParams = KIT_PARAMS,
        loss: float = LOSS_LIMIT_DB,
    ) -> None:
        super().__init__(params=params, loss=loss)
        fpga = self.fpga
        memory = self.memory
        if not isinstance(fpga, FanoutFpga) or not isinstance(memory, FanoutMemory):
            raise TypeError("Part 4 routes from Part 1's fanout and escapes")
        self.route_points: list[RoutePoint] = []
        self.control_point_attachments: list[PortAttachment] = []
        self.line_routes: list[Route] = []
        self.pair_points: list[PairPoint] = []
        self.pair_routes: list[Route] = []

        fpga_points = {
            slot: point
            for (slot, _, _), point in zip(
                fpga.escape_pairs(), fpga.escape_points, strict=True
            )
        }
        for lane_index, lane in enumerate(memory.memory.lpddr4.ch[1].d):
            slot = LPDDR4_X32.slots[BYTE_SLOTS[lane_index]]
            fpga_balls = [
                *(fpga.fpga_pin(slot.dq[k]) for k in DQ_BITS[lane_index]),
                fpga.fpga_pin(slot.dmi),
            ]
            memory_balls = [*lane.dq, lane.dmi]
            paths = [
                *(DQ_PATHS[lane_index, bit] for bit in range(len(lane.dq))),
                DMI_PATHS[lane_index],
            ]
            for fpga_ball, memory_ball, path in zip(
                fpga_balls, memory_balls, paths, strict=True
            ):
                self.line(fpga_ball, memory_ball, path)
            self.pair(
                fpga_points[BYTE_SLOTS[lane_index]],
                memory.escape_points[lane_index],
                [lane.dqs.p, lane.dqs.n],
                PAIR_PATHS[lane_index],
            )

        self.pair_serpentine = design_constraint(
            LPDDR4PairTag(), priority=8
        ).serpentine_params(min_pitch=PAIR_SERPENTINE_PITCH)

    def pair(
        self,
        fpga_point: PairPoint,
        memory_point: PairPoint,
        memory_balls: list[Port],
        path: PairPath,
    ) -> None:
        """Route one strobe pair's middle section from ``fpga_point`` to
        ``memory_point`` along ``path``, through two pair points attached to
        ``memory_balls``, its length-matching section between them. They
        face the memory with the FPGA pair point's polarity, so each joins
        the leg before it at its back."""
        fpga, memory = self.fpga, self.memory
        assert isinstance(fpga, FanoutFpga) and isinstance(memory, FanoutMemory)
        points = [
            PairPoint(layer=CHANNEL_B_LAYER, invert=FPGA_INVERT).at(
                (p.x, p.y), rotate=p.heading
            )
            for p in path.points
        ]
        self.pair_points += points
        self.control_point_attachments += [
            PortAttachment(memory_balls, point) for point in points
        ]
        starts = [fpga_point.front, *(p.front for p in points)]
        ends = [*(p.back for p in points), memory_point.front]
        positions = [
            board_position(fpga, fpga_point),
            *((p.x, p.y) for p in path.points),
            board_position(memory, memory_point),
        ]
        for k, turns in enumerate(path.legs):
            config = None
            if k == 1:
                config = Route.Config(envelope_overhead=PAIR_ENVELOPE)
            self.pair_routes.append(
                Route(
                    starts[k],
                    ends[k],
                    CHANNEL_B_LAYER,
                    sketch(positions[k], turns, positions[k + 1]),
                    config=config,
                )
            )

    def line(self, fpga_ball: Port, memory_ball: Port, path: LinePath) -> None:
        """Route one data line from the fanout via in ``fpga_ball`` to the
        one in ``memory_ball`` along ``path``: one route, or, around a
        length-matching section, three, joined at route points attached to
        ``memory_ball``. No route carries a tag."""
        fpga = self.fpga
        memory = self.memory
        assert isinstance(fpga, FanoutFpga) and isinstance(memory, FanoutMemory)
        fpga_via = fpga.fanout_via(fpga_ball)
        memory_via = memory.fanout_via(memory_ball)
        if len(path.points) not in (0, 2) or len(path.legs) != len(path.points) + 1:
            raise ValueError(
                f"{len(path.legs)} legs for {len(path.points)} route points: "
                "a line takes one leg and no points, or three legs and two"
            )
        points = [
            RoutePoint(layer=CHANNEL_B_LAYER).at((p.x, p.y), rotate=p.heading)
            for p in path.points
        ]
        self.route_points += points
        self.control_point_attachments += [
            PortAttachment(memory_ball, point) for point in points
        ]
        ends: list[Via | RoutePoint] = [fpga_via, *points, memory_via]
        positions = [
            board_position(fpga, fpga_via),
            *((p.x, p.y) for p in path.points),
            board_position(memory, memory_via),
        ]
        for k, turns in enumerate(path.legs):
            config = None
            if points and k == 1:
                envelope = LINE_ENVELOPE if path.envelope is None else path.envelope
                config = Route.Config(envelope_overhead=envelope)
            self.line_routes.append(
                Route(
                    ends[k],
                    ends[k + 1],
                    CHANNEL_B_LAYER,
                    sketch(positions[k], turns, positions[k + 1]),
                    config=config,
                )
            )


class JS4RoutingDesign(Design):
    """Part 4's reference: Part 3's design, with channel B's two byte lanes
    routed."""

    board = Reference18Board()
    substrate = Reference18Substrate()
    circuit = JS4RoutingCircuit()

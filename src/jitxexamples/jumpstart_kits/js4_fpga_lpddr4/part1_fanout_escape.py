"""JS4 Part 1: fanout and escape, the layout's first step, in code.

:py:class:`JS4FanoutCircuit` takes the connected board of :py:mod:`.base`
and lays down one via and routing strategy for both parts:

- Placement. The FPGA stays where the base design places it. The memory
  sits below the FPGA's LPDDR4 banks at (6.4509, -17.3772) mm on the board,
  turned 180 degrees, a design choice: to balance length across the data
  lanes (:py:data:`MEMORY_AT`).
- Layers, from UG863's layout rules as :py:mod:`.constraint` lists them (a
  byte's data and strobe on one internal layer, command, address and clock on
  one internal layer, data no deeper than 45 mil) and DIFF-85's inner layers,
  L3, L5 and L7. Channel B's bytes take L3_SIG1 (:py:data:`CHANNEL_B_LAYER`)
  under the FPGA and between the parts, so channel A's go to L5_SIG2 (14.2 mil
  below the top of TOP's copper, by the stackup table), reached by the fanout's
  through vias: the substrate has no TOP to L5 laser via. Both channels' CA,
  CS, CKE and CK go on L7_SIG3.
- Fanout. One through via at the centre of the pad of every FPGA ball but
  those the pinout names NC, and of every memory ball but NC and DNU. At
  the FPGA that includes the balls no net reaches yet (unused I/O and
  transceiver pins, the system clock, VCCINT_SENSE), a design choice that
  keeps every pin available to a later part. The NC balls get none: the
  kit leaves them unconnected, so no later part needs them
  (:py:meth:`FanoutFpga.fpga_balls`).
- Ground. A GND pour over the board outline on each of the eight ground
  layers, L2, L4, L6, L8, L11, L13, L15 and L17, held by the ground vias.
- Escape. Channel B's two DQS pairs, the ones Part 4 will route, leave each
  part's ball field on L3 on route segments tagged
  :py:class:`~.ball_field.BallFieldPairTag`, from the pair's two fanout vias
  through a ``PairInsertion`` beside them to a ``PairPoint`` just outside the
  field, where routing continues on the full pair structure.
  :py:func:`~.ball_field.ball_field_rules` gives the tagged segments the
  ball-field pair structure. Those two are the escape's only control
  points: the insertion where its two legs couple, and the pair point where
  the tag ends. No other pair escapes in code.
- Decoupling. The base design's capacitors stay unplaced, and the FPGA's
  circuit never creates the 27 that Part 2 (:py:mod:`.part2_power`) would
  have nowhere to put where they decouple anything
  (:py:meth:`FanoutFpga.decoupling_layouts`). Part 2 pours five rails, and
  puts a capacitor of 10 uF and up in a ring outside the ball field on its
  own via to its rail's pour, which on any other rail would join nothing.
  So on each FPGA rail Part 2 does not pour (:py:data:`POURED_RAILS`), the
  design has no capacitor of 10 uF and up (19 of them), and none of the
  eight below 10 uF that Part 2's field placement finds no free pair of
  ball vias for (:py:data:`NO_FIELD_PAIR`), which would go to the ring too.
  It holds 59 of the base design's 86 capacitors: 44 of the FPGA's 71 and
  all 15 of the memory's, whose rails Part 2 pours.

Each part's copper sits in the part's own circuit, so it moves when the
part's circuit moves: the FPGA's vias, insertions, pair points and escape
routes in :py:class:`FanoutFpga`, the memory's in :py:class:`FanoutMemory`.
The memory sits at its circuit's origin turned 180 degrees, and its circuit
is what is placed. The pours cover the whole board and stay in
:py:class:`JS4FanoutCircuit`.

Escape positions. Each escape's insertion and pair point sit at the
position and heading :py:mod:`.reference_escapes` gives, in the circuit of
the part they belong to: the control points of a reference layout of
channel B's two byte lanes on this board, memory at (6.4509, -17.3772)
turned 180. The FPGA's are keyed by byte slot
(:py:meth:`FanoutFpga.escape_pairs`), the memory's by byte lane
(:py:meth:`FanoutMemory.escape_pairs`).

Pair polarity, by :py:class:`jitx.controlpoint.PairInsertion` and
:py:class:`jitx.controlpoint.PairPoint`: an insertion's coupled end joins
the back of a pair point with the same ``invert`` flag, and two pair points
whose flags differ join front to front. Each part's insertions and pair
points share one flag, inverted at the FPGA and not at the memory
(:py:data:`FPGA_INVERT`), which at the saved headings keeps each
insertion's P leg on its P via's side. Whichever of channel B's bytes the
pin assignment puts in either of its slots, its two pair points then join
without P and N crossing between the parts.

Via size. Each fanout via is ``THVia_6p0``, the smallest drill the
substrate offers TOP to BOTTOM, a design choice: it leaves the most room
between pads for the ball-field routes. Its pad is 0.252 mm (the drill plus
two IPC-2221B 0.050 mm rings,
:py:func:`~jitxexamples.substrates.reference_18layer.via_pad`), inside the
VP1002's 0.51 mm land and the memory's 0.40 mm ball pad. With a full pad on
both neighbours, the narrowest case on an inner layer, the gaps between
neighbouring pads and what fits in them are:

- FPGA, 0.92 mm pitch both ways: 26.28 mil. The ball-field pair fits (17.2 mil,
  :py:attr:`~jitxexamples.substrates.reference_18layer.Reference18Substrate.DRS_85_FIELD`),
  as do two ``SE_46`` lines (24.8 mil: 3.1 mil wide, 6.2 mil clearance).
- Memory columns, 0.8 mm pitch: 21.56 mil. The ball-field pair fits, as
  does one ``SE_46`` line (15.5 mil), but not two ``SE_46`` lines.
- Memory rows, 0.65 mm pitch: 15.65 mil. One ``SE_46`` line fits; the pair
  does not.

Two more design choices at the memory. Its escapes take ``DRS_85_FIELD``,
documented for a 0.92 mm field, at its 0.8 by 0.65 mm field, because the
pair fits between its columns and the substrate has no structure for that
pitch. And they take UG863's under-device spacing, because the
:py:class:`~.ball_field.BallFieldTag` that gives them the narrower
structure is also the spacing rules' under-device tag.

The design applies no SI constraints; :py:mod:`.part3_si_constraints` adds
them on top of Part 2's circuit (:py:mod:`.part2_power`), which builds on
this one.
"""

from types import MappingProxyType

from jitx.circuit import Route
from jitx.component import Component
from jitx.controlpoint import PairInsertion, PairPoint
from jitx.copper import Pour
from jitx.design import Design
from jitx.inspect import extract, visit
from jitx.landpattern import Pad, PadMapping
from jitx.net import Port, PortAttachment
from jitx.shapes.composites import rectangle
from jitx.via import Via

from jitxexamples.protocols.memory.lpddr4 import LPDDR4Lane
from jitxexamples.substrates.reference_18layer import (
    BOARD_CORNER_RADIUS,
    BOARD_HEIGHT,
    BOARD_WIDTH,
    L3,
    Reference18Board,
    Reference18Substrate,
)

from ..vp1002_lpddr4.decoupling import BULK_CAPACITANCE, RailLayout, fpga_sets
from ..vp1002_lpddr4.pinout import LPDDR4_X32, Channel, Pos
from .ball_field import BallFieldPairTag, ball_field_rules
from .base import JS4BaseCircuit, JS4Fpga, JS4Memory
from .reference_escapes import FPGA_ESCAPES, MEMORY_ESCAPES, PairEscape

THROUGH_VIA = Reference18Substrate.THVia_6p0
"""The via in every fanout pad: the smallest plated drill on the
substrate's TOP to BOTTOM chart, 6.0 mil, 0.252 mm pad. Smallest is a design
choice: it leaves the most room between pads for the ball-field routes."""

CHANNEL_B_LAYER = L3
"""Channel B's bytes: L3_SIG1, a design choice, the layer the reference
layout of channel B's byte lanes puts them on."""

GROUND_LAYERS = (1, 3, 5, 7, 10, 12, 14, 16)
"""L2_GND, L4_GND, L6_GND, L8_GND_1OZ, L11_GND_1OZ, L13_GND, L15_GND and
L17_GND: every ground layer of the substrate's stackup."""

MEMORY_AT = (6.4509, -17.3772)
"""Where the memory's circuit sits on the board, mm, at 0 degrees, so the
memory, turned 180 degrees in it, sits there turned 180: below the FPGA's
LPDDR4 banks with channel B's end toward them. A design choice, to balance
length across the data lanes."""

POURED_RAILS = frozenset(
    {"VCCO_700", "VCCO_701", "VCCO_702", "VCCINT", "VCC_SOC", "VCC_IO", "VCCAUX"}
)
"""The FPGA rails Part 2 pours, by the set names of
:py:func:`~..vp1002_lpddr4.decoupling.fpga_sets`: the VCCO of XPIO banks 700
to 702 (on the 1.1 V net), VCCINT, VCC_SOC with VCC_IO (one net) and
VCCAUX. On every other FPGA rail the design creates no capacitor that Part
2 would put in its ring (module docstring, "Decoupling")."""

NO_FIELD_PAIR = MappingProxyType(
    {
        "VCCO_503": frozenset({1}),
        "VCC_PMC": frozenset({1}),
        "VCC_PSLP": frozenset({1}),
        "VCCAUX_SMON": frozenset({1}),
        "GTY_AVCC_RS": frozenset({2}),
        "GTM_AVCC_RN": frozenset({2}),
        "VCCINT_GT_R": frozenset({1, 2}),
    }
)
"""The capacitors below 10 uF on rails Part 2 does not pour that its field
placement finds no free pair of ball vias for, by rail name and place in
the rail's set: the 4.7 uF of VCCO_503, VCC_PMC and VCC_PSLP;
VCCAUX_SMON's 100 nF; the 470 nF of GTY_AVCC_RS and GTM_AVCC_RN; and
VCCINT_GT_R's 4.7 uF and 470 nF. Each belongs to a rail of one to three
balls whose few rail and ground pairs are taken. Whether a capacitor finds
a pair is known only once Part 2 places the field, so the result is worked
out once and written here as data; the repository's Part 2 tests place
every set whole and check it."""

FPGA_INVERT = True
"""The ``invert`` flag of every FPGA pair point and insertion. Every memory
pair point and insertion takes the opposite, so the two pair points of a
pair join front to front (module docstring, "Pair polarity")."""


def pad_centres(component: Component) -> dict[Port, tuple[float, float]]:
    """Position of the centre of each port's pad on a placed ``component``,
    in the frame of the circuit that holds it, read in one pass over its
    pads (the first pad, for a port with several)."""
    if component.transform is None:
        raise ValueError(f"{component} is not placed")
    mappings = list(extract(component, PadMapping))
    centres: dict[Port, tuple[float, float]] = {}
    for trace, pad in visit(component, Pad):
        if pad.transform is None or trace.transform is None:
            raise ValueError(f"{pad} of {component} is not placed")
        for mapping in mappings:
            port = mapping.get(pad)
            if isinstance(port, Port) and port not in centres:
                placement = component.transform * trace.transform * pad.transform
                x, y = placement * (0.0, 0.0)
                centres[port] = (float(x), float(y))
    return centres


def via_in_pad(
    centre: tuple[float, float], ball: Port, kind: type[Via]
) -> tuple[Via, PortAttachment]:
    """A ``kind`` via at the centre of the ball's pad, attached to the ball.
    The caller stores both in the circuit that holds the ball's part."""
    via = kind().at(centre)
    return via, PortAttachment(ball, via)


def attached_via(attachments: list[PortAttachment], ball: Port) -> Via:
    """The via attached to ``ball`` among ``attachments``."""
    for attachment in attachments:
        if attachment.port is ball:
            assert isinstance(attachment.attachment, Via)
            return attachment.attachment
    raise KeyError(f"{ball} has no fanout via")


def tagged_pair_routes(
    p_via: Via, n_via: Via, insertion: PairInsertion, point: PairPoint, layer: int
) -> list[Route]:
    """The three segments of a pair's escape, each tagged
    :py:class:`~.ball_field.BallFieldPairTag`: its two vias' legs into the
    insertion and the coupled segment from the insertion to the pair
    point."""
    routes = [
        Route(p_via, insertion.uncoupled.p, layer),
        Route(n_via, insertion.uncoupled.n, layer),
        Route(insertion.coupled, point.back, layer),
    ]
    for route in routes:
        BallFieldPairTag().assign(route)
    return routes


def pair_escape(
    p_via: Via, n_via: Via, saved: PairEscape, layer: int, invert: bool
) -> tuple[PairInsertion, PairPoint, list[Route]]:
    """A pair's insertion and pair point where ``saved`` places them, both
    with ``invert``, and its three tagged segments. The pair point shares
    the insertion's flag, so the insertion's coupled end joins its back."""
    at = saved.insertion
    insertion = PairInsertion(layer=layer, invert=invert).at(
        (at.x, at.y), rotate=at.heading
    )
    at = saved.point
    point = PairPoint(layer=layer, invert=invert).at((at.x, at.y), rotate=at.heading)
    return insertion, point, tagged_pair_routes(p_via, n_via, insertion, point, layer)


class FanoutFpga(JS4Fpga):
    """The FPGA's circuit with a via in every ball's pad but the NC balls',
    the pair escapes out of its ball field, and none of the capacitors Part
    2 would have nowhere to put (:py:meth:`decoupling_layouts`)."""

    def __init__(self) -> None:
        super().__init__()
        self.fanout_vias: list[Via] = []
        self.fanout_attachments: list[PortAttachment] = []
        pads = pad_centres(self.fpga)
        for ball in self.fpga_balls():
            via, attachment = via_in_pad(pads[ball], ball, THROUGH_VIA)
            self.fanout_vias.append(via)
            self.fanout_attachments.append(attachment)

        self.escape_insertions: list[PairInsertion] = []
        self.escape_points: list[PairPoint] = []
        self.escape_routes: list[Route] = []
        for slot, p, n in self.escape_pairs():
            self.escape(p, n, FPGA_ESCAPES[slot])

    def decoupling_layouts(self) -> dict[str, RailLayout]:
        """Each FPGA set's layout, read before any capacitor is created: on
        a rail outside :py:data:`POURED_RAILS`, leave out every capacitor
        of 10 uF and up and those of :py:data:`NO_FIELD_PAIR`, since in
        Part 2's ring their rail via would join nothing (module docstring,
        "Decoupling"). Every other capacitor is created, each below 10 uF
        tied to its ball by a ShortTrace."""
        layouts: dict[str, RailLayout] = {}
        for name, kinds in fpga_sets(self).items():
            if name in POURED_RAILS:
                continue
            bulk = {
                i
                for i, kind in enumerate(kinds)
                if kind.capacitance >= BULK_CAPACITANCE
            }
            omit = frozenset(bulk) | NO_FIELD_PAIR.get(name, frozenset())
            if omit:
                layouts[name] = RailLayout(omit=omit)
        return layouts

    def fpga_pin(self, pos: Pos) -> Port:
        """The VP1002 port at a position of the LPDDR4 layout."""
        return self.fpga.xpio_triplet_pins()[0][pos.index].port

    def fpga_balls(self) -> list[Port]:
        """The FPGA's fanout balls: every ball but those the pinout names
        NC, whether a net reaches it yet or not, a design choice that keeps
        every pin available to a later part: a later part may assign an
        unused I/O ball. UG863 v1.12 ("Unused VCCO Banks and NC Pins"):
        "Pins that are labeled as "NC" in the package file can either be
        left unconnected or tied to ground." The kit leaves them
        unconnected, a design choice, so no later part needs them."""
        fpga = self.fpga
        skip = {id(p) for p in fpga.NC}
        return [p for p, _ in fpga.ball_assignments() if id(p) not in skip]

    def fanout_via(self, ball: Port) -> Via:
        """The fanout via in a ball's pad."""
        return attached_via(self.fanout_attachments, ball)

    def escape_pairs(self) -> list[tuple[int, Port, Port]]:
        """Each escaped pair's byte slot and its (P, N) FPGA balls: the DQS
        of channel B's two byte slots, in slot order."""
        return [
            (k, self.fpga_pin(slot.dqs_t), self.fpga_pin(slot.dqs_c))
            for k, slot in enumerate(LPDDR4_X32.slots)
            if slot.channel is Channel.B
        ]

    def escape(self, p: Port, n: Port, saved: PairEscape) -> None:
        """Escape one pair out of the FPGA's ball field: its two vias to a
        ``PairInsertion`` coupled to a ``PairPoint``, both where ``saved``
        places them, each segment on :py:data:`CHANNEL_B_LAYER` tagged
        :py:class:`~.ball_field.BallFieldPairTag`, all with
        :py:data:`FPGA_INVERT`."""
        insertion, point, routes = pair_escape(
            self.fanout_via(p), self.fanout_via(n), saved, CHANNEL_B_LAYER, FPGA_INVERT
        )
        self.escape_insertions.append(insertion)
        self.escape_points.append(point)
        self.fanout_attachments += [
            PortAttachment([p, n], insertion),
            PortAttachment([p, n], point),
        ]
        self.escape_routes += routes


class FanoutMemory(JS4Memory):
    """The memory's circuit with the memory at its origin, turned 180
    degrees, a via in the pad of every ball but NC and DNU, and channel B's
    two DQS pairs escaped out of its ball field."""

    def __init__(self) -> None:
        super().__init__()
        self.memory.at(0, 0, rotate=180)

        self.fanout_vias: list[Via] = []
        self.fanout_attachments: list[PortAttachment] = []
        pads = pad_centres(self.memory)
        for ball in self.memory_balls():
            via, attachment = via_in_pad(pads[ball], ball, THROUGH_VIA)
            self.fanout_vias.append(via)
            self.fanout_attachments.append(attachment)

        self.escape_insertions: list[PairInsertion] = []
        self.escape_points: list[PairPoint] = []
        self.escape_routes: list[Route] = []
        for lane, (p, n) in enumerate(self.escape_pairs()):
            self.escape(p, n, MEMORY_ESCAPES[lane])

    def fanout_via(self, ball: Port) -> Via:
        """The fanout via in a ball's pad."""
        return attached_via(self.fanout_attachments, ball)

    def escape_pairs(self) -> list[tuple[Port, Port]]:
        """The memory's (P, N) balls of each escaped pair: DQS_t and DQS_c
        of channel B's byte lanes 0 and 1 (``ch[1]``)."""
        return [(lane.dqs.p, lane.dqs.n) for lane in self.memory.lpddr4.ch[1].d]

    def escape(self, p: Port, n: Port, saved: PairEscape) -> None:
        """Escape one pair out of the memory's ball field toward the FPGA:
        its two vias to a ``PairInsertion`` coupled to a ``PairPoint``, both
        where ``saved`` places them, each segment on
        :py:data:`CHANNEL_B_LAYER` tagged
        :py:class:`~.ball_field.BallFieldPairTag`, all with the opposite of
        :py:data:`FPGA_INVERT`."""
        insertion, point, routes = pair_escape(
            self.fanout_via(p),
            self.fanout_via(n),
            saved,
            CHANNEL_B_LAYER,
            not FPGA_INVERT,
        )
        self.escape_insertions.append(insertion)
        self.escape_points.append(point)
        self.fanout_attachments += [
            PortAttachment([p, n], insertion),
            PortAttachment([p, n], point),
        ]
        self.escape_routes += routes

    def memory_balls(self) -> list[Port]:
        """The memory's fanout balls, every ball but NC and DNU: the byte
        lanes of both channels, the command, address and clock, RESET_n, ZQ,
        ODT_CA, VDD1, VDD2, VDDQ and VSS."""
        memory = self.memory
        balls = [
            p for ch in memory.lpddr4.ch for lane in ch.d for p in lane_balls(lane)
        ]
        for ch in memory.lpddr4.ch:
            balls += [ch.ck.p, ch.ck.n, *ch.cke, *ch.cs, *ch.ca]
        balls += [memory.RESET_n, memory.ZQ0, memory.ZQ1]
        balls += [memory.ODT_CA_A, memory.ODT_CA_B]
        balls += [*memory.VDD1, *memory.VDD2, *memory.VDDQ, *memory.VSS]
        return balls


class JS4FanoutCircuit(JS4BaseCircuit):
    """:py:class:`~.base.JS4BaseCircuit` with Part 1's placement, fanout,
    ground pours and channel B's two DQS escapes."""

    def __init__(self) -> None:
        super().__init__()
        # The memory's placement, a design choice: to balance length across
        # the data lanes (MEMORY_AT).
        self.memory.at(MEMORY_AT)

        # A GND pour over the board outline on every ground layer. The ground
        # vias, which reach every layer, hold each one.
        outline = rectangle(BOARD_WIDTH, BOARD_HEIGHT, radius=BOARD_CORNER_RADIUS)
        self.ground_pours = [Pour(outline, layer=layer) for layer in GROUND_LAYERS]
        for pour in self.ground_pours:
            self.gnd_net += pour

        # The ball-field structure the escapes' tagged segments take.
        self.ball_field_rules = ball_field_rules(
            Reference18Substrate.DRS_85_FIELD, self.gnd_net
        )

    def new_fpga(self) -> JS4Fpga:
        return FanoutFpga()

    def new_memory(self) -> JS4Memory:
        return FanoutMemory()


def lane_balls(lane: LPDDR4Lane) -> list[Port]:
    """Every ball of a memory byte lane: the eight DQ, DQS_t, DQS_c and DMI."""
    return [*lane.dq, lane.dqs.p, lane.dqs.n, lane.dmi]


class JS4FanoutDesign(Design):
    """Part 1's reference: the base design with the memory placed, the
    fanout, the ground pours and the pair escapes. No SI constraints."""

    board = Reference18Board()
    substrate = Reference18Substrate()
    circuit = JS4FanoutCircuit()

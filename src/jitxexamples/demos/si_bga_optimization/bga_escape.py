"""BGA escape-port design.

Top-level circuit + design for an HDI BGA fanout experiment. Each
signal row-pair on the BGA gets a per-lane ``EscapeLane`` child Circuit
that owns the lane-local geometric features: signal-via antipad
``KeepOut`` list, deskew ``OverlappableCopper`` pair, and the deskew-
antipad ``KeepOut``. Every cross-lane JITX object — diff-pair ``Net``,
signal-via and pair/insertion-control ``PortAttachment``s,
``PairPoint`` / ``PairInsertion`` / ``Route`` triple, the deskew-copper
``VirtualConnection``s, and the upper-reference and deskew fence
``Pour``s — is constructed and owned
by ``BGALink``, since JITX requires each ``Net`` / ``PortAttachment`` /
``Pour`` to live on the common ancestor of every ``Port`` it touches
and the BGA Component sits at ``BGALink`` level. The diff pairs carry
the 85 ohm differential routing structure via a tag rule
(``StriplineDiffPairTag``) rather than an explicit ``>>`` topology, so
no far-end terminal component is needed.

The design-specific code is split by concern across this package:
design-rule tags and the antipad fence-via ``design_constraint`` rules
in ``constraints``, the substrate specialization (``BGAEscapeSubstrate``
with its routing structures and launch profiles, anchoring those rules)
in ``substrate``, and per-lane geometry constants and helpers —
including the HFSS-instrumented-lane override — in ``si_geometry``.
This file owns the per-lane ``EscapeLane`` and top-level ``BGALink``
circuit assembly plus the buildable ``bga_optimization_design`` entry
point.
"""

import jitx
from jitx import KeepOut, LayerSet, Pour
from jitx.circuit import Circuit, Route
from jitx.controlpoint import PairInsertion, PairPoint
from jitx.constraints import design_constraint
from jitx.net import Net, PortAttachment
from jitx.sample import SampleDesign
from jitx.shapes.composites import rectangle
from jitx.shapes.shapely import ShapelyGeometry
from jitx.via import Via
from jitx.virtual import VirtualConnection
from . import generic_bga as bga
from .constraints import StriplineDiffPairTag
from .deskew import deskew_pair
from .generic_bga import GenericHexGridBGA
from .si_geometry import (
    DESKEW_EXIT_ABOVE_LOWER_BALL,
    DESKEW_PAIR_SPACING,
    DESKEW_TRACE_WIDTH,
    DESKEW_VIA_PAD_TO_TRACE_GAP,
    INSTRUMENTED_SIGNAL2_L1_D_OUTWARD_RADIUS,
    INSTRUMENTED_SIGNAL2_SPLIT_ANTIPAD_RADIUS,
    SIGNAL_VIA_FENCE_RADIUS,
    SIGNAL_VIA_KEEPOUT_RADIUS,
    SIGNAL_VIA_PAD_DIAMETER,
    deskew_antipad_keepout_and_pour_shape,
    deskew_knobs,
    gnd_pad_via_sites,
    instrumented_l1_d_keepouts,
    is_instrumented_lane,
    make_si_cutout,
    signal_via_pair_antipad_keepouts,
    signal_via_pair_capsule,
)
from .substrate import BGAEscapeSubstrate, PerSignalLayerSpec


# -----------------------------------------------------------------------------
# Per-lane circuit + top-level assembly.
# -----------------------------------------------------------------------------


class EscapeLane(Circuit):
    """One BGA escape lane.

    Owns the lane-local geometric features: signal-via antipad
    ``KeepOut`` list, deskew ``OverlappableCopper`` pair, and the
    deskew-antipad ``KeepOut``. These have no port references and live
    cleanly inside this child Circuit.

    Every other JITX object that touches a lane — the diff-pair ``Net``,
    the signal-via and pair/insertion-control ``PortAttachment``s, the
    ``PairPoint`` / ``PairInsertion`` / ``Route`` triple, and the
    upper-reference / deskew fence ``Pour``s — is constructed and
    owned by ``BGALink``. JITX's structural rules require these objects
    to live on the common ancestor of every ``Port`` they touch
    (``BGALink`` for objects that reference the BGA's diff-pair Ports;
    the Net's owner for Pours), and control / route elements turn out
    not to be valid inside a non-net-owning child Circuit either.

    Each lane exposes the data ``BGALink`` needs (``p_pad``, ``n_pad``,
    ``spec``, ``signal_via_fence_shape``, ``deskew_fence_pour_shape``,
    ``deskew_left_exit``, ``deskew_right_exit``) — plain Python values
    that JITX does not walk as structural children.

    Built from the lane's signal-via pad coordinates, the per-signal-
    layer launch ``spec``, and the deskew-arc parameters (caller
    derives these from ``deskew_knobs(lane_index)``). The instrumented-
    lane override (mirrored L1 D-cuts plus enlarged L2/L3 circular
    cuts) is enabled by ``is_instrumented``.
    """

    def __init__(
        self,
        *,
        p_pad: tuple[float, float],
        n_pad: tuple[float, float],
        spec: PerSignalLayerSpec,
        theta_exit_deg: float,
        right_r_wrap: float,
        is_instrumented: bool = False,
    ):
        # Expose the launch parameters for ``BGALink`` to read when
        # building the Nets, PortAttachments, control points, Routes,
        # and Pours that must live on the common ancestor. These are
        # non-JITX data attributes (ints, tuples of floats, references
        # to module-level types).
        self.p_pad = p_pad
        self.n_pad = n_pad
        self.spec = spec

        # Signal-via antipad: capsule keepout at the baseline radius,
        # plus per-via circular cuts on the upper reference planes when
        # ``split_antipad_layers`` is set (default for Signal2+). The
        # instrumented lane on Signal2 swaps the L1 row for mirrored
        # D-cuts (decoupling L1 from the L2/L3 circular pair) and
        # enlarges the L2/L3 circles to the physics-sized radius.
        keepout_shape = signal_via_pair_capsule(p_pad, n_pad, SIGNAL_VIA_KEEPOUT_RADIUS)
        split_keepout_radius = SIGNAL_VIA_KEEPOUT_RADIUS
        split_antipad_layers = spec.split_antipad_layers
        fence_radius = SIGNAL_VIA_FENCE_RADIUS
        deskew_antipad_radius = fence_radius
        extra_keepouts: list[KeepOut] = []
        if is_instrumented:
            split_keepout_radius = INSTRUMENTED_SIGNAL2_SPLIT_ANTIPAD_RADIUS
            split_antipad_layers = LayerSet(1, 2)
            fence_radius = INSTRUMENTED_SIGNAL2_L1_D_OUTWARD_RADIUS
            # Decouple the L4 deskew antipad from the enlarged reference-
            # plane fence perimeter so the L4 cut stays sized to actual
            # deskew copper + buffer.
            deskew_antipad_radius = SIGNAL_VIA_KEEPOUT_RADIUS
            extra_keepouts = instrumented_l1_d_keepouts(p_pad, n_pad)

        fence_shape = signal_via_pair_capsule(p_pad, n_pad, fence_radius)
        deskew_antipad_shape = (
            fence_shape
            if deskew_antipad_radius == fence_radius
            else signal_via_pair_capsule(p_pad, n_pad, deskew_antipad_radius)
        )

        antipad_keepouts = signal_via_pair_antipad_keepouts(
            keepout_shape,
            spec,
            p_pad=p_pad,
            n_pad=n_pad,
            split_keepout_radius=split_keepout_radius,
            split_antipad_layers=split_antipad_layers,
        )
        antipad_keepouts.extend(extra_keepouts)
        self.antipad_keepouts = antipad_keepouts

        # Exposed for ``BGALink`` to use when constructing the upper-
        # reference fence Pour. ``None`` for Signal1 (no via spans above
        # its launch layer); see ``PerSignalLayerSpec``.
        self.signal_via_fence_shape: ShapelyGeometry | None = (
            fence_shape if spec.upper_ref_fence_pour_layer is not None else None
        )

        # Deskew geometry. ``deskew_pair`` returns a transient bundle of
        # copper + exit coordinates; destructure its fields into named
        # members so JITX's structural walk discovers the copper directly.
        deskew = deskew_pair(
            right_pad=p_pad,
            left_pad=n_pad,
            theta_exit_deg=theta_exit_deg,
            right_r_wrap=right_r_wrap,
            exit_above_lower=DESKEW_EXIT_ABOVE_LOWER_BALL,
            exit_ball_clearance=DESKEW_VIA_PAD_TO_TRACE_GAP
            - SIGNAL_VIA_PAD_DIAMETER / 2,
            layer=spec.deskew_layer,
            trace_w=DESKEW_TRACE_WIDTH,
            pair_spacing=DESKEW_PAIR_SPACING,
        )
        self.right_deskew_copper = deskew.right_copper
        self.left_deskew_copper = deskew.left_copper

        self.deskew_antipad_keepout, self.deskew_fence_pour_shape = (
            deskew_antipad_keepout_and_pour_shape(
                deskew.right_copper,
                deskew.left_copper,
                deskew_antipad_shape,
                fence_shape,
                spec,
            )
        )

        # Expose the deskew exit coordinates so ``BGALink`` can place
        # the ``PairPoint`` (at the exit midpoint) and ``PairInsertion``
        # (at the board edge below) on the deskew layer.
        self.deskew_right_exit = deskew.right_exit
        self.deskew_left_exit = deskew.left_exit


# Pour ranks resolve which pour renders when two overlap on the same
# layer; higher wins. Independent from constraint ``priority`` (which
# resolves fence-via dedup at coincident XY).
_ANTIPAD_FENCE_POUR_RANK = 4
_DESKEW_ANTIPAD_FENCE_POUR_RANK = _ANTIPAD_FENCE_POUR_RANK + 10


class BGALink(Circuit):
    """BGA row-pair escape wiring.

    Each signal row-pair gets a per-lane ``EscapeLane`` child Circuit
    that owns its lane-local objects (antipad keepouts, deskew copper +
    antipad keepout, PairPoint, PairInsertion, Route).

    JITX's structural rule — every ``Net`` / ``PortAttachment`` / ``Pour``
    must live on an ancestor of every ``Port`` it references, and a
    ``Pour`` lives with the ``Net`` it belongs to — forces the
    cross-lane objects (diff-pair Nets, signal-via PortAttachments,
    pair/insertion-control PortAttachments, the upper-reference /
    deskew fence Pours, and the board-wide ``GND`` Net) onto this
    Circuit, the common ancestor of the BGA Component and every lane.

    A tag rule applies the 85 ohm differential routing structure to
    every ``StriplineDiffPairTag`` net, so no ``>>`` topology or far-
    end terminal component is needed.
    """

    def __init__(self):
        substrate = jitx.current.substrate
        assert isinstance(substrate, BGAEscapeSubstrate)

        self.bga = GenericHexGridBGA().at(0, 0)

        # Per-lane structural children + the cross-lane JITX objects
        # whose structural ancestry requires them to live here.
        # ``EscapeLane`` children own the lane-local geometry and
        # control points; this loop also emits the diff-pair Nets, signal
        # Vias, PortAttachments, deskew-copper VirtualConnections, and
        # fence Pours — each accumulated into
        # a named list member of this Circuit (the JITX objects
        # themselves, not records of them).
        self.lanes: list[EscapeLane] = []
        signal_nets: list[Net] = []
        signal_vias: list[Via] = []
        signal_via_attachments: list[PortAttachment] = []
        pair_points: list[PairPoint] = []
        pair_insertions: list[PairInsertion] = []
        control_attachments: list[PortAttachment] = []
        virtual_connections: list[VirtualConnection] = []
        routes: list[Route] = []
        signal_via_fence_pours: list[Pour] = []
        deskew_fence_pours: list[Pour] = []
        for pair_index, (top_row, bottom_row) in enumerate(bga.SIGNAL_ROW_PAIRS):
            signal_layer = bga.signal_layer_for_pair(pair_index)
            spec = substrate.spec_for_signal_layer(signal_layer)
            via_cls = substrate.signal_via[signal_layer]
            for lane_index, col in enumerate(bga.signal_cols_for_pair(pair_index)):
                tx_pair = self.bga.lanes[pair_index][lane_index]
                p_pad = bga.ball_center(bottom_row, col)
                n_pad = bga.ball_center(top_row, col)

                theta_exit_deg, right_r_wrap = deskew_knobs(lane_index)
                lane = EscapeLane(
                    p_pad=p_pad,
                    n_pad=n_pad,
                    spec=spec,
                    theta_exit_deg=theta_exit_deg,
                    right_r_wrap=right_r_wrap,
                    is_instrumented=is_instrumented_lane(pair_index, lane_index),
                )
                self.lanes.append(lane)

                # Diff-pair Net + stripline tag.
                net = Net([tx_pair])
                StriplineDiffPairTag().assign(net)
                signal_nets.append(net)

                # Signal-via attachments at the two BGA pad coordinates.
                # The Vias also accumulate into ``signal_vias``: reaching
                # an object only through a Net/PortAttachment, without a
                # circuit assignment, is deprecated.
                p_via = via_cls().at(*p_pad)
                n_via = via_cls().at(*n_pad)
                signal_vias.append(p_via)
                signal_vias.append(n_via)
                signal_via_attachments.append(PortAttachment(tx_pair.p, p_via))
                signal_via_attachments.append(PortAttachment(tx_pair.n, n_via))

                # Pair-control (at the deskew exit midpoint) launches the
                # coupled stripline trunk; insertion-control sits at the
                # board-edge wave-port launch. Both anchor to the BGA pair
                # itself, so the Route walks coupled diff-pair to
                # uncoupled board-edge launch on the deskew layer. Both
                # control points are non-inverted, so the insertion's
                # coupled end pairs with the pair point's back side.
                pair_point = (
                    0.5 * (lane.deskew_left_exit[0] + lane.deskew_right_exit[0]),
                    0.5 * (lane.deskew_left_exit[1] + lane.deskew_right_exit[1]),
                )
                # Board-edge wave-port launch sits just below the SI cutout
                # y-min, at the boundary.
                insertion_point = (pair_point[0], -15)
                pair_point = PairPoint(layer=spec.deskew_layer).at(
                    pair_point, rotate=90
                )
                pair_insertion = PairInsertion(layer=spec.deskew_layer).at(
                    insertion_point, rotate=90
                )
                pair_points.append(pair_point)
                pair_insertions.append(pair_insertion)
                control_attachments.append(
                    PortAttachment([tx_pair.n, tx_pair.p], pair_point)
                )
                control_attachments.append(
                    PortAttachment([tx_pair.n, tx_pair.p], pair_insertion)
                )
                routes.append(
                    Route(
                        pair_point.back,
                        pair_insertion.coupled,
                        spec.deskew_layer,
                    )
                )

                # The deskew arcs are OverlappableCopper the router cannot
                # see; declare the connection each one makes — signal via to
                # front-side pair-point leg — so no flywires are emitted.
                # The [n, p] attachment order above puts tx_pair.n on the
                # point's p side, so the left (n) copper lands on front.p
                # and the right (p) copper on front.n.
                virtual_connections.append(
                    VirtualConnection(
                        n_via,
                        pair_point.front.p,
                        source_layer=spec.deskew_layer,
                        destination_layer=spec.deskew_layer,
                    )
                )
                virtual_connections.append(
                    VirtualConnection(
                        p_via,
                        pair_point.front.n,
                        source_layer=spec.deskew_layer,
                        destination_layer=spec.deskew_layer,
                    )
                )

                if (
                    lane.signal_via_fence_shape is not None
                    and spec.upper_ref_fence_pour_layer is not None
                    and spec.upper_ref_fence_tag is not None
                ):
                    p = Pour(
                        lane.signal_via_fence_shape,
                        layer=spec.upper_ref_fence_pour_layer,
                        rank=_ANTIPAD_FENCE_POUR_RANK,
                        isolate=0.0,
                    )
                    spec.upper_ref_fence_tag.assign(p)
                    signal_via_fence_pours.append(p)

                dp = Pour(
                    lane.deskew_fence_pour_shape,
                    layer=spec.deskew_antipad_fence_pour_layer,
                    rank=_DESKEW_ANTIPAD_FENCE_POUR_RANK,
                    isolate=0.0,
                )
                spec.deskew_antipad_fence_tag.assign(dp)
                deskew_fence_pours.append(dp)
        self.signal_nets = signal_nets
        self.signal_vias = signal_vias
        self.signal_via_attachments = signal_via_attachments
        self.pair_points = pair_points
        self.pair_insertions = pair_insertions
        self.control_attachments = control_attachments
        self.virtual_connections = virtual_connections
        self.routes = routes
        self.signal_via_fence_pours = signal_via_fence_pours
        self.deskew_fence_pours = deskew_fence_pours

        # GND pour on every conductor layer. ``rank=1`` (instead of 0)
        # makes JITX render the pour as a real fill rather than treating
        # it as a background that gets culled when no higher-rank
        # feature overlaps.
        n_conductors = len(substrate.stackup.conductors)
        gnd_pour_shape = rectangle(48, 48, radius=4)
        self.gnd_pours = [
            Pour(gnd_pour_shape, layer=layer, rank=1, isolate=0.0)
            for layer in range(n_conductors)
        ]

        # GND-via stitching around every BGA GND ball. The site-planning
        # helper returns pure data; this Circuit constructs the actual
        # Via instances and owns them as a named structural member.
        self.gnd_stitching_vias = [
            substrate.gnd_via[signal_layer]().at(*bga.ball_center(row, col))
            for row, col, signal_layer in gnd_pad_via_sites()
        ]

        self.GND = Net(
            [
                *self.bga.GND,
                *self.gnd_pours,
                *self.gnd_stitching_vias,
                *signal_via_fence_pours,
                *deskew_fence_pours,
            ],
            name="GND",
        )

        # Tag rule: apply the 85 ohm differential routing structure to
        # every StriplineDiffPairTag net, referenced to GND on each
        # stripline reference layer.
        self.routing_rule = design_constraint(StriplineDiffPairTag()).routing_structure(
            BGAEscapeSubstrate.DRS_DiffPair_85, ref_net=self.GND
        )

        self.sicut = make_si_cutout()


class bga_optimization_design(SampleDesign):
    substrate = BGAEscapeSubstrate()
    circuit = BGALink()

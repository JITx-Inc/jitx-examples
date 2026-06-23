"""BGA escape-port design.

Top-level circuit + design for an HDI BGA fanout experiment. Each
signal row-pair on the BGA gets a per-lane ``EscapeLane`` child Circuit
that owns the lane-local geometric features: signal-via antipad
``KeepOut`` list, deskew ``OverlappableCopper`` pair, and the deskew-
antipad ``KeepOut``. Every cross-lane JITX object — diff-pair ``Net``,
signal-via and pair/insertion-control ``PortAttachment``s,
``PairPoint`` / ``PairInsertion`` / ``Route`` triple, and the
upper-reference and deskew fence ``Pour``s — is constructed and owned
by ``BGALink``, since JITX requires each ``Net`` / ``PortAttachment`` /
``Pour`` to live on the common ancestor of every ``Port`` it touches
and the BGA Component sits at ``BGALink`` level. The diff pairs carry
the 85 ohm differential routing structure via a tag rule
(``StriplineDiffPairTag``) rather than an explicit ``>>`` topology, so
no far-end terminal component is needed.

Design-specific tags, geometry constants, and routing structures live
in this file; the substrate file is kept truly generic and gets
specialized here via ``BGAEscapeSubstrate(Generic_Substrate)``.
"""

import math
from dataclasses import dataclass

import shapely
import jitx
from jitx import KeepOut, LayerSet, Pour
from jitx.circuit import Circuit, Route
from jitx.controlpoint import PairInsertion, PairPoint
from jitx.constraints import Tag, ViaFencePattern, design_constraint
from jitx.feature import Custom
from jitx.net import Net, PortAttachment
from jitx.sample import SampleDesign
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Text
from jitx.shapes.shapely import ShapelyGeometry
from jitx.si import (
    DifferentialRoutingStructure,
    RoutingStructure,
    symmetric_routing_layers,
)
from jitx.units import ohm
from jitxexamples.substrates.generic_20layer import (
    VEL_STRIPLINE,
    Generic_Substrate,
)
from . import generic_bga as bga
from .deskew import deskew_pair, is_overlappable_copper
from .generic_bga import GenericHexGridBGA


# -----------------------------------------------------------------------------
# Design-rule tags (BGA-escape specific).
# -----------------------------------------------------------------------------


class StriplineDiffPairTag(Tag):
    """85 ohm differential stripline trunk net.

    Carries the differential routing structure via a tag rule (see
    ``BGALink``), so the diff pairs get their impedance-controlled
    cross-section without an explicit ``>>`` topology or a far-end
    terminal.
    """


# Per-layer antipad GND-pour fences. These are *mutually exclusive* —
# each cavity is closed by exactly one fence via class — so each is its
# own top-level Tag. (Tag inheritance would only help an additive
# parent-rule-plus-child-override pattern; here a shared base rule would
# double-fence every pour, and a parent-only base tag isn't registered in
# the backend tag table. See PR #4 discussion.)


class AntipadFenceTag(Tag):
    """Signal-via antipad GND pour on L7 (Ground4), fenced by uGnd_L1_L7.

    Upper-reference-plane antipad fence around the BGA wave-port launch
    of any Signal4-deskew row pair.
    """


class Ground3AntipadFenceTag(Tag):
    """Signal-via antipad GND pour on L5 (Ground3), fenced by uGnd_L1_L5."""


class Ground2AntipadFenceTag(Tag):
    """Signal-via antipad GND pour on L3 (Ground2), fenced by uGnd_L1_L3."""


class DeskewAntipadFenceTag(Tag):
    """Deskew antipad GND pour on L9 (Ground5), fenced by uFence_L7_L9
    (the Signal4 stripline-reference fence via)."""


class Ground4DeskewAntipadFenceTag(Tag):
    """Deskew antipad GND pour on L7 (Ground4), fenced by uFence_L5_L7."""


class Ground3DeskewAntipadFenceTag(Tag):
    """Deskew antipad GND pour on L5 (Ground3), fenced by uFence_L3_L5."""


class Ground2DeskewAntipadFenceTag(Tag):
    """Deskew antipad GND pour on L3 (Ground2), fenced by uFence_L1_L3."""


# -----------------------------------------------------------------------------
# BGA geometry constants.
# -----------------------------------------------------------------------------

BGA_MAIN_TRUNK_DP_TO_GND = 0.25
BGA_ANTIPAD_FENCE_PITCH = 0.35
BGA_ANTIPAD_FENCE_OFFSET = 0.15
BGA_ANTIPAD_FENCE_MIN_EDGE_CLEARANCE = -0.02

# Diff-pair stripline geometry for every 85 ohm signal layer (L2/L4/L6/L8).
DIFFPAIR_TRACE_WIDTH = 0.115
DIFFPAIR_PAIR_SPACING = 0.118

# Route-following pour keepout corridor width on the signal layer.
# ``geometry(KeepOut, width, ...)`` is applied per-trace centered on
# each leg's centerline; the two per-leg corridors union together. So
# the per-leg width is just trace_width + 2 x clearance -- adding the
# pair span here double-counts pair_spacing + trace_width on each side.
_DP_TO_GND_POUR_CORRIDOR = DIFFPAIR_TRACE_WIDTH + 2 * BGA_MAIN_TRUNK_DP_TO_GND

# Deskew-arc cross-section. Decoupled from ``DIFFPAIR_*``: the deskew
# arc routes its two legs as largely-uncoupled single-ended traces, so
# each leg's local Z is set by trace width vs. reference-plane spacing,
# not by the inner edge-to-edge gap. Widening the legs from 0.115 ->
# 0.150 mm pulls Z_se down toward 46 ohm -> Z_diff toward 85 ohm; inner
# gap preserved at the original 0.118 mm.
DESKEW_TRACE_WIDTH = 0.138
DESKEW_PAIR_SPACING = 0.118


def _drs_layer_85(
    signal_layer: int, upper_ref: int, lower_ref: int, fence_via_cls
) -> "DifferentialRoutingStructure.Layer":
    """85 ohm coplanar differential stripline layer entry.

    Parameterized by signal layer index, the two reference plane layer
    indices, and the fence-via class that ties them. References on three
    layers make this a coplanar stripline: the upper and lower ground
    planes (stripline) plus a coplanar GND reference on the signal layer
    itself. The DP-to-GND-pour (0.25 mm) clearance is the route-following
    KeepOut corridor on the signal layer (so the coplanar GND keeps its
    distance), expressed here rather than via a tag-keyed rule.
    """
    return (
        DifferentialRoutingStructure.Layer(
            trace_width=DIFFPAIR_TRACE_WIDTH,
            pair_spacing=DIFFPAIR_PAIR_SPACING,
            clearance=0.05,  # fab floor
            velocity=VEL_STRIPLINE,
            insertion_loss=0.018,
        )
        .reference(upper_ref, 1.0)
        .reference(lower_ref, 1.0)
        .reference(signal_layer, 1.0)  # coplanar GND on the signal layer
        .fence(fence_via_cls, _FENCE_PATTERN, reference_layer=lower_ref)
        .geometry(
            KeepOut, _DP_TO_GND_POUR_CORRIDOR, layers=LayerSet(signal_layer), pour=True
        )
    )


def _rs_uncoupled_layer(signal_layer: int) -> "RoutingStructure.Layer":
    """Single-ended uncoupled-region layer entry for the deskew/escape.

    References match the coplanar stripline: upper plane (signal-1),
    lower plane (signal+1), and the coplanar GND on the signal layer.
    ``symmetric_routing_layers`` mirrors these for the bottom half.
    """
    return (
        RoutingStructure.Layer(
            trace_width=0.10,
            clearance=0.135,
            velocity=VEL_STRIPLINE,
            insertion_loss=0.018,
            neck_down=RoutingStructure.NeckDown(trace_width=0.10, clearance=0.135),
        )
        .reference(signal_layer - 1, 1.0)
        .reference(signal_layer + 1, 1.0)
        .reference(signal_layer, 1.0)
    )


def _antipad_fence_pattern(via_diameter: float) -> ViaFencePattern:
    edge_clearance = BGA_ANTIPAD_FENCE_OFFSET - (via_diameter / 2)
    if edge_clearance < BGA_ANTIPAD_FENCE_MIN_EDGE_CLEARANCE:
        raise ValueError(
            "BGA_ANTIPAD_FENCE_OFFSET places the fence via pad too far into "
            "the antipad region; minimum allowed edge clearance is "
            f"{BGA_ANTIPAD_FENCE_MIN_EDGE_CLEARANCE} mm; "
            f"got {edge_clearance:.3f} mm."
        )
    return ViaFencePattern(
        pitch=BGA_ANTIPAD_FENCE_PITCH,
        offset=BGA_ANTIPAD_FENCE_OFFSET,
        initial_offset=BGA_ANTIPAD_FENCE_OFFSET,
        num_rows=1,
        input_shape_only=True,
    )


# Diff-pair trunk fence: shares the antipad fence pitch; offset 0.43 mm =
# trace-half 0.051 + DP-to-GND 0.25 + via-pad-radius 0.125.
_FENCE_PATTERN = ViaFencePattern(
    pitch=BGA_ANTIPAD_FENCE_PITCH,
    offset=0.43,
    num_rows=1,
)


# -----------------------------------------------------------------------------
# Per-signal-layer launch profile.
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class PerSignalLayerSpec:
    """Layer-dependent geometry knobs for one signal-layer launch.

    The deskew layer index ``d`` is ``2 * signal_layer - 1`` (Signal1 ->
    1, Signal2 -> 3, Signal3 -> 5, Signal4 -> 7). Antipad keepouts span
    layers in ``antipad_layers``; if ``split_antipad_layers`` is set,
    the keepout on those layers is split into per-via circular cuts
    instead of a single capsule covering both vias. The signal-via
    antipad fence pour sits on the upper reference plane (idx d-1); the
    deskew antipad fence pour sits on the lower reference plane (idx d+1).

    Signal1 (d=1) has no upper-reference fence pour (only L1 sits above);
    those fields are ``None`` for that spec.
    """

    signal_layer: int
    deskew_layer: int
    antipad_layers: LayerSet
    upper_ref_fence_pour_layer: int | None
    upper_ref_fence_tag: type | None
    deskew_antipad_layers: LayerSet
    deskew_antipad_fence_pour_layer: int
    deskew_antipad_fence_tag: type
    split_antipad_layers: LayerSet | None = None


# -----------------------------------------------------------------------------
# Substrate specialization: BGA-escape design-specific routing structure,
# design_constraint rules, and per-signal-layer launch profiles.
# -----------------------------------------------------------------------------


class BGAEscapeSubstrate(Generic_Substrate):
    """Generic 20-layer substrate specialized for the BGA escape design.

    Adds the 85 ohm differential stripline routing structure (one entry
    per signal layer plus its symmetric mirror), the per-signal-layer
    launch profile table (queried by each ``EscapeLane``), and the
    design-constraint rules that drive antipad / fence-via generation
    around the BGA breakout cavity.
    """

    # 85 ohm differential stripline: one entry per signal layer plus
    # its symmetric mirror. Top + bottom halves are listed explicitly
    # because ``symmetric_routing_layers`` can't auto-mirror the fence
    # uVia's layer endpoints.
    DRS_DiffPair_85 = DifferentialRoutingStructure(
        name="85 ohm Differential Stripline",
        impedance=85 * ohm,
        layers={
            # Top half (Signal1..Signal4)
            1: _drs_layer_85(1, 0, 2, Generic_Substrate.uFence_L1_L3),  # L2
            3: _drs_layer_85(3, 2, 4, Generic_Substrate.uFence_L3_L5),  # L4
            5: _drs_layer_85(5, 4, 6, Generic_Substrate.uFence_L5_L7),  # L6
            7: _drs_layer_85(7, 6, 8, Generic_Substrate.uFence_L7_L9),  # L8
            # Bottom-half mirrors
            -2: _drs_layer_85(-2, -1, -3, Generic_Substrate.uFence_L18_L20),
            -4: _drs_layer_85(-4, -3, -5, Generic_Substrate.uFence_L16_L18),
            -6: _drs_layer_85(-6, -5, -7, Generic_Substrate.uFence_L14_L16),
            -8: _drs_layer_85(-8, -7, -9, Generic_Substrate.uFence_L12_L14),
        },
        uncoupled_region=RoutingStructure(
            name="85 ohm Uncoupled (~42 ohm SE)",
            impedance=42 * ohm,
            # Fresh per-layer instance (with references) so the four signal
            # layers don't share one Layer object under JITX's structural
            # identity; ``symmetric_routing_layers`` mirrors the bottom half.
            layers=symmetric_routing_layers(
                {i: _rs_uncoupled_layer(i) for i in (1, 3, 5, 7)}
            ),
        ),
    )

    # Fence pattern around the signal-via antipad cavity. Sized off the
    # uGnd_L1_L7 via diameter so the fence-via pad sits just outside the
    # antipad opening.
    _ANTIPAD_FENCE_PATTERN = _antipad_fence_pattern(
        float(Generic_Substrate.uGnd_L1_L7.diameter) + 0.075
    )

    # Constraint ``priority`` breaks ties when generated fence vias from
    # competing rules want to land at the same X/Y; higher wins. The
    # antipad fence and deskew fence intentionally use DIFFERENT via
    # classes: the antipad fence closes only the upper cavity
    # (uGnd_L1_L<upper-ref>); the deskew fence closes only the lower
    # cavity (uFence_L<upper-ref>_L<lower-ref>). Unifying them to
    # uGnd_L1_L<lower-ref> catastrophically regressed Scd21 (gen7_nyquist
    # -32.62 -> -24.10 dB) by routing longer fence vias through the
    # signal layer adjacent to the launch.
    signal_via_antipad_fence = design_constraint(
        AntipadFenceTag(), priority=20
    ).fence_via(Generic_Substrate.uGnd_L1_L7, _ANTIPAD_FENCE_PATTERN)

    signal_via_antipad_fence_g3 = design_constraint(
        Ground3AntipadFenceTag(), priority=20
    ).fence_via(Generic_Substrate.uGnd_L1_L5, _ANTIPAD_FENCE_PATTERN)

    signal_via_antipad_fence_g2 = design_constraint(
        Ground2AntipadFenceTag(), priority=9
    ).fence_via(Generic_Substrate.uGnd_L1_L3, _ANTIPAD_FENCE_PATTERN)

    deskew_antipad_fence = design_constraint(
        DeskewAntipadFenceTag(), priority=10
    ).fence_via(Generic_Substrate.uFence_L7_L9, _ANTIPAD_FENCE_PATTERN)

    deskew_antipad_fence_g4 = design_constraint(
        Ground4DeskewAntipadFenceTag(), priority=10
    ).fence_via(Generic_Substrate.uFence_L5_L7, _ANTIPAD_FENCE_PATTERN)

    deskew_antipad_fence_g3 = design_constraint(
        Ground3DeskewAntipadFenceTag(), priority=10
    ).fence_via(Generic_Substrate.uGnd_L1_L5, _ANTIPAD_FENCE_PATTERN)

    deskew_antipad_fence_g2 = design_constraint(
        Ground2DeskewAntipadFenceTag(), priority=10
    ).fence_via(Generic_Substrate.uFence_L1_L3, _ANTIPAD_FENCE_PATTERN)

    # Per-signal-layer launch profile table. Queried by each EscapeLane
    # via ``spec_for_signal_layer``. Keyed by signal layer index (1..4).
    _SIGNAL_LAYER_PROFILES: dict[int, PerSignalLayerSpec] = {
        1: PerSignalLayerSpec(
            signal_layer=1,
            deskew_layer=1,
            antipad_layers=LayerSet(0, 1),
            upper_ref_fence_pour_layer=None,
            upper_ref_fence_tag=None,
            deskew_antipad_layers=LayerSet(1),
            deskew_antipad_fence_pour_layer=2,
            deskew_antipad_fence_tag=Ground2DeskewAntipadFenceTag,
        ),
        # Signal2: capsule keepout retained only on L4 (the trace breakout
        # needs a single shared opening); L1/L2/L3 are split into per-via
        # circular cuts by default. The instrumented lane overrides L1 with
        # mirrored D cuts while keeping L2/L3 circular.
        2: PerSignalLayerSpec(
            signal_layer=2,
            deskew_layer=3,
            antipad_layers=LayerSet(3),
            split_antipad_layers=LayerSet(0, 1, 2),
            upper_ref_fence_pour_layer=2,
            upper_ref_fence_tag=Ground2AntipadFenceTag,
            deskew_antipad_layers=LayerSet(3),
            deskew_antipad_fence_pour_layer=4,
            deskew_antipad_fence_tag=Ground3DeskewAntipadFenceTag,
        ),
        3: PerSignalLayerSpec(
            signal_layer=3,
            deskew_layer=5,
            antipad_layers=LayerSet(0, 1, 2, 3, 4, 5),
            upper_ref_fence_pour_layer=4,
            upper_ref_fence_tag=Ground3AntipadFenceTag,
            deskew_antipad_layers=LayerSet(5),
            deskew_antipad_fence_pour_layer=6,
            deskew_antipad_fence_tag=Ground4DeskewAntipadFenceTag,
        ),
        4: PerSignalLayerSpec(
            signal_layer=4,
            deskew_layer=7,
            antipad_layers=LayerSet(0, 1, 2, 3, 4, 5, 6, 7),
            upper_ref_fence_pour_layer=6,
            upper_ref_fence_tag=AntipadFenceTag,
            deskew_antipad_layers=LayerSet(7),
            deskew_antipad_fence_pour_layer=8,
            deskew_antipad_fence_tag=DeskewAntipadFenceTag,
        ),
    }

    @classmethod
    def spec_for_signal_layer(cls, signal_layer: int) -> PerSignalLayerSpec:
        """Launch profile for a signal layer (1..4)."""
        return cls._SIGNAL_LAYER_PROFILES[signal_layer]


# -----------------------------------------------------------------------------
# Per-lane geometry knobs and constants.
# -----------------------------------------------------------------------------


# Signal-via antipad geometry. Two radii around each via: the keepout
# (antipad clearance from the pad edge) and the fence (larger; pour
# boundary). The instrumented lane swaps the keepout for a physics-
# sized split radius on the L1-L3 reference-plane crossings above
# Signal2.
_SIGNAL_VIA_PAD_DIAMETER = 0.25
_SIGNAL_VIA_KEEPOUT_RADIUS = _SIGNAL_VIA_PAD_DIAMETER / 2 + 0.05
_SIGNAL_VIA_FENCE_RADIUS = _SIGNAL_VIA_PAD_DIAMETER / 2 + 0.17
_SIGNAL_VIA_ANTIPAD_OFFSET = 0.15  # buffer applied to deskew copper

_INSTRUMENTED_SIGNAL2_SPLIT_ANTIPAD_RADIUS = 0.38
# Outer radius of the L1 D-cut keepouts; the fence pour also lands here
# (no extra margin past the D-cut — pushing further hit neighbours).
_INSTRUMENTED_SIGNAL2_L1_D_OUTWARD_RADIUS = (
    _INSTRUMENTED_SIGNAL2_SPLIT_ANTIPAD_RADIUS
    + _SIGNAL_VIA_FENCE_RADIUS
    - _SIGNAL_VIA_KEEPOUT_RADIUS
)

# Pour ranks resolve which pour renders when two overlap on the same
# layer; higher wins. Independent from constraint ``priority`` (which
# resolves fence-via dedup at coincident XY).
_ANTIPAD_FENCE_POUR_RANK = 4
_DESKEW_ANTIPAD_FENCE_POUR_RANK = _ANTIPAD_FENCE_POUR_RANK + 10

# Deskew arc geometry (single shared input + clearance pair).
_DESKEW_EXIT_ABOVE_LOWER_BALL = 0.25
_DESKEW_VIA_PAD_TO_TRACE_GAP = 0.10

# Instrumented row pair (the lane the HFSS sim points at). Changing
# this re-points instrumentation; the design itself populates every
# row pair equally.
_INSTRUMENTED_ROW_PAIR = (16, 17)
_INSTRUMENTED_PAIR_INDEX = bga.SIGNAL_ROW_PAIRS.index(_INSTRUMENTED_ROW_PAIR)
_INSTRUMENTED_LANE_INDEX = 1


def _deskew_knobs(lane_index: int) -> tuple[float, float]:
    """Hand-tuned ``(theta_exit_deg, right_r_wrap)`` per lane.

    Smaller ``theta_exit_deg`` lengthens the P-leg wrap. ``right_r_wrap``
    is the wrap radius in mm. Lane 1 carries the HFSS instrumentation.
    """
    return ((92.7, 0.45), (99.6, 0.45), (45.0, 0.50))[lane_index]


# -----------------------------------------------------------------------------
# Geometry helpers (board-level features, antipads, deskew shapes).
# -----------------------------------------------------------------------------


def _make_si_cutout():
    # Cutout edges sit just inside the board-edge stitch-via row. The
    # previous -13.05 caused TXb6 Signal1 coupled-strip ports to touch
    # the top-to-Ground2 ground vias at the port plane. +0.10 mm "edge
    # capture" so boundary GND balls aren't dropped by this helper.
    edge_capture = 0.10
    ymin = -12.95
    ymax = -4.75 + edge_capture
    xmin = -(bga.BGA_LAYOUT_CENTER_COL * bga.BGA_VPITCH) - (bga.BGA_BALL_DIAMETER / 2)
    xmax = (
        ((bga.BGA_COLS - 1) - bga.BGA_LAYOUT_CENTER_COL) * bga.BGA_VPITCH
        + bga.BGA_BALL_DIAMETER / 2
        + edge_capture
    )
    w = xmax - xmin
    h = ymax - ymin
    cx = (xmax + xmin) / 2
    cy = (ymax + ymin) / 2
    return [
        Custom(rectangle(w, h).at(cx, cy), name="SI CUTOUT"),
        Custom(Text("SI Cutout", 0.3).at(cx, cy), name="SI CUTOUT"),
    ]


def _occupied_signal_cols_by_row() -> dict[int, set[int]]:
    occupied: dict[int, set[int]] = {}
    for pair_index, (top_row, bottom_row) in enumerate(bga.SIGNAL_ROW_PAIRS):
        cols = bga.signal_cols_for_pair(pair_index)
        for row_index in (top_row, bottom_row):
            occupied.setdefault(row_index, set()).update(cols)
    return occupied


def _gnd_pad_via_sites() -> list[tuple[int, int, int]]:
    """GND-via stitching plan around every BGA GND ball.

    Pure data: returns ``(row_index, col, signal_layer)`` triples in
    canonical order. ``BGALink`` constructs the actual Via instances
    directly (each site maps to ``substrate.gnd_via[signal_layer]()`` at
    the ball's coordinates), keeping JITX object emission inside the
    owning Circuit rather than in a free helper.

    For each signal row pair, walks the rows above and below, and at
    every (row, col) that isn't itself a signal ball records the
    ``gnd_via`` layer that matches the row pair's signal layer (so the
    via spans L1 to the signal's lower reference plane). If two row
    pairs both reach the same (row, col), the deeper signal layer wins.
    """
    row_col_layers: dict[tuple[int, int], int] = {}
    occupied_signal_cols = _occupied_signal_cols_by_row()

    def add_gnd_row(row_index: int, ground_layer: int) -> None:
        if row_index < 0 or row_index >= bga.BGA_ROWS:
            return
        for col in range(1, bga.BGA_COLS + 1):
            if col in occupied_signal_cols.get(row_index, set()):
                continue
            key = (row_index, col)
            row_col_layers[key] = max(ground_layer, row_col_layers.get(key, 0))

    for pair_index, row_pair in enumerate(bga.SIGNAL_ROW_PAIRS):
        ground_layer = bga.signal_layer_for_pair(pair_index)
        for signal_row in row_pair:
            add_gnd_row(signal_row - 1, ground_layer)
            add_gnd_row(signal_row, ground_layer)
            add_gnd_row(signal_row + 1, ground_layer)

    return [(row, col, layer) for (row, col), layer in sorted(row_col_layers.items())]


def _signal_via_pair_capsule(
    p_pad: tuple[float, float],
    n_pad: tuple[float, float],
    radius: float,
):
    """Capsule with circular caps centered at the two signal via pads."""
    return ShapelyGeometry(shapely.LineString([p_pad, n_pad]).buffer(radius))


def _signal_via_pair_antipad_keepouts(
    keepout_shape,
    spec: PerSignalLayerSpec,
    p_pad: tuple[float, float] | None = None,
    n_pad: tuple[float, float] | None = None,
    split_keepout_radius: float = _SIGNAL_VIA_KEEPOUT_RADIUS,
    split_antipad_layers: LayerSet | None = None,
) -> list[KeepOut]:
    """Antipad keepouts for one signal-via pair.

    Always returns at least one element (the per-pair capsule cut on
    ``spec.antipad_layers``); additional elements appear when
    ``split_antipad_layers`` (defaulting to ``spec.split_antipad_layers``)
    adds per-via circular cuts on those layers.

    The matching upper-reference fence Pour is *not* returned here:
    Pours must live on the same Circuit as the Net they belong to (the
    board-wide ``GND`` Net lives on ``BGALink``), so ``BGALink``
    constructs the Pour itself from the ``fence_shape`` exposed by each
    ``EscapeLane``.
    """
    keepouts: list[KeepOut] = [
        KeepOut(keepout_shape, layers=spec.antipad_layers, pour=True, via=True)
    ]
    active_split_layers = (
        spec.split_antipad_layers
        if split_antipad_layers is None
        else split_antipad_layers
    )
    if active_split_layers is not None:
        if p_pad is None or n_pad is None:
            raise ValueError(
                "split_antipad_layers requires p_pad/n_pad to build per-via "
                "circular keepouts"
            )
        for pad in (p_pad, n_pad):
            circle = ShapelyGeometry(shapely.Point(pad).buffer(split_keepout_radius))
            keepouts.append(
                KeepOut(
                    circle,
                    layers=active_split_layers,
                    pour=True,
                    via=True,
                )
            )

    return keepouts


def _signal_via_d_keepout(
    pad: tuple[float, float],
    partner_pad: tuple[float, float],
    inward_radius: float,
    outward_radius: float,
) -> ShapelyGeometry:
    """Per-via D cut: flat side faces the paired via."""
    px, py = pad
    dx = partner_pad[0] - px
    dy = partner_pad[1] - py
    length = math.hypot(dx, dy)
    if length == 0:
        raise ValueError("D-shaped keepout requires distinct signal-via pads")
    ux = dx / length
    uy = dy / length
    vx = -uy
    vy = ux
    lateral = outward_radius * 4.0
    back = outward_radius * 2.0
    boundary_x = px + ux * inward_radius
    boundary_y = py + uy * inward_radius
    back_x = px - ux * back
    back_y = py - uy * back
    half_plane = shapely.Polygon(
        [
            (boundary_x + vx * lateral, boundary_y + vy * lateral),
            (boundary_x - vx * lateral, boundary_y - vy * lateral),
            (back_x - vx * lateral, back_y - vy * lateral),
            (back_x + vx * lateral, back_y + vy * lateral),
        ]
    )
    disk = shapely.Point(pad).buffer(outward_radius)
    return ShapelyGeometry(disk.intersection(half_plane).buffer(0))


# Mirrored D-cut keepout for the instrumented lane on L1 only (zero-
# based layer index 0). The all-layer D cut expansion to L1/L2/L3 was
# the dominant Scd21 regression source; reverted to the L1-D + L2/L3-
# circular hybrid.
_INSTRUMENTED_D_KEEPOUT_LAYERS = LayerSet(0)


def _instrumented_l1_d_keepouts(
    p_pad: tuple[float, float],
    n_pad: tuple[float, float],
) -> list[KeepOut]:
    return [
        KeepOut(
            _signal_via_d_keepout(
                p_pad,
                n_pad,
                _INSTRUMENTED_SIGNAL2_SPLIT_ANTIPAD_RADIUS,
                _INSTRUMENTED_SIGNAL2_L1_D_OUTWARD_RADIUS,
            ),
            layers=_INSTRUMENTED_D_KEEPOUT_LAYERS,
            pour=True,
            via=True,
        ),
        KeepOut(
            _signal_via_d_keepout(
                n_pad,
                p_pad,
                _INSTRUMENTED_SIGNAL2_SPLIT_ANTIPAD_RADIUS,
                _INSTRUMENTED_SIGNAL2_L1_D_OUTWARD_RADIUS,
            ),
            layers=_INSTRUMENTED_D_KEEPOUT_LAYERS,
            pour=True,
            via=True,
        ),
    ]


def _shape_to_shapely(shape):
    if hasattr(shape, "to_shapely"):
        return shape.to_shapely().g
    return ShapelyGeometry.from_shapegeometry(shape).g


def _deskew_antipad_shape(coppers, antipad_shape) -> ShapelyGeometry:
    geoms = [
        _shape_to_shapely(copper.shape).buffer(_SIGNAL_VIA_ANTIPAD_OFFSET)
        for copper in coppers
        if is_overlappable_copper(copper)
    ]
    geoms.append(_shape_to_shapely(antipad_shape))
    if not geoms:
        raise ValueError("No overlappable deskew copper was provided")
    union = shapely.unary_union(geoms).buffer(0)
    if union.geom_type != "Polygon":
        union = union.convex_hull
    return ShapelyGeometry(union)


def _deskew_antipad_keepout_and_pour_shape(
    right_copper,
    left_copper,
    antipad_shape,
    fence_pour_shape,
    spec: PerSignalLayerSpec,
) -> tuple[KeepOut, ShapelyGeometry]:
    """Build the deskew-layer keepout and the deskew fence Pour's shape.

    ``antipad_shape`` and ``fence_pour_shape`` are usually the same (the
    fence-pour-sized capsule unioned with buffered deskew copper). The
    instrumented lane decouples them: the keepout shrinks to the per-via
    keepout-sized capsule so the L4 cut stays small even when the L1
    D-cut envelope grows.

    The Pour itself is constructed by ``BGALink`` (it must live on the
    same Circuit as the ``GND`` Net it belongs to), so we return the
    keepout (no Net membership, lives on ``EscapeLane``) and the *shape*
    the Pour needs.
    """
    coppers = (right_copper, left_copper)
    keepout_shape = _deskew_antipad_shape(coppers, antipad_shape)
    pour_shape = _deskew_antipad_shape(coppers, fence_pour_shape)
    keepout = KeepOut(
        keepout_shape, layers=spec.deskew_antipad_layers, pour=True, via=True
    )
    return keepout, pour_shape


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
    derives these from ``_deskew_knobs(lane_index)``). The instrumented-
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
        keepout_shape = _signal_via_pair_capsule(
            p_pad, n_pad, _SIGNAL_VIA_KEEPOUT_RADIUS
        )
        split_keepout_radius = _SIGNAL_VIA_KEEPOUT_RADIUS
        split_antipad_layers = spec.split_antipad_layers
        fence_radius = _SIGNAL_VIA_FENCE_RADIUS
        deskew_antipad_radius = fence_radius
        extra_keepouts: list[KeepOut] = []
        if is_instrumented:
            split_keepout_radius = _INSTRUMENTED_SIGNAL2_SPLIT_ANTIPAD_RADIUS
            split_antipad_layers = LayerSet(1, 2)
            fence_radius = _INSTRUMENTED_SIGNAL2_L1_D_OUTWARD_RADIUS
            # Decouple the L4 deskew antipad from the enlarged reference-
            # plane fence perimeter so the L4 cut stays sized to actual
            # deskew copper + buffer.
            deskew_antipad_radius = _SIGNAL_VIA_KEEPOUT_RADIUS
            extra_keepouts = _instrumented_l1_d_keepouts(p_pad, n_pad)

        fence_shape = _signal_via_pair_capsule(p_pad, n_pad, fence_radius)
        deskew_antipad_shape = (
            fence_shape
            if deskew_antipad_radius == fence_radius
            else _signal_via_pair_capsule(p_pad, n_pad, deskew_antipad_radius)
        )

        antipad_keepouts = _signal_via_pair_antipad_keepouts(
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
            exit_above_lower=_DESKEW_EXIT_ABOVE_LOWER_BALL,
            exit_ball_clearance=_DESKEW_VIA_PAD_TO_TRACE_GAP
            - _SIGNAL_VIA_PAD_DIAMETER / 2,
            layer=spec.deskew_layer,
            trace_w=DESKEW_TRACE_WIDTH,
            pair_spacing=DESKEW_PAIR_SPACING,
        )
        self.right_deskew_copper = deskew.right_copper
        self.left_deskew_copper = deskew.left_copper

        self.deskew_antipad_keepout, self.deskew_fence_pour_shape = (
            _deskew_antipad_keepout_and_pour_shape(
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


def _is_instrumented_lane(pair_index: int, lane_index: int) -> bool:
    """The HFSS-instrumented lane lives on a specific Signal2 row pair.

    The signal-layer guard is defensive: if ``_INSTRUMENTED_ROW_PAIR`` is
    ever retargeted off Signal2, the Signal2-specific override (L1
    D-cuts + enlarged L2/L3 circles) silently no-ops instead of
    misapplying to a different layer's antipad stack.
    """
    return (
        pair_index == _INSTRUMENTED_PAIR_INDEX
        and lane_index == _INSTRUMENTED_LANE_INDEX
        and bga.signal_layer_for_pair(pair_index) == 2
    )


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
        # control points; this loop also emits the diff-pair Nets,
        # PortAttachments, and fence Pours — each accumulated into a
        # named list member of this Circuit (the JITX objects
        # themselves, not records of them).
        self.lanes: list[EscapeLane] = []
        signal_nets: list[Net] = []
        signal_via_attachments: list[PortAttachment] = []
        pair_points: list[PairPoint] = []
        pair_insertions: list[PairInsertion] = []
        control_attachments: list[PortAttachment] = []
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

                theta_exit_deg, right_r_wrap = _deskew_knobs(lane_index)
                lane = EscapeLane(
                    p_pad=p_pad,
                    n_pad=n_pad,
                    spec=spec,
                    theta_exit_deg=theta_exit_deg,
                    right_r_wrap=right_r_wrap,
                    is_instrumented=_is_instrumented_lane(pair_index, lane_index),
                )
                self.lanes.append(lane)

                # Diff-pair Net + stripline tag.
                net = Net([tx_pair])
                StriplineDiffPairTag().assign(net)
                signal_nets.append(net)

                # Signal-via attachments at the two BGA pad coordinates.
                signal_via_attachments.append(
                    PortAttachment(tx_pair.p, via_cls().at(*p_pad))
                )
                signal_via_attachments.append(
                    PortAttachment(tx_pair.n, via_cls().at(*n_pad))
                )

                # Pair-control (at the deskew exit midpoint) launches the
                # coupled stripline trunk; insertion-control sits at the
                # board-edge wave-port launch. Both anchor to the BGA pair
                # itself, so the Route walks coupled diff-pair to
                # uncoupled board-edge launch on the deskew layer.
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
                        pair_point.pair,
                        pair_insertion.coupled,
                        spec.deskew_layer,
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
        self.signal_via_attachments = signal_via_attachments
        self.pair_points = pair_points
        self.pair_insertions = pair_insertions
        self.control_attachments = control_attachments
        self.routes = routes
        self.signal_via_fence_pours = signal_via_fence_pours
        self.deskew_fence_pours = deskew_fence_pours

        # GND pour on every conductor layer. ``rank=1`` (instead of 0)
        # makes JITX render the pour as a real fill rather than treating
        # it as a background that gets culled when no higher-rank
        # feature overlaps.
        n_conductors = len(substrate.stackup.conductors)
        gnd_pour_shape = rectangle(48, 48, radius=4)
        gnd_pours = [
            Pour(gnd_pour_shape, layer=layer, rank=1, isolate=0.0)
            for layer in range(n_conductors)
        ]

        # GND-via stitching around every BGA GND ball. The site-planning
        # helper returns pure data; this Circuit constructs the actual
        # Via instances and owns them as a named structural member.
        self.gnd_stitching_vias = [
            substrate.gnd_via[signal_layer]().at(*bga.ball_center(row, col))
            for row, col, signal_layer in _gnd_pad_via_sites()
        ]

        self.GND = Net(
            [
                *self.bga.GND,
                *gnd_pours,
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

        self.sicut = _make_si_cutout()


class bga_optimization_design(SampleDesign):
    substrate = BGAEscapeSubstrate()
    circuit = BGALink()

"""Per-lane SI escape geometry for the BGA escape design.

Signal-via antipad shapes and keepouts, deskew-arc cross-section and
per-lane knobs, GND-via stitching sites, the board-level SI cutout, and
the HFSS-instrumented-lane override. Helpers here build shapes and
``KeepOut``s only; JITX objects with Net membership (``Pour``s, Vias)
are constructed by the owning Circuit in ``bga_escape``.
"""

import math

import shapely
from jitx import KeepOut, LayerSet
from jitx.feature import Custom
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Text
from jitx.shapes.shapely import ShapelyGeometry
from . import generic_bga as bga
from .deskew import is_overlappable_copper
from .substrate import PerSignalLayerSpec


# -----------------------------------------------------------------------------
# Per-lane geometry knobs and constants.
# -----------------------------------------------------------------------------

# Deskew-arc cross-section. Decoupled from ``substrate.DIFFPAIR_*``: the
# deskew arc routes its two legs as largely-uncoupled single-ended
# traces, so each leg's local Z is set by trace width vs. reference-
# plane spacing, not by the inner edge-to-edge gap. Widening the legs
# from 0.115 -> 0.150 mm pulls Z_se down toward 46 ohm -> Z_diff toward
# 85 ohm; inner gap preserved at the original 0.118 mm.
DESKEW_TRACE_WIDTH = 0.138
DESKEW_PAIR_SPACING = 0.118

# Signal-via antipad geometry. Two radii around each via: the keepout
# (antipad clearance from the pad edge) and the fence (larger; pour
# boundary). The instrumented lane swaps the keepout for a physics-
# sized split radius on the L1-L3 reference-plane crossings above
# Signal2.
SIGNAL_VIA_PAD_DIAMETER = 0.25
SIGNAL_VIA_KEEPOUT_RADIUS = SIGNAL_VIA_PAD_DIAMETER / 2 + 0.05
SIGNAL_VIA_FENCE_RADIUS = SIGNAL_VIA_PAD_DIAMETER / 2 + 0.17
_SIGNAL_VIA_ANTIPAD_OFFSET = 0.15  # buffer applied to deskew copper

# Deskew arc geometry (single shared input + clearance pair).
DESKEW_EXIT_ABOVE_LOWER_BALL = 0.25
DESKEW_VIA_PAD_TO_TRACE_GAP = 0.10


def deskew_knobs(lane_index: int) -> tuple[float, float]:
    """Hand-tuned ``(theta_exit_deg, right_r_wrap)`` per lane.

    Smaller ``theta_exit_deg`` lengthens the P-leg wrap. ``right_r_wrap``
    is the wrap radius in mm. Lane 1 carries the HFSS instrumentation.
    """
    return ((92.7, 0.45), (99.6, 0.45), (45.0, 0.50))[lane_index]


# -----------------------------------------------------------------------------
# Geometry helpers (board-level features, antipads, deskew shapes).
# -----------------------------------------------------------------------------


def make_si_cutout():
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


def gnd_pad_via_sites() -> list[tuple[int, int, int]]:
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


def signal_via_pair_capsule(
    p_pad: tuple[float, float],
    n_pad: tuple[float, float],
    radius: float,
):
    """Capsule with circular caps centered at the two signal via pads."""
    return ShapelyGeometry(shapely.LineString([p_pad, n_pad]).buffer(radius))


def signal_via_pair_antipad_keepouts(
    keepout_shape,
    spec: PerSignalLayerSpec,
    p_pad: tuple[float, float] | None = None,
    n_pad: tuple[float, float] | None = None,
    split_keepout_radius: float = SIGNAL_VIA_KEEPOUT_RADIUS,
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


def deskew_antipad_keepout_and_pour_shape(
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
# HFSS-instrumented lane.
# -----------------------------------------------------------------------------

INSTRUMENTED_SIGNAL2_SPLIT_ANTIPAD_RADIUS = 0.38
# Outer radius of the L1 D-cut keepouts; the fence pour also lands here
# (no extra margin past the D-cut — pushing further hit neighbours).
INSTRUMENTED_SIGNAL2_L1_D_OUTWARD_RADIUS = (
    INSTRUMENTED_SIGNAL2_SPLIT_ANTIPAD_RADIUS
    + SIGNAL_VIA_FENCE_RADIUS
    - SIGNAL_VIA_KEEPOUT_RADIUS
)

# Instrumented row pair (the lane the HFSS sim points at). Changing
# this re-points instrumentation; the design itself populates every
# row pair equally.
_INSTRUMENTED_ROW_PAIR = (16, 17)
_INSTRUMENTED_PAIR_INDEX = bga.SIGNAL_ROW_PAIRS.index(_INSTRUMENTED_ROW_PAIR)
_INSTRUMENTED_LANE_INDEX = 1

# Mirrored D-cut keepout for the instrumented lane on L1 only (zero-
# based layer index 0). The all-layer D cut expansion to L1/L2/L3 was
# the dominant Scd21 regression source; reverted to the L1-D + L2/L3-
# circular hybrid.
_INSTRUMENTED_D_KEEPOUT_LAYERS = LayerSet(0)


def instrumented_l1_d_keepouts(
    p_pad: tuple[float, float],
    n_pad: tuple[float, float],
) -> list[KeepOut]:
    return [
        KeepOut(
            _signal_via_d_keepout(
                p_pad,
                n_pad,
                INSTRUMENTED_SIGNAL2_SPLIT_ANTIPAD_RADIUS,
                INSTRUMENTED_SIGNAL2_L1_D_OUTWARD_RADIUS,
            ),
            layers=_INSTRUMENTED_D_KEEPOUT_LAYERS,
            pour=True,
            via=True,
        ),
        KeepOut(
            _signal_via_d_keepout(
                n_pad,
                p_pad,
                INSTRUMENTED_SIGNAL2_SPLIT_ANTIPAD_RADIUS,
                INSTRUMENTED_SIGNAL2_L1_D_OUTWARD_RADIUS,
            ),
            layers=_INSTRUMENTED_D_KEEPOUT_LAYERS,
            pour=True,
            via=True,
        ),
    ]


def is_instrumented_lane(pair_index: int, lane_index: int) -> bool:
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

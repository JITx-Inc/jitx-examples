"""Reusable arc-polyline deskew geometry for BGA diff-pair escapes."""

import math
from dataclasses import dataclass

from jitx.feature import OverlappableCopper
from jitx.shapes.primitive import Arc, ArcPolyline


DEFAULT_LAYER = 7  # L8-Signal4, zero-based layer index
DEFAULT_TRACE_W = 0.13
DEFAULT_PAIR_SPACING = 0.10
DEFAULT_BALL_DIA = 0.5
DEFAULT_EXIT_ABOVE_LOWER_BALL = 0.25
DEFAULT_EXIT_BALL_CLEARANCE = 0.0
DEFAULT_RIGHT_R_WRAP = 0.5
_ANGLE_EPS_DEG = 1e-6
_MIN_SWEEP_DEG = 1e-3
_MAX_ARC_SWEEP_DEG = 180.0
_GEOMETRY_EPS = 1e-9


@dataclass(frozen=True)
class DeskewBuild:
    """Result of one ``deskew_pair`` call."""

    right_shape: ArcPolyline
    left_shape: ArcPolyline
    right_copper: OverlappableCopper
    left_copper: OverlappableCopper
    right_exit: tuple[float, float]
    left_exit: tuple[float, float]
    bbox: tuple[float, float, float, float]


def _copper(shape: ArcPolyline, layer: int):
    return OverlappableCopper(shape, layer=layer)


def is_overlappable_copper(copper) -> bool:
    return OverlappableCopper is not None and isinstance(copper, OverlappableCopper)


def _require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be positive, got {value!r}")


def _normalize_angle_deg(angle_deg: float) -> float:
    if not math.isfinite(angle_deg):
        raise ValueError(f"angle must be finite, got {angle_deg!r}")
    value = angle_deg % 360.0
    return 0.0 if math.isclose(value, 360.0, abs_tol=_ANGLE_EPS_DEG) else value


def _validate_arc_sweep(
    name: str,
    sweep_deg: float,
    *,
    min_abs_deg: float = _MIN_SWEEP_DEG,
    max_abs_deg: float = _MAX_ARC_SWEEP_DEG,
) -> None:
    if not math.isfinite(sweep_deg):
        raise ValueError(f"{name} sweep must be finite, got {sweep_deg!r}")
    abs_sweep = abs(sweep_deg)
    if abs_sweep < min_abs_deg:
        raise ValueError(
            f"{name} sweep {sweep_deg:.6f} deg is too small; "
            "choose a different theta_exit_deg / right_r_wrap"
        )
    if abs_sweep > max_abs_deg + _ANGLE_EPS_DEG:
        raise ValueError(
            f"{name} sweep {sweep_deg:.6f} deg exceeds {max_abs_deg:.1f} deg; "
            "refusing to generate a near-full-circle deskew arc"
        )


def deskew_pair(
    *,
    right_pad: tuple[float, float],
    left_pad: tuple[float, float],
    theta_exit_deg: float = 0.0,
    layer: int = DEFAULT_LAYER,
    trace_w: float = DEFAULT_TRACE_W,
    pair_spacing: float = DEFAULT_PAIR_SPACING,
    ball_dia: float = DEFAULT_BALL_DIA,
    exit_above_lower: float = DEFAULT_EXIT_ABOVE_LOWER_BALL,
    exit_ball_clearance: float = DEFAULT_EXIT_BALL_CLEARANCE,
    right_r_wrap: float = DEFAULT_RIGHT_R_WRAP,
) -> DeskewBuild:
    """Build deskew copper for one vertical diff pair.

    ``right_pad`` is the lower-Y ball and receives the wrapping leg.
    ``left_pad`` is the upper-Y ball and receives the larger concentric arc.
    The names describe geometric slots from the recovered generator, not
    electrical polarity.
    """
    _require_positive("trace_w", trace_w)
    if not math.isfinite(pair_spacing) or pair_spacing < 0.0:
        raise ValueError(f"pair_spacing must be non-negative, got {pair_spacing!r}")
    _require_positive("ball_dia", ball_dia)
    _require_positive("right_r_wrap", right_r_wrap)
    if not math.isclose(right_pad[0], left_pad[0]):
        raise ValueError(
            f"right_pad and left_pad must share an X column "
            f"({right_pad[0]} vs {left_pad[0]})"
        )
    if right_pad[1] >= left_pad[1]:
        raise ValueError(
            f"right_pad must sit below left_pad in Y ({right_pad[1]} >= {left_pad[1]})"
        )
    pair_y_pitch = left_pad[1] - right_pad[1]
    if not (0.0 < exit_above_lower < pair_y_pitch):
        raise ValueError(
            f"exit_above_lower must be between 0 and pair pitch "
            f"{pair_y_pitch:.4f}, got {exit_above_lower!r}"
        )

    pair_pitch = trace_w + pair_spacing
    ball_half = ball_dia / 2
    ball_x = right_pad[0]

    exit_y = right_pad[1] + exit_above_lower
    struct_right_x = ball_x - ball_half - exit_ball_clearance
    right_trace_x = struct_right_x - trace_w / 2
    left_trace_x = right_trace_x - pair_pitch

    right_exit = (right_trace_x, exit_y)
    left_exit = (left_trace_x, exit_y)

    bx, by = right_pad
    rex, rey = right_exit
    dx_r = rex - bx
    dy_r = rey - by
    denom = 2.0 * (dx_r + right_r_wrap)
    if abs(denom) <= _GEOMETRY_EPS:
        raise ValueError("Singular geometry: dx + right_r_wrap = 0")
    r3 = (right_r_wrap * right_r_wrap - dx_r * dx_r - dy_r * dy_r) / denom
    if not (0.0 < r3 < right_r_wrap):
        raise ValueError(
            f"r3 = {r3:.4f} out of (0, {right_r_wrap}); choose a different "
            f"right_r_wrap / exit"
        )

    sin_t2 = dy_r / (right_r_wrap - r3)
    cos_t2 = (dx_r + r3) / (right_r_wrap - r3)
    theta_2_deg = math.degrees(math.atan2(sin_t2, cos_t2))
    c_3 = (rex + r3, rey)

    right_arcline = _build_right_trace(
        right_pad,
        right_exit,
        right_r_wrap,
        theta_exit_deg,
        c_3,
        r3,
        theta_2_deg,
        trace_w,
    )
    left_arcline = _build_left_trace(left_pad, left_exit, c_3, trace_w)

    xmin = left_trace_x - trace_w / 2
    xmax = ball_x + max(ball_half, right_r_wrap)
    ymin = right_pad[1] - right_r_wrap
    ymax = left_pad[1] + ball_half

    return DeskewBuild(
        right_shape=right_arcline,
        left_shape=left_arcline,
        right_copper=_copper(right_arcline, layer),
        left_copper=_copper(left_arcline, layer),
        right_exit=right_exit,
        left_exit=left_exit,
        bbox=(xmin, ymin, xmax, ymax),
    )


def _build_left_trace(
    left_pad: tuple[float, float],
    left_exit: tuple[float, float],
    c_3: tuple[float, float],
    trace_w: float,
) -> ArcPolyline:
    # Left leg: an arc on the circle of radius |c_3->left_exit| about c_3, swept
    # clockwise from left_exit to the point where it becomes tangent to the line
    # into the off-circle left_pad, then a straight segment into the pad.
    cx, cy = c_3
    r = math.hypot(left_exit[0] - cx, left_exit[1] - cy)

    px, py = left_pad
    dx_p = px - cx
    dy_p = py - cy
    norm = math.hypot(dx_p, dy_p)
    if r > norm + _GEOMETRY_EPS:
        raise ValueError(
            f"left_pad inside fillet circle (r={r:.4f} > |c_3-pad|={norm:.4f})"
        )
    if norm <= _GEOMETRY_EPS:
        raise ValueError("left_pad coincides with fillet center")

    phi = math.degrees(math.atan2(dy_p, dx_p))
    delta = math.degrees(math.acos(max(-1.0, min(1.0, r / norm))))
    alpha_end = phi + delta
    sweep_deg = alpha_end - 180.0
    if sweep_deg >= -_MIN_SWEEP_DEG:
        raise ValueError(
            f"left trace arc sweep {sweep_deg:.6f} deg is not clockwise; "
            "choose a different theta_exit_deg / right_r_wrap"
        )
    _validate_arc_sweep("left trace arc", sweep_deg)

    return ArcPolyline(
        trace_w,
        [
            left_exit,
            Arc((cx, cy), r, 180.0, sweep_deg),
            left_pad,
        ],
    )


def _build_right_trace(
    right_pad: tuple[float, float],
    right_exit: tuple[float, float],
    radius: float,
    theta_exit_deg: float,
    c_3: tuple[float, float],
    r3: float,
    theta_2_deg: float,
    trace_w: float,
) -> ArcPolyline:
    # Right leg: three tangent arcs from right_pad to right_exit -- a half-circle
    # wrap of radius/2 off the pad, a main arc of radius about the pad, then a
    # fillet arc of r3 on the c_3 circle into the exit.
    bx, by = right_pad
    theta_exit_norm = _normalize_angle_deg(theta_exit_deg)
    theta_e = math.radians(theta_exit_norm)
    cos_e, sin_e = math.cos(theta_e), math.sin(theta_e)

    m1 = (bx + (radius / 2) * cos_e, by + (radius / 2) * sin_e)
    arc1_start_deg = theta_exit_norm + 180.0
    arc1_sweep_deg = 180.0
    arc2_sweep_deg = theta_2_deg - theta_exit_norm
    arc3_sweep_deg = 180.0 - theta_2_deg
    if arc2_sweep_deg <= _MIN_SWEEP_DEG:
        raise ValueError(
            f"theta_exit_deg={theta_exit_deg:.6f} deg is at or beyond the "
            f"right-trace tangent angle {theta_2_deg:.6f} deg for "
            f"right_r_wrap={radius:.4f}; raw arc sweep would be "
            f"{arc2_sweep_deg:.6f} deg"
        )
    _validate_arc_sweep("right trace arc 1", arc1_sweep_deg)
    _validate_arc_sweep("right trace arc 2", arc2_sweep_deg)
    _validate_arc_sweep("right trace arc 3", arc3_sweep_deg)

    return ArcPolyline(
        trace_w,
        [
            right_pad,
            Arc(m1, radius / 2, arc1_start_deg, arc1_sweep_deg),
            Arc((bx, by), radius, theta_exit_norm, arc2_sweep_deg),
            Arc(c_3, r3, theta_2_deg, arc3_sweep_deg),
            right_exit,
        ],
    )

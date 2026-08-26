"""BGA-escape substrate specialization.

``BGAEscapeSubstrate`` extends the generic 20-layer substrate with the
85 ohm differential stripline routing structure and the per-signal-layer
launch profile table (``PerSignalLayerSpec``), and anchors the antipad
fence-via rules defined in ``constraints`` into the design tree. The
substrate base file stays truly generic; everything BGA-escape-specific
attaches here.
"""

from dataclasses import dataclass

from jitx import KeepOut, LayerSet
from jitx.constraints import ViaFencePattern
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
from . import constraints
from .constraints import (
    BGA_ANTIPAD_FENCE_PITCH,
    AntipadFenceTag,
    DeskewAntipadFenceTag,
    Ground2AntipadFenceTag,
    Ground2DeskewAntipadFenceTag,
    Ground3AntipadFenceTag,
    Ground3DeskewAntipadFenceTag,
    Ground4DeskewAntipadFenceTag,
)


# -----------------------------------------------------------------------------
# Stripline geometry constants.
# -----------------------------------------------------------------------------

BGA_MAIN_TRUNK_DP_TO_GND = 0.25

# Diff-pair stripline geometry for every 85 ohm signal layer (L2/L4/L6/L8).
DIFFPAIR_TRACE_WIDTH = 0.115
DIFFPAIR_PAIR_SPACING = 0.118

# Route-following pour keepout corridor width on the signal layer.
# ``geometry(KeepOut, width, ...)`` is applied per-trace centered on
# each leg's centerline; the two per-leg corridors union together. So
# the per-leg width is just trace_width + 2 x clearance -- adding the
# pair span here double-counts pair_spacing + trace_width on each side.
_DP_TO_GND_POUR_CORRIDOR = DIFFPAIR_TRACE_WIDTH + 2 * BGA_MAIN_TRUNK_DP_TO_GND


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
# anchored design_constraint rules, and per-signal-layer launch profiles.
# -----------------------------------------------------------------------------


class BGAEscapeSubstrate(Generic_Substrate):
    """Generic 20-layer substrate specialized for the BGA escape design.

    Adds the 85 ohm differential stripline routing structure (one entry
    per signal layer plus its symmetric mirror) and the per-signal-layer
    launch profile table (queried by each ``EscapeLane``), and anchors
    the ``constraints`` fence-via rules that drive antipad / fence-via
    generation around the BGA breakout cavity.
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

    # Anchor the antipad fence-via rules defined in ``constraints``:
    # JITX discovers ``DesignConstraint`` rules by walking the design
    # tree, so each rule must be reachable as a substrate (or circuit)
    # attribute to take effect.
    signal_via_antipad_fence = constraints.signal_via_antipad_fence
    signal_via_antipad_fence_g3 = constraints.signal_via_antipad_fence_g3
    signal_via_antipad_fence_g2 = constraints.signal_via_antipad_fence_g2
    deskew_antipad_fence = constraints.deskew_antipad_fence
    deskew_antipad_fence_g4 = constraints.deskew_antipad_fence_g4
    deskew_antipad_fence_g3 = constraints.deskew_antipad_fence_g3
    deskew_antipad_fence_g2 = constraints.deskew_antipad_fence_g2

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

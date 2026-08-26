"""Design-rule ``Tag`` subclasses and antipad fence-via rules for the
BGA escape design.

``StriplineDiffPairTag`` keys the 85 ohm differential routing structure
rule (built in ``bga_escape.BGALink``, which owns the GND reference
net); the antipad fence tags key the per-layer fence-via rules defined
at the bottom of this file.

JITX discovers ``DesignConstraint`` rules by walking the design object
tree, so a module-level rule takes effect only once it is reachable
from the design — the rules here are anchored as attributes of
``substrate.BGAEscapeSubstrate``.
"""

from jitx.constraints import Tag, ViaFencePattern, design_constraint
from jitxexamples.substrates.generic_20layer import Generic_Substrate


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
# Antipad fence-via pattern.
# -----------------------------------------------------------------------------

BGA_ANTIPAD_FENCE_PITCH = 0.35
BGA_ANTIPAD_FENCE_OFFSET = 0.15
BGA_ANTIPAD_FENCE_MIN_EDGE_CLEARANCE = -0.02


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


# Fence pattern around the signal-via antipad cavity. Sized off the
# uGnd_L1_L7 via diameter so the fence-via pad sits just outside the
# antipad opening.
_ANTIPAD_FENCE_PATTERN = _antipad_fence_pattern(
    float(Generic_Substrate.uGnd_L1_L7.diameter) + 0.075
)


# -----------------------------------------------------------------------------
# Antipad fence-via rules.
# -----------------------------------------------------------------------------

# Constraint ``priority`` breaks ties when generated fence vias from
# competing rules want to land at the same X/Y; higher wins. The
# antipad fence and deskew fence intentionally use DIFFERENT via
# classes: the antipad fence closes only the upper cavity
# (uGnd_L1_L<upper-ref>); the deskew fence closes only the lower
# cavity (uFence_L<upper-ref>_L<lower-ref>). Unifying them to
# uGnd_L1_L<lower-ref> catastrophically regressed Scd21 (gen7_nyquist
# -32.62 -> -24.10 dB) by routing longer fence vias through the
# signal layer adjacent to the launch.
signal_via_antipad_fence = design_constraint(AntipadFenceTag(), priority=20).fence_via(
    Generic_Substrate.uGnd_L1_L7, _ANTIPAD_FENCE_PATTERN
)

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

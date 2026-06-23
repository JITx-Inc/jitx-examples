"""Generic 20-layer substrate.

Explicit-symmetry stack: 20 conductor layers about a thick core, one
generic dielectric (Dk 3.0) throughout, 0.5 oz copper on every layer,
0.8 mm core. The upper half (L1..L10) interleaves ground/signal planes
with L1 as outer ground and L10 adjacent to the core as a power plane;
L11..L20 are the explicit mirror. The substrate exposes the HDI via
families needed for top-side BGA escape via the ``signal_via`` and
``gnd_via`` accessors so designs query the substrate instead of
mirroring tables.
"""

from jitx.stackup import Stackup, Conductor, Dielectric
from jitx.substrate import Substrate, FabricationConstraints
from jitx.via import Via, ViaType
from jitx.si import PinModel
from jitx.layerindex import Side
from jitxlib.physics import phase_velocity


# -----------------------------------------------------------------------------
# Materials
# -----------------------------------------------------------------------------


class GenericDielectric(Dielectric):
    """Generic low-loss dielectric -- Dk 3.0, tan delta 0.004."""

    dielectric_coefficient = 3.0
    loss_tangent = 0.004


class SolderMask(Dielectric):
    """Generic soldermask."""

    dielectric_coefficient = 3.8
    loss_tangent = 0.02


class GenericCopper(Conductor):
    """0.5 oz copper -- 0.0175 mm thick.

    ``roughness`` is intentionally left unset, so no per-conductor
    surface-roughness boundary is generated. Set it when modelling
    fab-grade conductor loss (a Hammerstad ratio, or a Huray
    ``(nodule_radius_m, area_ratio)`` tuple)."""


VEL_STRIPLINE = phase_velocity(3.0)


# -----------------------------------------------------------------------------
# Stackup: explicit 20-layer mirror about the thick core dielectric.
# -----------------------------------------------------------------------------


class Generic_Stackup(Stackup):
    """Explicit 20-conductor stack with one generic dielectric throughout."""

    top_mask = SolderMask(thickness=0.0127)

    # Upper half: L1 (outer ground) -> L10 (power, adjacent to core)
    L1_Ground1 = GenericCopper(thickness=0.0175, name="L1-Ground1")
    d_1_2 = GenericDielectric(thickness=0.1)
    L2_Signal1 = GenericCopper(thickness=0.0175, name="L2-Signal1")
    d_2_3 = GenericDielectric(thickness=0.1)
    L3_Ground2 = GenericCopper(thickness=0.0175, name="L3-Ground2")
    d_3_4 = GenericDielectric(thickness=0.1)
    L4_Signal2 = GenericCopper(thickness=0.0175, name="L4-Signal2")
    d_4_5 = GenericDielectric(thickness=0.1)
    L5_Ground3 = GenericCopper(thickness=0.0175, name="L5-Ground3")
    d_5_6 = GenericDielectric(thickness=0.1)
    L6_Signal3 = GenericCopper(thickness=0.0175, name="L6-Signal3")
    d_6_7 = GenericDielectric(thickness=0.1)
    L7_Ground4 = GenericCopper(thickness=0.0175, name="L7-Ground4")
    d_7_8 = GenericDielectric(thickness=0.1)
    L8_Signal4 = GenericCopper(thickness=0.0175, name="L8-Signal4")
    d_8_9 = GenericDielectric(thickness=0.1)
    L9_Ground5 = GenericCopper(thickness=0.0175, name="L9-Ground5")
    d_9_10 = GenericDielectric(thickness=0.1)
    L10_Power1 = GenericCopper(thickness=0.0175, name="L10-Power1")

    # Center dielectric: thick core.
    d_center = GenericDielectric(thickness=0.8, name="Core")

    # Lower half: explicit mirror of the upper half. Layer N+10 mirrors
    # layer 11-N; e.g. L11_Power1 mirrors L10_Power1, L20_Ground1 mirrors
    # L1_Ground1.
    L11_Power1 = GenericCopper(thickness=0.0175, name="L11-Power1")
    d_11_12 = GenericDielectric(thickness=0.1)
    L12_Ground5 = GenericCopper(thickness=0.0175, name="L12-Ground5")
    d_12_13 = GenericDielectric(thickness=0.1)
    L13_Signal4 = GenericCopper(thickness=0.0175, name="L13-Signal4")
    d_13_14 = GenericDielectric(thickness=0.1)
    L14_Ground4 = GenericCopper(thickness=0.0175, name="L14-Ground4")
    d_14_15 = GenericDielectric(thickness=0.1)
    L15_Signal3 = GenericCopper(thickness=0.0175, name="L15-Signal3")
    d_15_16 = GenericDielectric(thickness=0.1)
    L16_Ground3 = GenericCopper(thickness=0.0175, name="L16-Ground3")
    d_16_17 = GenericDielectric(thickness=0.1)
    L17_Signal2 = GenericCopper(thickness=0.0175, name="L17-Signal2")
    d_17_18 = GenericDielectric(thickness=0.1)
    L18_Ground2 = GenericCopper(thickness=0.0175, name="L18-Ground2")
    d_18_19 = GenericDielectric(thickness=0.1)
    L19_Signal1 = GenericCopper(thickness=0.0175, name="L19-Signal1")
    d_19_20 = GenericDielectric(thickness=0.1)
    L20_Ground1 = GenericCopper(thickness=0.0175, name="L20-Ground1")

    bottom_mask = SolderMask(thickness=0.0127)


# -----------------------------------------------------------------------------
# Fabrication constraints
# -----------------------------------------------------------------------------


class Generic_FabRules(FabricationConstraints):
    # HDI-class fab floors tight enough that the routing structure's
    # neckdown ``clearance=0.05`` isn't clamped up by the fab rule.
    min_copper_width = 0.04
    min_copper_copper_space = 0.05
    min_copper_hole_space = 0.05
    min_copper_edge_space = 0.15
    min_annular_ring = 0.04
    min_drill_diameter = 0.05
    min_hole_to_hole = 0.3
    min_pitch_leaded = 0.2
    min_pitch_bga = 0.4
    max_board_width = 500
    max_board_height = 400
    min_silkscreen_width = 0.1
    min_silk_solder_mask_space = 0.05
    min_silkscreen_text_height = 0.6
    solder_mask_registration = 0.025
    min_soldermask_opening = 0.025
    min_soldermask_bridge = 0.04
    min_th_pad_expand_outer = 0.08
    min_pth_pin_solder_clearance = 0.0


# -----------------------------------------------------------------------------
# Substrate definition: vias + introspection accessors.
# -----------------------------------------------------------------------------


class Generic_Substrate(Substrate):
    """Generic 20-layer substrate. Truly reusable: holds materials,
    stackup, fab rules, and HDI vias only; design-specific tags,
    routing structures, and fence-via rules attach in a design subclass.
    """

    stackup = Generic_Stackup()
    constraints = Generic_FabRules()

    # --- HDI signal-launch vias (L1 -> signal layer) -----------------------
    class uVia_L1_L2(Via):
        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 1
        diameter = 0.25
        hole_diameter = 0.1
        filled = True
        via_in_pad = True
        models = {(0, 1): PinModel(0.0, 0.0)}

    class uVia_L1_L4(Via):
        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 3
        diameter = 0.25
        hole_diameter = 0.1
        filled = True
        via_in_pad = True
        models = {(0, 3): PinModel(0.0, 0.0)}

    class uVia_L1_L6(Via):
        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 5
        diameter = 0.25
        hole_diameter = 0.1
        filled = True
        via_in_pad = True
        models = {(0, 5): PinModel(0.0, 0.0)}

    class uVia_L1_L8(Via):
        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 7
        diameter = 0.25
        hole_diameter = 0.1
        filled = True
        via_in_pad = True
        models = {(0, 7): PinModel(0.0, 0.0)}

    # --- GND fence uVias from L1 to the lower reference plane of each signal
    class uGnd_L1_L3(Via):
        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 2
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uGnd_L1_L5(Via):
        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 4
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uGnd_L1_L7(Via):
        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 6
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uGnd_L1_L9(Via):
        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 8
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    # --- Routing-structure fence vias: one per signal layer, spanning the
    # stripline's two reference planes. ``Lk_Lm`` is (upper, lower)
    # reference layer index for the diff-pair stripline on signal Lk.
    class uFence_L1_L3(Via):
        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 2
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uFence_L3_L5(Via):
        type = ViaType.LaserDrill
        start_layer = 2
        stop_layer = 4
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uFence_L5_L7(Via):
        type = ViaType.LaserDrill
        start_layer = 4
        stop_layer = 6
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uFence_L7_L9(Via):
        type = ViaType.LaserDrill
        start_layer = 6
        stop_layer = 8
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    # Bottom-half mirror fence vias for the symmetric stack. ``start/stop`` are
    # negative indices so they track the mirrored stripline reference planes.
    class uFence_L18_L20(Via):
        type = ViaType.LaserDrill
        start_layer = -3
        stop_layer = -1
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uFence_L16_L18(Via):
        type = ViaType.LaserDrill
        start_layer = -5
        stop_layer = -3
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uFence_L14_L16(Via):
        type = ViaType.LaserDrill
        start_layer = -7
        stop_layer = -5
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    class uFence_L12_L14(Via):
        type = ViaType.LaserDrill
        start_layer = -9
        stop_layer = -7
        diameter = 0.25
        hole_diameter = 0.1
        filled = True

    # Mechanical through-hole via for stitching + PTH components.
    class TH_Via(Via):
        type = ViaType.MechanicalDrill
        start_layer = Side.Top
        stop_layer = Side.Bottom
        diameter = 0.5
        hole_diameter = 0.25
        filled = True

    # Top-half GND stitch via: L1 (outer GND pour) down to L9 (Ground5).
    # Gives reference-plane continuity across the inner-layer escape
    # without crossing the core.
    class uStitch_L1_L9(Via):
        type = ViaType.LaserDrill
        start_layer = 0
        stop_layer = 8
        diameter = 0.25
        hole_diameter = 0.1
        filled = True
        via_in_pad = True

    # Mirror stitch via for the bottom half: L20 <-> L12.
    class uStitch_L12_L20(Via):
        type = ViaType.LaserDrill
        start_layer = -9
        stop_layer = -1
        diameter = 0.25
        hole_diameter = 0.1
        filled = True
        via_in_pad = True

    # --- Introspection accessors ------------------------------------------
    # Designs query these instead of restating substrate-shaped tables.

    @property
    def signal_via(self) -> dict[int, type[Via]]:
        """Signal-launch via class keyed by signal-layer index (1..4)."""
        return {
            1: self.uVia_L1_L2,
            2: self.uVia_L1_L4,
            3: self.uVia_L1_L6,
            4: self.uVia_L1_L8,
        }

    @property
    def gnd_via(self) -> dict[int, type[Via]]:
        """Matching GND fence-via class keyed by signal-layer index (1..4).
        Returns the via that spans L1 to the signal's lower reference plane."""
        return {
            1: self.uGnd_L1_L3,
            2: self.uGnd_L1_L5,
            3: self.uGnd_L1_L7,
            4: self.uGnd_L1_L9,
        }

    @property
    def n_conductors(self) -> int:
        """Total number of conductor layers in the stackup."""
        return len(self.stackup.conductors)

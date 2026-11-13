"""SI constraints for the VP1002 to Micron LPDDR4 link, from AMD UG863.

Source: AMD, *Versal Adaptive SoC PCB Design User Guide*, UG863 v1.12
(2026-06-16): "Timing Constraint Rules for LPDDR4/4x Signals", Table 25 "Skew
Constraint Rules for LPDDR4/4x Signals", and "Physical Design Rules for
LPDDR4/4x Signals", Table 24,
https://docs.amd.com/r/en-US/ug863-versal-pcb-design.

:py:class:`VersalLPDDR4Constraint` is reusable: it takes the routing
structures and the limits as arguments, so another board with this link, or
a revision of UG863 that changes only limits, changes values, not code. It builds on the
library's :py:class:`~jitxexamples.protocols.memory.lpddr4.LPDDR4Constraint`
for the skew rules and adds UG863's trace length rule as a delay limit.

Timing (skew) rules applied
---------------------------

======================================  ================  ==========================
UG863 timing Table 25 row                Limit             ``LPDDR4ConstraintParams``
======================================  ================  ==========================
Address to Clock A/B: CA[5:0] to CK_T   -100 to +100 ps   ``skew_ck_ca``
Command to Clock A/B: CKE, CS to CK_T   -20 to +20 ps     ``skew_ck_cke``,
                                                          ``skew_ck_cs``
Clock (A or B): CK_T to CK_C            0 to 2 ps         ``skew_ck``
Data to DQS0 to DQS3: DQ, DM to DQS_T   -100 to +100 ps   ``skew_dqs_dq``
DQS0 to DQS3: DQS_T to DQS_C            0 to 2 ps         ``skew_dqs``
DQS0/1 to CK_A, DQS2/3 to CK_B          -150 to +150 ps   ``skew_ck_dqs``
======================================  ================  ==========================

The intra-pair rows carry the note "It does not matter which signal is
faster or slower", so 0 to 2 ps is applied as +/-2 ps.

CKE: the table lists CKE0 and CKE1 per channel, CKE1 on dual-rank devices
only. The supplied VP1002 offer drives one CKE per channel, as AMD's own
boards do, and the design nets it to both of the memory's CKE balls, so
``skew_ck_cke`` holds each ball against CK_T.

The kit's layout targets
------------------------

:py:data:`KIT_PARAMS` is the set Part 3 applies. The kit sets a layout
target at 20% of UG863 Table 25's limit on four rules: DQ and DM to DQS_T
(+/-20 ps), each DQS and CK pair (+/-0.4 ps), and CKE and CS to CK_T
(+/-4 ps). This is the kit's choice. CA to CK_T and DQS to CK_T keep
UG863's limits. A target below the limit leaves margin for simulation and
for the package delays, which are synthetic estimates here. TI SPRAD66B,
*AM62Ax, AM62Px, AM62Dx LPDDR4 Board Design and Layout Guidelines*, revised
December 2024, recommends matching in the layout tool, before simulation, to
a target less than 20% of the limits in its own tables. The kit's 20% is at
that bound, not below it.

Trace length rule applied as a delay
------------------------------------

Physical Table 24 limits the PCB trace length of CAC (command, address and
control: CA, CS, CKE) and data (DQ, DMI) signals to 3600 mil, routed on inner
layers. A routing structure carries its propagation velocity per layer, so
the limit becomes a maximum delay: 3600 mil (91.44 mm) over the fastest inner
layer's velocity of the single-ended structure, :py:func:`length_budget`.
Using the fastest layer keeps the conversion conservative across layers: at
the structure's stated velocities, a path at the limit has no more than
3600 mil of trace on any of the layers. On the 18-layer reference
substrate's stripline layers (effective permittivity 3.293 on each, from
the EM-890 datasheet; see
:py:mod:`jitxexamples.substrates.reference_18layer`) that is about 554 ps.
The rule names no limit for CK or DQS, which the skews to CA and DQ bound.

Package delay counts toward this limit, and that is this design's reading,
not UG863's text. Physical Table 24 names the rule "Maximum PCB trace
length"; the general guideline says "Include package delay in routing
constraints when determining signal trace lengths unless otherwise
specified". A pin model adds its package delay to every path on its pin, so
the delay held against this limit is package, vias and trace together, and
the trace gets less than 3600 mil: about 2340 to 2980 mil of stripline on
the length-limited pins with the synthetic package estimates. That is the
conservative reading. The other, the trace alone held to 3600 mil, needs
each path's limit raised by its own pin's package delay, and JITX does not
assign the FPGA pins until the board is routed.

Package delay
-------------

Timing Table 25 says to include the adaptive SoC's package delays in every
skew. :py:mod:`.part3_si_constraints` gives each FPGA pin of memory triplet M0 a
:py:class:`~jitx.si.TerminatingPinModel` at its midpoint package delay
(:py:mod:`.models`), so JITX adds it to every measured skew and delay. The
values the design reads are synthetic estimates, not AMD data; a real design
reads its own Vivado export. A routed pair's package skew is its two legs'
difference, which the synthetic file sets to zero.

Not applied
-----------

- DQ to DQ spread. UG863 gives no such rule, so ``spread_dq`` is ``None``.
- Insertion loss, as a UG863 rule. ``UG863_PARAMS`` sets no loss limit.
  The 1.0 dB limit :py:mod:`.part3_si_constraints` sets on every signal
  stands in for an SI team's budget and is not a UG863 value.
- Impedance, as a signal constraint. Physical Table 24 asks for 45 ohm
  +/-10% single ended and 82 ohm +/-10% differential. The design meets it by
  its choice of routing structures: the reference substrate's 46 ohm
  single-ended structure (SE_46, inside 40.5 to 49.5 ohm) and 85 ohm
  differential structure (DRS_85, inside 73.8 to 90.2 ohm). The substrate's
  45 ohm structure exists only on the outer layers, and these signals route
  on inner layers.
- Spacing in multiples of the height to the nearest ground plane. It is a
  layout rule, not a signal constraint: :py:mod:`.rules` applies it, with
  the ball-field pair structure.
- Other layout rules from Physical Table 24: vias per signal; CAC and clock
  on one internal layer; a byte's data and strobe on one internal layer;
  data on inner layers no deeper than 45 mil from the adaptive SoC; data and
  strobe on inner layers as close to the memory devices as possible. None
  is a signal constraint; a layout review checks them.
"""

from dataclasses import replace

from jitx.net import Port
from jitx.si import (
    Constrain,
    DifferentialRoutingStructure,
    RoutingStructure,
    SignalConstraint,
    Topology,
)
from jitx.toleranced import Toleranced

from jitxexamples.protocols.memory.lpddr4 import (
    LPDDR4,
    LPDDR4Constraint,
    LPDDR4ConstraintParams,
    LPDDR4SharedCKE,
)

UG863_PARAMS = LPDDR4ConstraintParams(
    skew_ck=Toleranced(0, 2.0e-12),
    skew_ck_cke=Toleranced(0, 20.0e-12),
    skew_ck_cs=Toleranced(0, 20.0e-12),
    skew_ck_ca=Toleranced(0, 100.0e-12),
    skew_ck_dqs=Toleranced(0, 150.0e-12),
    skew_dqs=Toleranced(0, 2.0e-12),
    skew_dqs_dq=Toleranced(0, 100.0e-12),
    spread_dq=None,
    loss=None,
)
"UG863 v1.12 timing Table 25 limits, as above."

KIT_LAYOUT_FRACTION = 0.2
"""The kit's layout target on four rules, as a fraction of UG863's limit: the
kit's choice (see "The kit's layout targets" above)."""


def _kit_window(window: Toleranced) -> Toleranced:
    """``window`` narrowed to :py:data:`KIT_LAYOUT_FRACTION` of its limit."""
    return Toleranced(0, KIT_LAYOUT_FRACTION * window.max_value)


KIT_PARAMS = replace(
    UG863_PARAMS,
    skew_dqs_dq=_kit_window(UG863_PARAMS.skew_dqs_dq),
    skew_dqs=_kit_window(UG863_PARAMS.skew_dqs),
    skew_ck=_kit_window(UG863_PARAMS.skew_ck),
    skew_ck_cke=_kit_window(UG863_PARAMS.skew_ck_cke),
    skew_ck_cs=_kit_window(UG863_PARAMS.skew_ck_cs),
)
"""The set Part 3 applies: DQ and DM to DQS_T +/-20 ps, each DQS and CK pair
+/-0.4 ps, CKE and CS to CK_T +/-4 ps, each :py:data:`KIT_LAYOUT_FRACTION`
of UG863's; CA to CK_T and DQS to CK_T at UG863's limits."""

MAX_TRACE_LENGTH = 3600 * 0.0254
"UG863 v1.12 physical Table 24: 3600 mil for CAC and data signals, in mm."


def length_budget(structure: RoutingStructure, layers: tuple[int, ...]) -> float:
    """The delay, in seconds, of :py:data:`MAX_TRACE_LENGTH` on the fastest of
    ``layers`` of ``structure``: the conservative conversion, since at the
    structure's velocities a trace meeting this delay is no longer than the
    limit on any of the layers.

    Velocity is in mm/s, as :py:func:`jitxlib.physics.phase_velocity` gives
    it.
    """
    fastest = max(structure.layers[layer].velocity for layer in layers)
    return MAX_TRACE_LENGTH / fastest


class VersalLPDDR4Constraint(SignalConstraint[LPDDR4]):
    """UG863's LPDDR4/4x skew limits and trace length budget on one link.

    Args:
        diff_structure: Differential routing structure for CK and DQS.
        se_structure: Single-ended routing structure for CAC and data.
        params: Skew limits; :py:data:`UG863_PARAMS` by default.
        max_delay: Delay limit in seconds for every CAC and data signal, or
            ``None`` for none. :py:func:`length_budget` derives UG863's.
    """

    def __init__(
        self,
        diff_structure: DifferentialRoutingStructure,
        se_structure: RoutingStructure,
        params: LPDDR4ConstraintParams = UG863_PARAMS,
        max_delay: float | None = None,
    ) -> None:
        super().__init__()
        self.skews = LPDDR4Constraint(diff_structure, se_structure, params)
        self.max_delay = max_delay

    def constrain(self, src: LPDDR4 | LPDDR4SharedCKE, dst: LPDDR4) -> None:
        """Apply the skews, then the delay limit, between two netted bundles."""
        self.skews.constrain(src, dst)
        if self.max_delay is None:
            return
        for s_ch, d_ch in zip(src.ch, dst.ch, strict=True):
            pairs: list[tuple[Port, Port]] = []
            s_cke = s_ch.cke
            s_ckes = [s_cke] * len(d_ch.cke) if isinstance(s_cke, Port) else s_cke
            pairs += zip(s_ckes, d_ch.cke, strict=True)
            pairs += zip(s_ch.cs, d_ch.cs, strict=True)
            pairs += zip(s_ch.ca, d_ch.ca, strict=True)
            for s_lane, d_lane in zip(s_ch.d, d_ch.d, strict=True):
                pairs.append((s_lane.dmi, d_lane.dmi))
                pairs += zip(s_lane.dq, d_lane.dq, strict=True)
            for s, d in pairs:
                self.add(Constrain(Topology(s, d)).timing(self.max_delay))

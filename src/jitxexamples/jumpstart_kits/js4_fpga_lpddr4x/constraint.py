"""LPDDR4X timing constraints for the VP1002 to Micron link, from AMD UG863.

Source: AMD, *Versal Adaptive SoC PCB Design User Guide*, UG863 v1.12
(2026-06-16), "Timing Constraint Rules for LPDDR4/4x Signals", Table 1,
"Skew Constraint Rules for LPDDR4/4x Signals",
https://docs.amd.com/r/en-US/ug863-versal-pcb-design/Timing-Constraint-Rules-for-LPDDR4/4x-Signals.

======================================  ================  ==========================
UG863 Table 1 row                       Limit             ``LPDDR4ConstraintParams``
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

CKE: the controller's one CKE per channel is netted to both of the
memory's CKE balls (an inference from AMD's boards, see
:py:mod:`.pinout`), and
:py:meth:`~jitxexamples.protocols.memory.lpddr4.LPDDR4Constraint.constrain`
applies ``skew_ck_cke`` from that pin to each ball. Until the three-pad CKE
net is routed, its two paths report ``No path for signal constraint``;
routed in a chain from the FPGA pin to CKE0 and on to CKE1, both measure
(:py:mod:`.proof`).

What is not applied
-------------------

- Package delay. Table 1 says to include the adaptive SoC's package delays in
  every skew. The VP1002 model has no
  :py:class:`~jitx.si.TerminatingPinModel`, so the measured skews are board
  only.
- DQ to DQ spread. UG863 gives no such rule, so ``spread_dq`` is ``None``.
- Insertion loss. UG863 gives no limit.
- Impedance, trace length, spacing and via counts. They are UG863 "Physical
  Design Rules for LPDDR4/4x Signals", Table 1: 45 ohm +/-10% single ended,
  82 ohm +/-10% differential, 3600 mil maximum on inner layers. No JS1 HDI
  routing structure is in either impedance window (SE_40 is 40 ohm, SE_50 is
  50 ohm, DRS_100 is 100 ohm); the kit uses SE_50 and DRS_100 until the
  stackup gains matching structures.
"""

from jitx.toleranced import Toleranced

from jitxexamples.protocols.memory.lpddr4 import LPDDR4ConstraintParams

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
"UG863 v1.12 Table 1 limits, as above."

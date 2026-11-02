"""
LPDDR4
======

Port bundles and a signal-integrity constraint for a point-to-point LPDDR4
link between a controller and one memory device.

Source and scope
----------------

The defaults in :py:class:`LPDDR4ConstraintParams` are Table 2, "LPDDR4
without ECC Skew Constraints", in AMD UG583, *UltraScale Architecture PCB
Design User Guide*, section "LPDDR4 without ECC Length and Skew Constraints",
https://docs.amd.com/r/en-US/ug583-ultrascale-pcb-design/LPDDR4-without-ECC-Length-and-Skew-Constraints.
That table is written for the Zynq UltraScale+ MPSoC processing system (PS)
driving one LPDDR4 device without ECC; for any other controller, check its
own layout guide.

- CK_t to CK_c: 2 ps (applied as +/-2 ps)
- DQS_t to DQS_c: 2 ps (applied as +/-2 ps)
- Address/command/control to CK: +/-8 ps (applied to CKE, CS and CA0 to
  CA5)
- DQ and DM to DQS: +/-5 ps (applied to DQ and DMI)
- CK to DQS: -500 ps to +2500 ps, as CK delay minus DQS delay. Table 2's
  note sends skew to items 3 to 8 of UG583's General Memory Routing
  Guidelines, whose CK-to-DQS example subtracts the DQS delay from the
  clock delay. On jitx 4.6, ``ConstrainReferenceDifference(guide, target)``
  measures guide delay minus target delay (checked on a code-routed pair),
  so CK is the guide.
- DQ and DM, slowest to fastest: 5 ps. The constraint holds each DQ within
  +/-2.5 ps of DMI, which keeps any two of them within 5 ps; it is stricter
  than the rule for DMI against a DQ, since UG583 allows DMI anywhere inside
  the 5 ps spread.

Table 2's note also says: "FPGA package flight times must be included in
both total length constraints and skew constraints ... Memory device
package flight times do not need to be factored in." The design-issue
report counts a package's delay only where its pins carry a
:py:class:`~jitx.si.TerminatingPinModel`, so give the controller's pins one
from its package delay data (UG583 asks for the midrange where a minimum
and maximum are given), and leave the memory's pins without one. The
controller in :py:mod:`.lpddr4_example` is fictional and has none.

UG583 also sets maximum lengths (its Table 1), which this module does not
apply, and excludes reset_n from the skew rules. It gives no insertion-loss
limit and no impedance target, so the module sets neither by default: pass
``loss`` in the parameters to add a loss limit, and pass the routing
structures from the board's substrate.

Use
---

Net the controller's bundle to the memory's bundle with an ordinary net and
apply the constraint to the same two bundles::

    self.link = self.controller.lpddr4 + self.memory.lpddr4
    self.si = LPDDR4Constraint(diff_structure=..., se_structure=...)
    self.si.constrain(self.controller.lpddr4, self.memory.lpddr4)

A controller that drives one CKE per channel for both ranks of an x32
dual-rank memory (the dual-rank VMK180 and VPK120 boards map their LPDDR4
interfaces this way) offers :py:class:`LPDDR4SharedCKE` instead. Net its one
CKE to both of the memory channel's CKE balls and pass it as the controller side:
:py:meth:`LPDDR4Constraint.constrain` holds each of those balls against CK.
Set ``spread_dq`` to ``None`` for a layout guide with no DQ spread rule.

The issue report measures a constraint only once the path between its two ends
is routed. :py:mod:`.lpddr4_example` is not routed.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from jitx.net import DiffPair, Port
from jitx.si import (
    Constrain,
    ConstrainReferenceDifference,
    DifferentialRoutingStructure,
    ConstrainDiffPair,
    RoutingStructure,
    SignalConstraint,
    Topology,
)
from jitx.toleranced import Toleranced


class LPDDR4Width(Enum):
    """LPDDR4 interface width: the number of x16 channels times 16."""

    x16 = 16
    "One x16 channel"
    x32 = 32
    "Two x16 channels"
    x64 = 64
    "Four x16 channels"


def num_x16_channels(width: LPDDR4Width) -> int:
    """Return the number of x16 channels in an interface of this width."""
    return width.value // 16


class LPDDR4Rank(Enum):
    """LPDDR4 rank count: the number of CKE and CS signals per channel."""

    Rank1 = 1
    "Single rank"
    Rank2 = 2
    "Dual rank"


class LPDDR4Lane(Port):
    """One LPDDR4 byte lane: eight DQ, one DQS pair and one DMI."""

    dq = [Port() for _ in range(8)]
    "Data bits"

    dqs = DiffPair()
    "Data strobe (``p`` is DQS_t, ``n`` is DQS_c)"

    dmi = Port()
    "Data mask and inversion"


class LPDDR4Channel(Port):
    """One LPDDR4 x16 channel: two byte lanes, the clock, and command/address.

    Args:
        rank: Rank count, which sets the number of CKE and CS signals.
    """

    d: Sequence[LPDDR4Lane]
    "Byte lanes 0 and 1"

    ck = DiffPair()
    "Clock (``p`` is CK_t, ``n`` is CK_c)"

    cke: Sequence[Port]
    "Clock enable, one per rank"

    cs: Sequence[Port]
    "Chip select, one per rank"

    ca = [Port() for _ in range(6)]
    "Command/address bits CA0 to CA5"

    def __init__(self, rank: LPDDR4Rank) -> None:
        self.d = (LPDDR4Lane(), LPDDR4Lane())
        self.cke = tuple(Port() for _ in range(rank.value))
        self.cs = tuple(Port() for _ in range(rank.value))


class LPDDR4(Port):
    """LPDDR4 interface: one or more x16 channels.

    Args:
        width: Interface width.
        rank: Rank count.
    """

    ch: Sequence[LPDDR4Channel]
    "x16 channels"

    def __init__(self, width: LPDDR4Width, rank: LPDDR4Rank) -> None:
        self.ch = tuple(LPDDR4Channel(rank) for _ in range(num_x16_channels(width)))


class LPDDR4SharedCKEChannel(Port):
    """One x16 channel of a dual-rank controller that drives one CKE for both
    ranks."""

    d = (LPDDR4Lane(), LPDDR4Lane())
    "Byte lanes 0 and 1"

    ck = DiffPair()
    "Clock (``p`` is CK_t, ``n`` is CK_c)"

    cke = Port()
    "Clock enable, shared by both ranks"

    cs = (Port(), Port())
    "Chip select, one per rank"

    ca = [Port() for _ in range(6)]
    "Command/address bits CA0 to CA5"


class LPDDR4SharedCKE(Port):
    """An x32 dual-rank controller interface with one CKE per channel.

    The controller side of a link to an x32 dual-rank :py:class:`LPDDR4`
    memory. A pin assignment option maps one controller pin to one port, so a
    shared CKE needs its own port rather than two ports of :py:class:`LPDDR4`.
    """

    ch = (LPDDR4SharedCKEChannel(), LPDDR4SharedCKEChannel())
    "Channels A and B"


def signal_ports(bus: LPDDR4) -> list[Port]:
    """Return every single-pin port of ``bus`` in a fixed order.

    Per channel: CK p and n, the CKE signals, the CS signals, CA0 to CA5, then
    per byte lane DQ0 to DQ7, DQS p and n, and DMI. Two bundles of the same
    width and rank give lists that line up signal for signal. The example
    controller assigns its balls in this order.
    """
    ports: list[Port] = []
    for ch in bus.ch:
        ports += [ch.ck.p, ch.ck.n, *ch.cke, *ch.cs, *ch.ca]
        for lane in ch.d:
            ports += [*lane.dq, lane.dqs.p, lane.dqs.n, lane.dmi]
    return ports


@dataclass(frozen=True)
class LPDDR4ConstraintParams:
    """LPDDR4 timing limits. Defaults are AMD UG583 Table 2.

    To change one value, use :py:func:`dataclasses.replace` on a default
    instance.
    """

    skew_ck: Toleranced = Toleranced(0, 2.0e-12)
    "CK intra-pair skew"

    skew_ck_cke: Toleranced = Toleranced(0, 8.0e-12)
    "CKE to CK skew"

    skew_ck_cs: Toleranced = Toleranced(0, 8.0e-12)
    "CS to CK skew"

    skew_ck_ca: Toleranced = Toleranced(0, 8.0e-12)
    "CA to CK skew"

    skew_ck_dqs: Toleranced = Toleranced.min_max(-500.0e-12, 2500.0e-12)
    "CK.p delay minus DQS.p delay"

    skew_dqs: Toleranced = Toleranced(0, 2.0e-12)
    "DQS intra-pair skew"

    skew_dqs_dq: Toleranced = Toleranced(0, 5.0e-12)
    "DQ and DMI to DQS skew"

    spread_dq: float | None = 5.0e-12
    """Largest delay difference, slowest to fastest, among the DQ and DMI of a
    byte lane, in seconds, or ``None`` for no spread rule. Applied as +/- half
    of it around DMI."""

    loss: float | None = None
    "Maximum insertion loss in dB for every signal, or ``None`` for no limit"

    def __post_init__(self) -> None:
        if self.spread_dq is not None and self.spread_dq <= 0:
            raise ValueError(f"spread_dq must be positive, got {self.spread_dq}")


class LPDDR4Constraint(SignalConstraint[LPDDR4]):
    """Signal-integrity constraint for an LPDDR4 link.

    For each channel, :py:meth:`constrain` applies:

    - CK: intra-pair skew, on the differential structure.
    - CKE, CS and CA: skew against CK.p, on the single-ended structure. A
      :py:class:`LPDDR4SharedCKE` controller's one CKE is held against CK.p
      to each of the memory channel's CKE balls.
    - Per byte lane, DQS: intra-pair skew, and the CK.p minus DQS.p window.
    - Per byte lane, DQ and DMI: skew against DQS.p, on the single-ended
      structure.
    - Per byte lane, unless ``spread_dq`` is ``None``, DQ spread: each DQ
      within half of ``spread_dq`` of DMI, so any two of them differ by at
      most ``spread_dq``.
      :py:class:`~jitx.si.ConstrainReferenceDifference` compares each signal
      with one guide, which is why a pairwise limit is expressed this way.
    - With ``params.loss`` set, that insertion-loss limit on every signal.

    The guides are single pins (CK.p, DQS.p) because
    :py:class:`~jitx.si.ConstrainReferenceDifference` accepts only a
    single-pin guide. UG583 measures against a differential pair's
    mid-point, so the p leg can sit off that reference by up to half the
    pair's intra-pair skew.

    Args:
        diff_structure: Differential routing structure for CK and DQS.
        se_structure: Single-ended routing structure for CKE, CS, CA, DQ and
            DMI.
        params: Timing limits. Defaults to :py:class:`LPDDR4ConstraintParams`.
    """

    def __init__(
        self,
        diff_structure: DifferentialRoutingStructure,
        se_structure: RoutingStructure,
        params: LPDDR4ConstraintParams | None = None,
    ) -> None:
        super().__init__()
        self.params = params or LPDDR4ConstraintParams()
        self.diff_structure = diff_structure
        self.se_structure = se_structure

    def _diff_pair(self, src: DiffPair, dst: DiffPair, skew: Toleranced) -> None:
        constrain = ConstrainDiffPair(Topology(src, dst)).timing_difference(skew)
        constrain.structure(self.diff_structure)
        if self.params.loss is not None:
            constrain.insertion_loss(self.params.loss)
        self.add(constrain)

    def _single_ended(
        self, guide: Topology, src: Port, dst: Port, skew: Toleranced
    ) -> Topology:
        topo = Topology(src, dst)
        self.add(ConstrainReferenceDifference(guide, topo).timing_difference(skew))
        constrain = Constrain(topo)
        constrain.structure(self.se_structure)
        if self.params.loss is not None:
            constrain.insertion_loss(self.params.loss)
        self.add(constrain)
        return topo

    def constrain(self, src: LPDDR4 | LPDDR4SharedCKE, dst: LPDDR4) -> None:
        """Apply the LPDDR4 constraints between two netted bundles.

        Args:
            src: Controller-side bundle: an :py:class:`LPDDR4` of the same
                width and rank as ``dst``, or an :py:class:`LPDDR4SharedCKE`
                when ``dst`` is x32 dual rank.
            dst: Memory-side bundle.

        Raises:
            TypeError: If ``dst`` is not an :py:class:`LPDDR4`, such as the
                controller and memory sides passed in the wrong order.
            ValueError: If the bundles differ in width or rank.
        """
        if not isinstance(dst, LPDDR4):
            raise TypeError(
                f"dst must be the memory-side LPDDR4 bundle, got {type(dst).__name__}:"
                " pass the controller side first"
            )
        if len(src.ch) != len(dst.ch):
            raise ValueError(
                f"LPDDR4 width mismatch: {len(src.ch)} channels against {len(dst.ch)}"
            )
        p = self.params
        half_spread = None if p.spread_dq is None else Toleranced(0, p.spread_dq / 2)
        for s_ch, d_ch in zip(src.ch, dst.ch, strict=True):
            if len(s_ch.cs) != len(d_ch.cs):
                raise ValueError(
                    f"LPDDR4 rank mismatch: {len(s_ch.cs)} against {len(d_ch.cs)}"
                )
            self._diff_pair(s_ch.ck, d_ch.ck, p.skew_ck)
            guide_ck = Topology(s_ch.ck.p, d_ch.ck.p)
            s_cke = s_ch.cke
            s_ckes = [s_cke] * len(d_ch.cke) if isinstance(s_cke, Port) else s_cke
            for s, d in zip(s_ckes, d_ch.cke, strict=True):
                self._single_ended(guide_ck, s, d, p.skew_ck_cke)
            for s, d in zip(s_ch.cs, d_ch.cs, strict=True):
                self._single_ended(guide_ck, s, d, p.skew_ck_cs)
            for s, d in zip(s_ch.ca, d_ch.ca, strict=True):
                self._single_ended(guide_ck, s, d, p.skew_ck_ca)

            for s_lane, d_lane in zip(s_ch.d, d_ch.d, strict=True):
                self._diff_pair(s_lane.dqs, d_lane.dqs, p.skew_dqs)
                guide_dqs = Topology(s_lane.dqs.p, d_lane.dqs.p)
                self.add(
                    ConstrainReferenceDifference(guide_ck, guide_dqs).timing_difference(
                        p.skew_ck_dqs
                    )
                )
                dmi = self._single_ended(
                    guide_dqs, s_lane.dmi, d_lane.dmi, p.skew_dqs_dq
                )
                for s, d in zip(s_lane.dq, d_lane.dq, strict=True):
                    dq = self._single_ended(guide_dqs, s, d, p.skew_dqs_dq)
                    if half_spread is None:
                        continue
                    self.add(
                        ConstrainReferenceDifference(dmi, dq).timing_difference(
                            half_spread
                        )
                    )

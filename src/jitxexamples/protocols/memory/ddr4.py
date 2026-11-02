"""
DDR4
====

Port bundles and signal-integrity constraints for a point-to-point DDR4 link
between a controller and one memory device.

Source and scope
----------------

The defaults are Table 116, "Skew Matching Guidelines for DDR4 Discrete
Topologies", in Altera, *External Memory Interfaces Agilex 7 F-Series and
I-Series FPGA IP User Guide* (683216, version 23.2), section 6.5.6.4, "Skew
Matching Guidelines for DDR4 Discrete Configurations",
https://docs.altera.com/r/docs/683216/23.2/external-memory-interfaces-agilextm-7-f-series-and-i-series-fpga-ip-user-guide/skew-matching-guidelines-for-ddr4-discrete-configurations.
That section covers single-rank x8 and single-rank x16 discrete
(device-down) topologies. The module accepts other widths and ranks, but
the table does not cover them, and it does not support several memories
on one bus (see Fly-by below).

- CK to CK#: < 1 ps (applied as +/-1 ps)
- DQS to DQS#: < 1 ps (applied as +/-1 ps)
- DQ to DQS within a byte: -3.5 ps < DQ - DQS < 3.5 ps (applied to DQ and
  DM_n)
- CMD/ADDR/CTRL to clock: -20 ps < CLK - CMD/ADDR/CTRL < 20 ps
- CMD/ADDR/CTRL among themselves within each channel: < 20 ps. The
  constraint holds each of them within +/-10 ps of CKE[0], so any two
  differ by at most 20 ps. That is stricter than the table, which allows
  every other signal to sit together 15 ps from CKE[0]; the constraint fails
  that layout.
- DQS to CLK: -85 ps < CLK - DQS < 935 ps. On jitx 4.6,
  ``ConstrainReferenceDifference(guide, target)`` measures guide delay minus
  target delay (checked on a code-routed pair), so CK is the guide and the
  window is used as written.

The constraint applies the CMD/ADDR/CTRL rules to the address bits (A0 to
A16 in this bundle; A14 to A16 double as WE_n, CAS_n and RAS_n), BA, BG,
ACT_n, CKE, CS_n, ODT and PAR. The section says ALERT_n needs no skew
matching. It does not name RESET_n; this module gives RESET_n no skew limit.
Both get the routing structure and the optional loss limit.

The section also asks for skew matching in time rather than length:
"Include both package per-pin skew and PCB delay when performing skew
matching." The design-issue report counts a package's delay only where its
pins carry a :py:class:`~jitx.si.TerminatingPinModel`, so give the
controller's pins one from its package delay data. The controller in
:py:mod:`.ddr4_example` is fictional and has none, so its numbers would be
PCB delay only. The table gives no rule between CK
pairs, no insertion-loss limit and no impedance target, so the module sets
none of them: pass ``loss`` in the parameter classes to add a loss limit,
and pass the routing structures from the board's substrate.

Use
---

Net the controller's bundle to the memory's bundle with an ordinary net and
apply the constraint to the same two bundles::

    self.link = self.controller.ddr4 + self.memory.ddr4
    self.si = DDR4Constraint(
        ck_structure=..., dqs_structure=..., dq_structure=..., acc_structure=...
    )
    self.si.constrain(self.controller.ddr4, self.memory.ddr4)

The issue report measures a constraint only once the path between its two ends
is routed.

Fly-by
------

With several memories on one address/command bus, the bus is a daisy chain:
controller, first memory, second memory. This module does not support that:
its constraint covers one controller-to-memory link, and the cited table
covers discrete single-device topologies only. In a fly-by design, the chain
order is part of the design, and ``>>`` (``TopologyNet``) declares it.
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


class DDR4Width(Enum):
    """DDR4 data width: the number of DQ signals."""

    x4 = 4
    "4 bits, one byte lane"
    x8 = 8
    "8 bits, one byte lane"
    x16 = 16
    "16 bits, two byte lanes"
    x32 = 32
    "32 bits, four byte lanes"
    x64 = 64
    "64 bits, eight byte lanes"
    x72 = 72
    "72 bits (64 plus ECC), nine byte lanes"


def num_byte_lanes(width: DDR4Width) -> int:
    """Return the number of byte lanes (DQS pairs) for a data width."""
    return max(1, width.value // 8)


class DDR4Rank(Enum):
    """DDR4 rank count: the number of CS_n, CKE and ODT signals."""

    SingleRank = 1
    "One rank"
    DualRank = 2
    "Two ranks"
    QuadRank = 4
    "Four ranks"


class DDR4DataChannel(Port):
    """DDR4 data signals: DQ, one DQS pair and one DM_n per byte lane.

    Args:
        width: Data width.
    """

    DQ: Sequence[Port]
    "Data bits"

    DQS: Sequence[DiffPair]
    "Data strobes, one per byte lane (``p`` is DQS_t, ``n`` is DQS_c)"

    DM_n: Sequence[Port]
    "Data masks, one per byte lane"

    def __init__(self, width: DDR4Width) -> None:
        lanes = num_byte_lanes(width)
        self.DQ = tuple(Port() for _ in range(width.value))
        self.DQS = tuple(DiffPair() for _ in range(lanes))
        self.DM_n = tuple(Port() for _ in range(lanes))


class DDR4AccChannel(Port):
    """DDR4 address, command, control and clock signals.

    Args:
        rank: Rank count, which sets the number of CKE, CS_n and ODT signals.
        ck_count: Number of CK pairs.
        bg_count: Number of bank-group signals (one on x16 parts).
        ba_count: Number of bank-address signals.
    """

    CK: Sequence[DiffPair]
    "Clock pairs (``p`` is CK_t, ``n`` is CK_c)"

    CKE: Sequence[Port]
    "Clock enable, one per rank"

    A: Sequence[Port]
    "Address A0 to A16 (A14 to A16 double as WE_n, CAS_n, RAS_n)"

    ACT_n = Port()
    "Activate command"

    BG: Sequence[Port]
    "Bank group"

    BA: Sequence[Port]
    "Bank address"

    CS_n: Sequence[Port]
    "Chip select, one per rank"

    RESET_n = Port()
    "Reset"

    ODT: Sequence[Port]
    "On-die termination, one per rank"

    PAR = Port()
    "Command and address parity"

    ALERT_n = Port()
    "Alert"

    def __init__(
        self,
        rank: DDR4Rank,
        ck_count: int = 1,
        bg_count: int = 2,
        ba_count: int = 2,
    ) -> None:
        self.CK = tuple(DiffPair() for _ in range(ck_count))
        self.CKE = tuple(Port() for _ in range(rank.value))
        self.A = tuple(Port() for _ in range(17))
        self.BG = tuple(Port() for _ in range(bg_count))
        self.BA = tuple(Port() for _ in range(ba_count))
        self.CS_n = tuple(Port() for _ in range(rank.value))
        self.ODT = tuple(Port() for _ in range(rank.value))


class DDR4(Port):
    """DDR4 interface: data channel plus address/command/control channel.

    Args:
        width: Data width.
        rank: Rank count.
        ck_count: Number of CK pairs.
        bg_count: Number of bank-group signals.
        ba_count: Number of bank-address signals.
    """

    data: DDR4DataChannel
    "Data channel"

    acc: DDR4AccChannel
    "Address, command, control and clock channel"

    def __init__(
        self,
        width: DDR4Width,
        rank: DDR4Rank = DDR4Rank.SingleRank,
        ck_count: int = 1,
        bg_count: int = 2,
        ba_count: int = 2,
    ) -> None:
        self.data = DDR4DataChannel(width)
        self.acc = DDR4AccChannel(rank, ck_count, bg_count, ba_count)


def signal_ports(bus: DDR4) -> list[Port]:
    """Return every single-pin port of ``bus`` in a fixed order.

    Data first (DQ, DQS p and n per lane, DM_n), then CK p and n per pair,
    CKE, A, ACT_n, BG, BA, CS_n, RESET_n, ODT, PAR and ALERT_n. Two bundles
    built with the same arguments give lists that line up signal for signal.
    """
    d, a = bus.data, bus.acc
    ports: list[Port] = [*d.DQ]
    for dqs in d.DQS:
        ports += [dqs.p, dqs.n]
    ports += [*d.DM_n]
    for ck in a.CK:
        ports += [ck.p, ck.n]
    ports += [*a.CKE, *a.A, a.ACT_n, *a.BG, *a.BA, *a.CS_n, a.RESET_n]
    ports += [*a.ODT, a.PAR, a.ALERT_n]
    return ports


@dataclass(frozen=True)
class DDR4DataConstraintParams:
    """DDR4 data-channel limits. Defaults are the cited rules in this module.

    Attributes:
        skew_dqs: DQS intra-pair skew.
        skew_dq_dqs: DQ and DM_n to DQS.P skew within a byte lane.
        loss: Maximum insertion loss in dB for DQ, DM_n and DQS, or ``None``
            for no loss limit.
    """

    skew_dqs: Toleranced = Toleranced(0, 1.0e-12)
    skew_dq_dqs: Toleranced = Toleranced(0, 3.5e-12)
    loss: float | None = None


@dataclass(frozen=True)
class DDR4AccConstraintParams:
    """DDR4 address/command/control limits. Defaults are the cited rules.

    Attributes:
        skew_ck: CK intra-pair skew.
        skew_acc_ck: CK.P delay minus address, command and control delay.
        spread_acc: Largest delay difference among the address, command and
            control signals of the channel, in seconds. Applied as +/- half
            of it around CKE[0].
        loss: Maximum insertion loss in dB for CK and the address, command
            and control signals, or ``None`` for no loss limit.
    """

    skew_ck: Toleranced = Toleranced(0, 1.0e-12)
    skew_acc_ck: Toleranced = Toleranced(0, 20.0e-12)
    spread_acc: float = 20.0e-12
    loss: float | None = None

    def __post_init__(self) -> None:
        if self.spread_acc <= 0:
            raise ValueError(f"spread_acc must be positive, got {self.spread_acc}")


@dataclass(frozen=True)
class DDR4DataAccConstraintParams:
    """DDR4 data-to-clock limit. The default is the cited rule.

    Attributes:
        skew_ck_dqs: CK.P delay minus DQS.P delay.
    """

    skew_ck_dqs: Toleranced = Toleranced.min_max(-85.0e-12, 935.0e-12)


def _single_ended(
    loss: float | None, structure: RoutingStructure, topo: Topology
) -> Constrain:
    constrain = Constrain(topo)
    constrain.structure(structure)
    if loss is not None:
        constrain.insertion_loss(loss)
    return constrain


def _diff_pair(
    loss: float | None,
    skew: Toleranced,
    structure: DifferentialRoutingStructure,
    src: DiffPair,
    dst: DiffPair,
) -> ConstrainDiffPair:
    constrain = ConstrainDiffPair(Topology(src, dst)).timing_difference(skew)
    constrain.structure(structure)
    if loss is not None:
        constrain.insertion_loss(loss)
    return constrain


class DDR4DataConstraint(SignalConstraint[DDR4DataChannel]):
    """Constraint for the DDR4 data channel.

    Per byte lane: DQS intra-pair skew, and DQ and DM_n skew against DQS.P.
    Byte lane ``i`` holds DQ ``8 * i`` to ``8 * i + 7``.

    Args:
        dqs_structure: Differential routing structure for DQS.
        dq_structure: Single-ended routing structure for DQ and DM_n.
        params: Limits. Defaults to :py:class:`DDR4DataConstraintParams`.
    """

    def __init__(
        self,
        dqs_structure: DifferentialRoutingStructure,
        dq_structure: RoutingStructure,
        params: DDR4DataConstraintParams | None = None,
    ) -> None:
        super().__init__()
        self.params = params or DDR4DataConstraintParams()
        self.dqs_structure = dqs_structure
        self.dq_structure = dq_structure

    def constrain(self, src: DDR4DataChannel, dst: DDR4DataChannel) -> None:
        """Apply the data-channel constraints between two netted channels.

        Raises:
            ValueError: If the channels differ in width.
        """
        if len(src.DQ) != len(dst.DQ):
            raise ValueError(
                f"DDR4 width mismatch: {len(src.DQ)} DQ against {len(dst.DQ)}"
            )
        p = self.params
        lanes = zip(src.DQS, dst.DQS, src.DM_n, dst.DM_n, strict=True)
        for i, (s_dqs, d_dqs, s_dm, d_dm) in enumerate(lanes):
            self.add(_diff_pair(p.loss, p.skew_dqs, self.dqs_structure, s_dqs, d_dqs))
            guide = Topology(s_dqs.p, d_dqs.p)
            bits = range(8 * i, min(8 * i + 8, len(src.DQ)))
            topos = [Topology(src.DQ[j], dst.DQ[j]) for j in bits]
            topos.append(Topology(s_dm, d_dm))
            self.add(
                ConstrainReferenceDifference(guide, topos).timing_difference(
                    p.skew_dq_dqs
                )
            )
            for topo in topos:
                self.add(_single_ended(p.loss, self.dq_structure, topo))


class DDR4AccConstraint(SignalConstraint[DDR4AccChannel]):
    """Constraint for the DDR4 address, command, control and clock channel.

    Applies CK intra-pair skew to every CK pair, then holds CKE, A, ACT_n,
    BG, BA, CS_n, ODT and PAR within ``skew_acc_ck`` of CK[0].P and within
    half of ``spread_acc`` of CKE[0]. RESET_n and ALERT_n get the routing
    structure and loss limit only. There is no limit between CK pairs, since
    the cited table gives none.

    Args:
        ck_structure: Differential routing structure for CK.
        acc_structure: Single-ended routing structure for the other signals.
        params: Limits. Defaults to :py:class:`DDR4AccConstraintParams`.
    """

    def __init__(
        self,
        ck_structure: DifferentialRoutingStructure,
        acc_structure: RoutingStructure,
        params: DDR4AccConstraintParams | None = None,
    ) -> None:
        super().__init__()
        self.params = params or DDR4AccConstraintParams()
        self.ck_structure = ck_structure
        self.acc_structure = acc_structure

    def constrain(self, src: DDR4AccChannel, dst: DDR4AccChannel) -> None:
        """Apply the address/command/control constraints between two channels."""
        p = self.params
        guide_ck = Topology(src.CK[0].p, dst.CK[0].p)
        for s_ck, d_ck in zip(src.CK, dst.CK, strict=True):
            self.add(_diff_pair(p.loss, p.skew_ck, self.ck_structure, s_ck, d_ck))

        guide_cke = Topology(src.CKE[0], dst.CKE[0])
        self.add(_single_ended(p.loss, self.acc_structure, guide_cke))
        timed: list[tuple[Port, Port]] = [
            *zip(src.CKE[1:], dst.CKE[1:], strict=True),
            *zip(src.A, dst.A, strict=True),
            (src.ACT_n, dst.ACT_n),
            *zip(src.BG, dst.BG, strict=True),
            *zip(src.BA, dst.BA, strict=True),
            *zip(src.CS_n, dst.CS_n, strict=True),
            *zip(src.ODT, dst.ODT, strict=True),
            (src.PAR, dst.PAR),
        ]
        others: list[Topology] = []
        for s, d in timed:
            topo = Topology(s, d)
            self.add(_single_ended(p.loss, self.acc_structure, topo))
            others.append(topo)
        for s, d in ((src.RESET_n, dst.RESET_n), (src.ALERT_n, dst.ALERT_n)):
            self.add(_single_ended(p.loss, self.acc_structure, Topology(s, d)))
        self.add(
            ConstrainReferenceDifference(
                guide_ck, [guide_cke, *others]
            ).timing_difference(p.skew_acc_ck),
            ConstrainReferenceDifference(guide_cke, others).timing_difference(
                Toleranced(0, p.spread_acc / 2)
            ),
        )


class DDR4DataAccConstraint(SignalConstraint["DDR4"]):
    """Constraint between the two channels: each DQS.P against CK[0].P.

    Args:
        params: Limit. Defaults to :py:class:`DDR4DataAccConstraintParams`.
    """

    def __init__(self, params: DDR4DataAccConstraintParams | None = None) -> None:
        super().__init__()
        self.params = params or DDR4DataAccConstraintParams()

    def constrain(self, src: DDR4, dst: DDR4) -> None:
        """Apply the DQS-to-CK window between two netted bundles."""
        guide_ck = Topology(src.acc.CK[0].p, dst.acc.CK[0].p)
        dqs = [
            Topology(s.p, d.p) for s, d in zip(src.data.DQS, dst.data.DQS, strict=True)
        ]
        self.add(
            ConstrainReferenceDifference(guide_ck, dqs).timing_difference(
                self.params.skew_ck_dqs
            )
        )


class DDR4Constraint(SignalConstraint["DDR4"]):
    """Complete DDR4 constraint: data, address/command/control, and the
    DQS-to-CK window between them.

    Args:
        ck_structure: Differential routing structure for CK.
        dqs_structure: Differential routing structure for DQS.
        dq_structure: Single-ended routing structure for DQ and DM_n.
        acc_structure: Single-ended routing structure for address, command
            and control.
        data_params: Data-channel limits.
        acc_params: Address/command/control limits.
        data_acc_params: DQS-to-CK window.
    """

    def __init__(
        self,
        ck_structure: DifferentialRoutingStructure,
        dqs_structure: DifferentialRoutingStructure,
        dq_structure: RoutingStructure,
        acc_structure: RoutingStructure,
        data_params: DDR4DataConstraintParams | None = None,
        acc_params: DDR4AccConstraintParams | None = None,
        data_acc_params: DDR4DataAccConstraintParams | None = None,
    ) -> None:
        super().__init__()
        self.data_constraint = DDR4DataConstraint(
            dqs_structure, dq_structure, data_params
        )
        self.acc_constraint = DDR4AccConstraint(ck_structure, acc_structure, acc_params)
        self.data_acc_constraint = DDR4DataAccConstraint(data_acc_params)

    def constrain(self, src: DDR4, dst: DDR4) -> None:
        """Apply every DDR4 constraint between two netted bundles.

        Args:
            src: Controller-side bundle.
            dst: Memory-side bundle, built with the same arguments.
        """
        self.data_constraint.constrain(src.data, dst.data)
        self.acc_constraint.constrain(src.acc, dst.acc)
        self.data_acc_constraint.constrain(src, dst)

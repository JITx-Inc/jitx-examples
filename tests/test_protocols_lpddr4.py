"""The LPDDR4 example applies every UG583 skew limit between controller and memory."""

from typing import cast

from jitx.net import Port
from jitx.sample import SampleSubstrate
from jitx.si import (
    BaseConstrain,
    Constrain,
    ConstrainDiffPair,
    ConstrainReferenceDifference,
    InsertionLossConstraint,
    SignalConstraint,
    TimingDifferenceConstraint,
)
from jitx.test import TestCase

from jitxexamples.protocols.memory.lpddr4 import (
    LPDDR4,
    LPDDR4Constraint,
    LPDDR4ConstraintParams,
    LPDDR4Rank,
    LPDDR4SharedCKE,
    LPDDR4Width,
    signal_ports,
)
from jitxexamples.protocols.memory.lpddr4_example import (
    LPDDR4Example,
    LPDDR4ExampleDesign,
)

PS = 1e-12

type Ends = tuple[Port, Port]


def _constrains(sc: object) -> list[BaseConstrain]:
    assert isinstance(sc, SignalConstraint)
    out = list(sc.constrains)
    for value in vars(sc).values():
        if isinstance(value, SignalConstraint):
            out += _constrains(value)
    return out


def _windows(c: BaseConstrain) -> set[tuple[float, float]]:
    pairwise = getattr(c, "_pairwise_constraints", [])
    return {
        (round(t.min_delta / PS, 3), round(t.max_delta / PS, 3))
        for t in pairwise
        if isinstance(t, TimingDifferenceConstraint)
    }


def _losses(c: BaseConstrain) -> set[float]:
    return {
        t.max_loss for t in c._constraints if isinstance(t, InsertionLossConstraint)
    }


def _reference_windows(
    constrains: list[BaseConstrain],
) -> dict[tuple[Ends, Ends], set[tuple[float, float]]]:
    """(guide ends, target ends) -> skew window in ps."""
    ref: dict[tuple[Ends, Ends], set[tuple[float, float]]] = {}
    for c in constrains:
        if isinstance(c, ConstrainReferenceDifference):
            g = (c.guide.begin, c.guide.end)
            for t in c.topologies:
                ref.setdefault((g, (t.begin, t.end)), set()).update(_windows(c))
    return ref


class TestLPDDR4Example(TestCase):
    def setUp(self) -> None:
        design = LPDDR4ExampleDesign()
        circuit = design.circuit
        assert isinstance(circuit, LPDDR4Example)
        self.ctrl: LPDDR4 = circuit.controller.lpddr4
        self.mem: LPDDR4 = circuit.memory.lpddr4
        si = circuit.si
        assert isinstance(si, LPDDR4Constraint)
        constrains = _constrains(si)
        self.constrains = constrains

        # diff-pair ends (p pins) -> skew window in ps
        self.diff: dict[Ends, set[tuple[float, float]]] = {}
        # ends, single-ended or one side of a pair, with a routing structure
        self.structured: set[Ends] = set()
        self.ref = _reference_windows(constrains)
        for c in constrains:
            if isinstance(c, ConstrainDiffPair):
                for t in c.topologies:
                    self.diff[(t.begin.p, t.end.p)] = _windows(c)
                    if c._structure is not None:
                        self.structured.add((t.begin.p, t.end.p))
                        self.structured.add((t.begin.n, t.end.n))
            elif isinstance(c, Constrain):
                for t in c.topologies:
                    if c._structure is not None:
                        self.structured.add((t.begin, t.end))

    def test_every_signal_has_a_routing_structure(self) -> None:
        """Every LPDDR4 signal is constrained from controller pin to memory pin."""
        for ends in zip(signal_ports(self.ctrl), signal_ports(self.mem), strict=True):
            self.assertIn(ends, self.structured)

    def test_no_uncited_loss_limit(self) -> None:
        """UG583 gives no loss figure, so the default sets no loss limit."""
        for c in self.constrains:
            self.assertEqual(_losses(c), set())

    def test_loss_limit_applies_when_given(self) -> None:
        """A loss passed in the parameters reaches every signal."""
        si = LPDDR4Constraint(
            diff_structure=SampleSubstrate.DRS_100,
            se_structure=SampleSubstrate.RS_50,
            params=LPDDR4ConstraintParams(loss=4.0),
        )
        bus_a = LPDDR4(LPDDR4Width.x16, LPDDR4Rank.Rank1)
        bus_b = LPDDR4(LPDDR4Width.x16, LPDDR4Rank.Rank1)
        si.constrain(bus_a, bus_b)
        limited = [
            c for c in si.constrains if isinstance(c, Constrain | ConstrainDiffPair)
        ]
        self.assertEqual(len(limited), 1 + 1 + 1 + 6 + 2 * (1 + 1 + 8))
        for c in limited:
            self.assertEqual(_losses(c), {4.0})

    def test_nonpositive_spread_is_rejected(self) -> None:
        """A DQ spread of zero or less raises instead of building a window."""
        with self.assertRaises(ValueError):
            LPDDR4ConstraintParams(spread_dq=0.0)

    def test_clock_and_strobe_intra_pair_skew(self) -> None:
        """CK and DQS pairs carry the UG583 +/-2.0 ps intra-pair skew."""
        for s_ch, d_ch in zip(self.ctrl.ch, self.mem.ch, strict=True):
            self.assertEqual(self.diff[(s_ch.ck.p, d_ch.ck.p)], {(-2.0, 2.0)})
            for s_l, d_l in zip(s_ch.d, d_ch.d, strict=True):
                self.assertEqual(self.diff[(s_l.dqs.p, d_l.dqs.p)], {(-2.0, 2.0)})

    def test_command_address_to_clock(self) -> None:
        """CKE, CS and CA0 to CA5 are each held +/-8.0 ps from CK.p."""
        for s_ch, d_ch in zip(self.ctrl.ch, self.mem.ch, strict=True):
            guide = (s_ch.ck.p, d_ch.ck.p)
            sigs = [
                *zip(s_ch.cke, d_ch.cke, strict=True),
                *zip(s_ch.cs, d_ch.cs, strict=True),
                *zip(s_ch.ca, d_ch.ca, strict=True),
            ]
            self.assertEqual(len(sigs), 2 + 2 + 6)
            for ends in sigs:
                self.assertEqual(self.ref[(guide, ends)], {(-8.0, 8.0)})

    def test_strobe_to_clock_window(self) -> None:
        """CK.p minus each DQS.p is held to -500 ps to +2500 ps (CK.p is the guide)."""
        for s_ch, d_ch in zip(self.ctrl.ch, self.mem.ch, strict=True):
            guide = (s_ch.ck.p, d_ch.ck.p)
            for s_l, d_l in zip(s_ch.d, d_ch.d, strict=True):
                key = (guide, (s_l.dqs.p, d_l.dqs.p))
                self.assertEqual(self.ref[key], {(-500.0, 2500.0)})

    def test_all_eight_dq_to_strobe_and_mask(self) -> None:
        """All eight DQ per lane, DQ0 included, are tied to DQS.p and DMI."""
        for s_ch, d_ch in zip(self.ctrl.ch, self.mem.ch, strict=True):
            for s_l, d_l in zip(s_ch.d, d_ch.d, strict=True):
                dqs = (s_l.dqs.p, d_l.dqs.p)
                dmi = (s_l.dmi, d_l.dmi)
                self.assertEqual(self.ref[(dqs, dmi)], {(-5.0, 5.0)})
                for ends in zip(s_l.dq, d_l.dq, strict=True):
                    self.assertEqual(self.ref[(dqs, ends)], {(-5.0, 5.0)})
                    self.assertEqual(self.ref[(dmi, ends)], {(-2.5, 2.5)})

    def test_rank_mismatch_is_rejected(self) -> None:
        """Bundles of different rank raise instead of silently pairing."""
        si = LPDDR4Constraint(
            diff_structure=SampleSubstrate.DRS_100,
            se_structure=SampleSubstrate.RS_50,
        )
        with self.assertRaises(ValueError):
            si.constrain(
                LPDDR4(LPDDR4Width.x32, LPDDR4Rank.Rank2),
                LPDDR4(LPDDR4Width.x32, LPDDR4Rank.Rank1),
            )

    def test_shared_cke_reaches_both_cke_balls(self) -> None:
        """A shared-CKE controller's one CKE is held +/-8.0 ps from CK.p to
        each of the memory channel's two CKE balls."""
        si = LPDDR4Constraint(
            diff_structure=SampleSubstrate.DRS_100,
            se_structure=SampleSubstrate.RS_50,
        )
        ctrl = LPDDR4SharedCKE()
        mem = LPDDR4(LPDDR4Width.x32, LPDDR4Rank.Rank2)
        si.constrain(ctrl, mem)
        ref = _reference_windows(list(si.constrains))
        for s_ch, d_ch in zip(ctrl.ch, mem.ch, strict=True):
            guide = (s_ch.ck.p, d_ch.ck.p)
            self.assertEqual(len(d_ch.cke), 2)
            for ball in d_ch.cke:
                self.assertEqual(ref[(guide, (s_ch.cke, ball))], {(-8.0, 8.0)})

    def test_shared_cke_rejects_single_rank_memory(self) -> None:
        """A shared-CKE controller has two chip selects, so a single-rank
        memory raises instead of silently pairing."""
        si = LPDDR4Constraint(
            diff_structure=SampleSubstrate.DRS_100,
            se_structure=SampleSubstrate.RS_50,
        )
        with self.assertRaisesRegex(ValueError, "rank mismatch"):
            si.constrain(LPDDR4SharedCKE(), LPDDR4(LPDDR4Width.x32, LPDDR4Rank.Rank1))

    def test_no_spread_rule_when_spread_is_none(self) -> None:
        """With no spread rule, nothing is held against DMI, while every DQ
        keeps its +/-5.0 ps window to DQS.p."""
        si = LPDDR4Constraint(
            diff_structure=SampleSubstrate.DRS_100,
            se_structure=SampleSubstrate.RS_50,
            params=LPDDR4ConstraintParams(spread_dq=None),
        )
        ctrl = LPDDR4(LPDDR4Width.x16, LPDDR4Rank.Rank1)
        mem = LPDDR4(LPDDR4Width.x16, LPDDR4Rank.Rank1)
        si.constrain(ctrl, mem)
        ref = _reference_windows(list(si.constrains))
        for s_l, d_l in zip(ctrl.ch[0].d, mem.ch[0].d, strict=True):
            dmi = (s_l.dmi, d_l.dmi)
            self.assertFalse([k for k in ref if k[0] == dmi])
            dqs = (s_l.dqs.p, d_l.dqs.p)
            for ends in zip(s_l.dq, d_l.dq, strict=True):
                self.assertEqual(ref[(dqs, ends)], {(-5.0, 5.0)})

    def test_memory_side_first_is_rejected(self) -> None:
        """The controller and memory sides passed in the wrong order raise a
        TypeError naming the order."""
        si = LPDDR4Constraint(
            diff_structure=SampleSubstrate.DRS_100,
            se_structure=SampleSubstrate.RS_50,
        )
        with self.assertRaisesRegex(TypeError, "controller side first"):
            si.constrain(
                LPDDR4(LPDDR4Width.x32, LPDDR4Rank.Rank2),
                cast(LPDDR4, LPDDR4SharedCKE()),
            )

"""The DDR4 example applies every cited skew rule between controller and memory."""

from jitx.net import DiffPair, Port
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

from jitx.sample import SampleSubstrate

from jitxexamples.protocols.memory.ddr4 import (
    DDR4,
    DDR4AccChannel,
    DDR4AccConstraint,
    DDR4AccConstraintParams,
    DDR4Constraint,
    DDR4Rank,
    signal_ports,
)
from jitxexamples.protocols.memory.ddr4_example import (
    DDR4Example,
    DDR4ExampleDesign,
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


class TestDDR4Example(TestCase):
    def setUp(self) -> None:
        design = DDR4ExampleDesign()
        circuit = design.circuit
        assert isinstance(circuit, DDR4Example)
        self.ctrl: DDR4 = circuit.controller.ddr4
        self.mem: DDR4 = circuit.memory.ddr4
        si = circuit.si
        assert isinstance(si, DDR4Constraint)
        self.constrains = _constrains(si)

        # (guide ends, target ends) -> skew windows in ps
        self.ref: dict[tuple[Ends, Ends], set[tuple[float, float]]] = {}
        # diff-pair ends (p pins) -> skew windows in ps
        self.diff: dict[Ends, set[tuple[float, float]]] = {}
        # single-ended ends with a routing structure
        self.structured: set[Ends] = set()
        for c in self.constrains:
            if isinstance(c, ConstrainReferenceDifference):
                g = (c.guide.begin, c.guide.end)
                for t in c.topologies:
                    key = (g, (t.begin, t.end))
                    self.ref.setdefault(key, set()).update(_windows(c))
            elif isinstance(c, ConstrainDiffPair):
                for t in c.topologies:
                    self.diff[(t.begin.p, t.end.p)] = _windows(c)
                    if c._structure is not None:
                        self.structured.add((t.begin.p, t.end.p))
                        self.structured.add((t.begin.n, t.end.n))
            elif isinstance(c, Constrain):
                for t in c.topologies:
                    if c._structure is not None:
                        self.structured.add((t.begin, t.end))

    def _strobes(self) -> list[tuple[DiffPair, DiffPair]]:
        return list(zip(self.ctrl.data.DQS, self.mem.data.DQS, strict=True))

    def test_every_signal_has_a_routing_structure(self) -> None:
        """Every DDR4 signal is constrained from controller pin to memory pin."""
        for ends in zip(signal_ports(self.ctrl), signal_ports(self.mem), strict=True):
            self.assertIn(ends, self.structured)

    def test_no_uncited_loss_limit(self) -> None:
        """The cited rules give no loss limit, so the default sets none."""
        for c in self.constrains:
            losses = [
                t for t in c._constraints if isinstance(t, InsertionLossConstraint)
            ]
            self.assertEqual(losses, [])

    def test_clock_and_strobe_intra_pair_skew(self) -> None:
        """CK and both DQS pairs carry the +/-1.0 ps intra-pair skew."""
        ck = (self.ctrl.acc.CK[0].p, self.mem.acc.CK[0].p)
        self.assertEqual(self.diff[ck], {(-1.0, 1.0)})
        for s, d in self._strobes():
            self.assertEqual(self.diff[(s.p, d.p)], {(-1.0, 1.0)})

    def test_data_to_strobe_per_byte_lane(self) -> None:
        """DQ0-7 and DM_n[0] follow DQS[0]; DQ8-15 and DM_n[1] follow DQS[1]."""
        data_s, data_d = self.ctrl.data, self.mem.data
        for lane, (s_dqs, d_dqs) in enumerate(self._strobes()):
            guide = (s_dqs.p, d_dqs.p)
            members = [
                (data_s.DQ[j], data_d.DQ[j]) for j in range(8 * lane, 8 * lane + 8)
            ]
            members.append((data_s.DM_n[lane], data_d.DM_n[lane]))
            for ends in members:
                self.assertEqual(self.ref[(guide, ends)], {(-3.5, 3.5)})

    def test_address_command_control_to_clock_and_cke(self) -> None:
        """A, ACT_n, BG, BA, CS_n, ODT and PAR are within 20 ps of CK.P and
        within 10 ps of CKE[0], so their spread stays under the 20 ps rule;
        RESET_n and ALERT_n get no skew."""
        s, d = self.ctrl.acc, self.mem.acc
        ck = (s.CK[0].p, d.CK[0].p)
        cke = (s.CKE[0], d.CKE[0])
        timed: list[Ends] = [
            *zip(s.A, d.A, strict=True),
            (s.ACT_n, d.ACT_n),
            *zip(s.BG, d.BG, strict=True),
            *zip(s.BA, d.BA, strict=True),
            *zip(s.CS_n, d.CS_n, strict=True),
            *zip(s.ODT, d.ODT, strict=True),
            (s.PAR, d.PAR),
        ]
        self.assertEqual(len(timed), 17 + 1 + 1 + 2 + 1 + 1 + 1)
        self.assertEqual(self.ref[(ck, cke)], {(-20.0, 20.0)})
        for ends in timed:
            self.assertEqual(self.ref[(ck, ends)], {(-20.0, 20.0)})
            self.assertEqual(self.ref[(cke, ends)], {(-10.0, 10.0)})
        untimed = {(s.RESET_n, d.RESET_n), (s.ALERT_n, d.ALERT_n)}
        for guide_ends, target in self.ref:
            self.assertNotIn(target, untimed, guide_ends)

    def test_strobe_to_clock_window(self) -> None:
        """CK.P minus each DQS.P is held to -85 ps to +935 ps (CK.P is the guide)."""
        ck = (self.ctrl.acc.CK[0].p, self.mem.acc.CK[0].p)
        for s, d in self._strobes():
            self.assertEqual(self.ref[(ck, (s.p, d.p))], {(-85.0, 935.0)})

    def test_no_skew_between_clock_pairs(self) -> None:
        """The table gives no CK-pair-to-CK-pair rule, so none is applied."""
        si = DDR4AccConstraint(SampleSubstrate.DRS_100, SampleSubstrate.RS_50)
        bus_a = DDR4AccChannel(DDR4Rank.SingleRank, ck_count=2)
        bus_b = DDR4AccChannel(DDR4Rank.SingleRank, ck_count=2)
        si.constrain(bus_a, bus_b)
        targets = {
            (t.begin, t.end)
            for c in si.constrains
            if isinstance(c, ConstrainReferenceDifference)
            for t in c.topologies
        }
        self.assertNotIn((bus_a.CK[1].p, bus_b.CK[1].p), targets)

    def test_nonpositive_spread_is_rejected(self) -> None:
        """An ACC spread of zero or less raises instead of building a window."""
        with self.assertRaises(ValueError):
            DDR4AccConstraintParams(spread_acc=-1.0e-12)

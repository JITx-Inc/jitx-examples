"""JS4: the UG863 constraints the shipping design applies.

Source: AMD UG863 v1.12, "Timing Constraint Rules for LPDDR4/4x Signals",
Table 1, and "Physical Design Rules for LPDDR4/4x Signals", Table 1.
"""

from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory

from jitx.net import Port
from jitx.si import (
    Constrain,
    ConstrainDiffPair,
    ConstrainReferenceDifference,
    TerminatingPinModel,
    TimingConstraint,
    TimingDifferenceConstraint,
)
from jitx.substrate import SubstrateContext
from jitx.test import TestCase

from jitxexamples.jumpstart_kits.js1_stackup_components.hdi_stackup.board import (
    MICROSTRIP_LAYERS,
    STRIPLINE_LAYERS,
    HDISubstrate,
)
from jitxexamples.jumpstart_kits.js4_si_constraints.constraint import length_budget
from jitxexamples.jumpstart_kits.js1_stackup_components.versal_fpga.xcvp1002 import (
    XCVP1002,
)
from jitxexamples.jumpstart_kits.js4_si_constraints.main import JS4Circuit, JS4Design
from jitxexamples.jumpstart_kits.js4_si_constraints.models import (
    MicroVia_L1_L2,
    MicroVia_L2_L3,
    MicroVia_L3_L4,
    MicroVia_L4_L5,
    read_package_delays,
)
from jitxexamples.jumpstart_kits.vp1002_lpddr4x.package_delays import (
    SYNTHETIC_CSV,
    render,
    triplet_balls,
)
from jitxexamples.jumpstart_kits.vp1002_lpddr4x.pinout import LPDDR4X_X32

C_M_PER_S = 299_792_458
"Speed of light in vacuum."

STRIPLINE_EPS_EFF = 2.96
"JS1 fab report, IMPEDANCE rows SE-50 on the inner striplines."

MICROSTRIP_EPS_EFF = 2.4572
"JS1 fab report, IMPEDANCE row SE-50 on the outer microstrips."


@cache
def design() -> JS4Design:
    """One shared instantiation; call only inside a TestCase."""
    return JS4Design()


def circuit() -> JS4Circuit:
    c = design().circuit
    assert isinstance(c, JS4Circuit)
    return c


class TestTimingConstraints(TestCase):
    """UG863 v1.12 Table 1, as :py:mod:`.constraint` applies it."""

    def references(self) -> list[ConstrainReferenceDifference]:
        circuit = design().circuit
        assert isinstance(circuit, JS4Circuit)
        return [
            c
            for c in circuit.lpddr4x_si.skews.constrains
            if isinstance(c, ConstrainReferenceDifference)
        ]

    def test_no_dq_spread_rule(self) -> None:
        """UG863 has no DQ to DQ spread rule, so nothing is held against DMI."""
        circuit = design().circuit
        assert isinstance(circuit, JS4Circuit)
        dmi = {lane.dmi for ch in circuit.memory.lpddr4.ch for lane in ch.d}
        for c in self.references():
            self.assertNotIn(c.guide.end, dmi)

    def test_one_fpga_cke_held_to_both_balls(self) -> None:
        """Per channel, the FPGA's one CKE is held +/-20 ps from CK_T to each
        of the memory's two CKE balls."""
        circuit = design().circuit
        assert isinstance(circuit, JS4Circuit)
        for ch in circuit.memory.lpddr4.ch:
            starts: list[Port] = []
            for ball in ch.cke:
                found = [
                    (c, t)
                    for c in self.references()
                    if c.guide.end is ch.ck.p
                    for t in c.topologies
                    if t.end is ball
                ]
                self.assertEqual(len(found), 1)
                c, t = found[0]
                starts.append(t.begin)
                windows = {
                    (round(w.min_delta * 1e12, 3), round(w.max_delta * 1e12, 3))
                    for w in getattr(c, "_pairwise_constraints", [])
                    if isinstance(w, TimingDifferenceConstraint)
                }
                self.assertEqual(windows, {(-20.0, 20.0)})
            self.assertIs(starts[0], starts[1])


class TestLengthBudget(TestCase):
    """Physical Table 1: 3600 mil for CAC and data signals, as a delay."""

    def limits(self) -> list[Constrain]:
        return [c for c in circuit().lpddr4x_si.constrains if isinstance(c, Constrain)]

    def test_budget_is_3600_mil_on_the_stripline(self) -> None:
        expected = 3600 * 25.4e-6 * STRIPLINE_EPS_EFF**0.5 / C_M_PER_S
        for c in self.limits():
            highs = {
                t.max_delay
                for t in getattr(c, "_constraints", [])
                if isinstance(t, TimingConstraint)
            }
            self.assertEqual(len(highs), 1)
            self.assertAlmostEqual(highs.pop(), expected, delta=0.1e-12)

    def test_budget_converts_on_the_fastest_layer(self) -> None:
        """Across layers of different velocity the limit is the conservative
        one: 3600 mil on the fastest layer, here the microstrip."""
        layers = (*MICROSTRIP_LAYERS, *STRIPLINE_LAYERS)
        expected = 3600 * 25.4e-6 * MICROSTRIP_EPS_EFF**0.5 / C_M_PER_S
        with SubstrateContext(HDISubstrate()):
            budget = length_budget(HDISubstrate.SE_50, layers)
        self.assertAlmostEqual(budget, expected, delta=0.1e-12)

    def test_every_cac_and_data_signal_and_no_clock_or_strobe(self) -> None:
        mem = circuit().memory.lpddr4
        expected: set[int] = set()
        excluded: set[int] = set()
        for ch in mem.ch:
            expected |= {id(p) for p in (*ch.cke, *ch.cs, *ch.ca)}
            excluded |= {id(ch.ck.p), id(ch.ck.n)}
            for lane in ch.d:
                expected |= {id(p) for p in (lane.dmi, *lane.dq)}
                excluded |= {id(lane.dqs.p), id(lane.dqs.n)}
        ends: list[Port] = [t.end for c in self.limits() for t in c.topologies]
        self.assertEqual({id(e) for e in ends}, expected)
        self.assertEqual(len(ends), len(expected))
        self.assertFalse({id(e) for e in ends} & excluded)


def window_ps(c: object) -> set[tuple[float, float]]:
    """The skew windows a constraint carries, in ps."""
    return {
        (round(w.min_delta * 1e12, 3), round(w.max_delta * 1e12, 3))
        for w in getattr(c, "_pairwise_constraints", [])
        if isinstance(w, TimingDifferenceConstraint)
    }


class TestSkewWindows(TestCase):
    """Every skew UG863 v1.12 timing Table 1 sets for this link, with its
    window: per channel the CK pair, two CKE, two CS and six CA against CK_T;
    per byte the DQS pair, DQS against CK_T, and DMI and eight DQ against
    DQS_T."""

    def test_each_signal_has_its_table_window(self) -> None:
        mem = circuit().memory.lpddr4
        expected: dict[int, tuple[str, set[tuple[float, float]]]] = {}
        for ch in mem.ch:
            expected[id(ch.ck)] = ("CK pair", {(-2.0, 2.0)})
            for p in (*ch.cke, *ch.cs):
                expected[id(p)] = ("CKE or CS", {(-20.0, 20.0)})
            for p in ch.ca:
                expected[id(p)] = ("CA", {(-100.0, 100.0)})
            for lane in ch.d:
                expected[id(lane.dqs)] = ("DQS pair", {(-2.0, 2.0)})
                expected[id(lane.dqs.p)] = ("DQS to CK", {(-150.0, 150.0)})
                for p in (lane.dmi, *lane.dq):
                    expected[id(p)] = ("DQ or DMI", {(-100.0, 100.0)})
        seen: list[int] = []
        for c in circuit().lpddr4x_si.skews.constrains:
            if not isinstance(c, ConstrainReferenceDifference | ConstrainDiffPair):
                continue
            ends = [t.end for t in c.topologies]
            for end in ends:
                name, window = expected[id(end)]
                with self.subTest(signal=name):
                    self.assertEqual(window_ps(c), window)
                seen.append(id(end))
        self.assertEqual(sorted(seen), sorted(expected))


def csv_rows() -> list[list[str]]:
    """The synthetic package delay file's data rows, split by hand."""
    lines = SYNTHETIC_CSV.read_text(encoding="utf-8").splitlines()
    data = [line.split(",") for line in lines if not line.startswith("#")]
    return data[1:]


def models_by_port() -> dict[int, TerminatingPinModel]:
    return {id(m.port): m for m in circuit().package_delays}


class TestPackageDelay(TestCase):
    """UG863 v1.12: include the adaptive SoC's package delays in every skew
    calculation, and use the midpoint of a minimum and a maximum."""

    def test_file_says_synthetic(self) -> None:
        """No reader may take the estimates for AMD data."""
        first = SYNTHETIC_CSV.read_text(encoding="utf-8").splitlines()[0]
        self.assertTrue(first.startswith("# SYNTHETIC ESTIMATES, NOT AMD DATA"))

    def test_every_offered_pin_has_a_model(self) -> None:
        """Every FPGA pin the LPDDR4X offer can put a memory signal on."""
        positions = [
            pos
            for name, pos in LPDDR4X_X32.fixed.items()
            if name not in {"SYS_CLK_P", "SYS_CLK_N", "RESET_N"}
        ]
        for slot in LPDDR4X_X32.slots:
            positions += [slot.dqs_t, slot.dqs_c, slot.dmi, *slot.dq]
        pins = circuit().fpga.fpga.xpio_triplet_pins()[0]
        modeled = models_by_port()
        for pos in positions:
            with self.subTest(pos=pos):
                self.assertIn(id(pins[pos.index].port), modeled)

    def test_one_model_per_row_at_its_midpoint(self) -> None:
        rows = csv_rows()
        expected = sorted((float(r[2]) + float(r[3])) / 2 * 1e-12 for r in rows)
        got = sorted(m.delay.typ for m in circuit().package_delays)
        self.assertEqual(len(got), len(expected))
        for g, e in zip(got, expected, strict=True):
            self.assertAlmostEqual(g, e, delta=1e-16)

    def test_ball_at20_takes_its_own_row(self) -> None:
        """AMD's pin file puts IO_L8P_N2P4_M0P70_701 on ball AT20."""
        row = next(r for r in csv_rows() if r[1] == "AT20")
        port = circuit().fpga.fpga.IO_L8P_N2P4_M0P70_701
        model = models_by_port()[id(port)]
        mid = (float(row[2]) + float(row[3])) / 2 * 1e-12
        self.assertAlmostEqual(model.delay.typ, mid, delta=1e-16)

    def test_pair_legs_alike(self) -> None:
        """Both legs of a P/N pair take one value. AMD's VP1002 pin file puts
        IO_L9P_GC_XCC_N3P0_M0P126_702 on AT28 and IO_L9N_GC_XCC_N3P1_M0P127_702
        on AU29."""
        rows = {r[1]: r[2:] for r in csv_rows()}
        self.assertEqual(rows["AT28"], rows["AU29"])

    def test_reads_an_export_by_column_name(self) -> None:
        """UG899 Appendix A's export columns, in its order, with a row for a
        pin that has no delay: only delay rows, each at its midpoint."""
        text = (
            "# comment\n"
            "I/O Bank,Pin Number,Site,Site Type,"
            "Min Trace Delay (ps),Max Trace Delay (ps),Trace Length (um)\n"
            "701,AT20,IOB_X0Y0,IO_L8P,100.0,110.0,\n"
            ",AM17,,VCCO_702,,,\n"
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "export.csv"
            path.write_text(text, encoding="utf-8")
            delays = read_package_delays(path)
        self.assertEqual(set(delays), {"AT20"})
        self.assertAlmostEqual(delays["AT20"], 105.0e-12, delta=1e-16)

    def test_file_matches_its_formula(self) -> None:
        """The file is generated; a hand edit or a stale file fails here."""
        with SubstrateContext(HDISubstrate()):
            text = render(triplet_balls(XCVP1002()))
        self.assertEqual(SYNTHETIC_CSV.read_text(encoding="utf-8"), text)


class TestViaDelay(TestCase):
    """Barrel transit, mid-copper to mid-copper, through one JS1 build-up
    layer: D * sqrt(Dk) / c. Thicknesses and Dk from the JS1 fab report's
    STACKUP rows (Rev B): build-up D-BU 0.1000 mm, Dk 2.96; L1 CU-OUT
    0.0355 mm; plane CU-PLN 0.0350 mm; signal CU-SIG 0.0175 mm."""

    def delay(self, top_mm: float, bottom_mm: float) -> float:
        span_m = (top_mm / 2 + 0.1000 + bottom_mm / 2) * 1e-3
        return span_m * 2.96**0.5 / C_M_PER_S

    def test_each_microvia(self) -> None:
        cases = (
            (MicroVia_L1_L2, (0, 1), self.delay(0.0355, 0.0350)),
            (MicroVia_L2_L3, (1, 2), self.delay(0.0350, 0.0175)),
            (MicroVia_L3_L4, (2, 3), self.delay(0.0175, 0.0350)),
            (MicroVia_L4_L5, (3, 4), self.delay(0.0350, 0.0175)),
        )
        for via, span, expected in cases:
            with self.subTest(via=via.__name__):
                model = via.models[span]
                self.assertAlmostEqual(model.delay.typ, expected, delta=1e-16)

from jitx.inspect import extract
from jitx.landpattern import Pad
from jitx.net import Port
from jitx.sample import SampleSubstrate
from jitx.test import TestCase

from jitxexamples.components.memories.MT53E1G32D2FW_046_WT_B import (
    MT53E1G32D2FW_046_WT_B,
)
from jitxexamples.protocols.memory.lpddr4 import signal_ports

# Micron z42m data sheet Rev. I, Figure 6, "200-Ball Dual-Channel, Dual-Rank
# Discrete FBGA": one row per line, the ten populated columns in order.
FIGURE_6 = """
    A DNU DNU VSS VDD2 ZQ0 ZQ1 VDD2 VSS DNU DNU
    B DNU DQ0_A VDDQ DQ7_A VDDQ VDDQ DQ15_A VDDQ DQ8_A DNU
    C VSS DQ1_A DMI0_A DQ6_A VSS VSS DQ14_A DMI1_A DQ9_A VSS
    D VDDQ VSS DQS0_t_A VSS VDDQ VDDQ VSS DQS1_t_A VSS VDDQ
    E VSS DQ2_A DQS0_c_A DQ5_A VSS VSS DQ13_A DQS1_c_A DQ10_A VSS
    F VDD1 DQ3_A VDDQ DQ4_A VDD2 VDD2 DQ12_A VDDQ DQ11_A VDD1
    G VSS ODT_CA_A VSS VDD1 VSS VSS VDD1 VSS NC VSS
    H VDD2 CA0_A CS1_A CS0_A VDD2 VDD2 CA2_A CA3_A CA4_A VDD2
    J VSS CA1_A VSS CKE0_A CKE1_A CK_t_A CK_c_A VSS CA5_A VSS
    K VDD2 VSS VDD2 VSS NC NC VSS VDD2 VSS VDD2
    N VDD2 VSS VDD2 VSS NC NC VSS VDD2 VSS VDD2
    P VSS CA1_B VSS CKE0_B CKE1_B CK_t_B CK_c_B VSS CA5_B VSS
    R VDD2 CA0_B CS1_B CS0_B VDD2 VDD2 CA2_B CA3_B CA4_B VDD2
    T VSS ODT_CA_B VSS VDD1 VSS VSS VDD1 VSS RESET_n VSS
    U VDD1 DQ3_B VDDQ DQ4_B VDD2 VDD2 DQ12_B VDDQ DQ11_B VDD1
    V VSS DQ2_B DQS0_c_B DQ5_B VSS VSS DQ13_B DQS1_c_B DQ10_B VSS
    W VDDQ VSS DQS0_t_B VSS VDDQ VDDQ VSS DQS1_t_B VSS VDDQ
    Y VSS DQ1_B DMI0_B DQ6_B VSS VSS DQ14_B DMI1_B DQ9_B VSS
    AA DNU DQ0_B VDDQ DQ7_B VDDQ VDDQ DQ15_B VDDQ DQ8_B DNU
    AB DNU DNU VSS VDD2 VSS VSS VDD2 VSS DNU DNU
"""
FIGURE_6_COLUMNS = (1, 2, 3, 4, 5, 8, 9, 10, 11, 12)


class TestMT53E1G32D2FW_046_WT_B(TestCase):
    def setUp(self) -> None:
        SampleSubstrate()  # the landpattern reads the current substrate
        self.comp = MT53E1G32D2FW_046_WT_B()

    def test_200_balls_all_mapped(self) -> None:
        """The FW package has 200 balls (Micron z42m data sheet Rev. I,
        Figure 6), and every one is mapped to exactly one port."""
        pads = list(extract(self.comp.landpattern, Pad))
        self.assertEqual(len(pads), 200)
        self.assertEqual(len(self.comp.mapping[0].inverse()), 200)

    def test_grid_pitch_and_depopulation(self) -> None:
        """0.8 mm column pitch, 0.65 mm row pitch, A1 at (-4.4, 6.825)
        (8.8 mm and 13.65 mm between outer ball centers, Figure 10), and no
        balls in columns 6 and 7 or rows L and M."""
        lp = self.comp.landpattern

        def xy(pad: Pad) -> tuple[float, float]:
            transform = pad.transform
            assert transform is not None
            x, y = transform.translation
            return round(x, 4), round(y, 4)

        self.assertEqual(xy(lp.A[1]), (-4.4, 6.825))
        self.assertEqual(xy(lp.A[2]), (-3.6, 6.825))
        self.assertEqual(xy(lp.B[1]), (-4.4, 6.175))
        self.assertEqual(xy(lp.AB[12]), (4.4, -6.825))
        for row in (lp.A, lp.K, lp.N, lp.AB):
            self.assertEqual(sorted(row), [1, 2, 3, 4, 5, 8, 9, 10, 11, 12])
        self.assertFalse(hasattr(lp, "L"))
        self.assertFalse(hasattr(lp, "M"))

    def test_lpddr4_balls_match_figure_6(self) -> None:
        """Every LPDDR4 signal has its own ball; spot checks against the
        dual-rank ball map."""
        mapping = self.comp.mapping[0]
        lp = self.comp.landpattern
        bus = self.comp.lpddr4
        signals = signal_ports(bus)
        self.assertEqual(len(signals), 68)
        self.assertEqual(len({id(mapping[p]) for p in signals}), 68)
        self.assertIs(mapping[bus.ch[0].ck.p], lp.J[8])
        self.assertIs(mapping[bus.ch[0].ck.n], lp.J[9])
        self.assertIs(mapping[bus.ch[1].ck.p], lp.P[8])
        self.assertIs(mapping[bus.ch[0].d[0].dqs.p], lp.D[3])
        self.assertIs(mapping[bus.ch[0].d[1].dmi], lp.C[10])
        self.assertIs(mapping[bus.ch[1].d[0].dq[0]], lp.AA[2])
        self.assertIs(mapping[bus.ch[1].cs[1]], lp.R[3])
        self.assertIs(mapping[self.comp.RESET_n], lp.T[11])

    def _port_names(self) -> dict[int, str]:
        """Figure 6 names for every port, keyed by port identity."""
        comp = self.comp
        names: dict[int, str] = {}

        def name(port: Port, label: str) -> None:
            names[id(port)] = label

        for index, ch in enumerate(comp.lpddr4.ch):
            side = "AB"[index]
            name(ch.ck.p, f"CK_t_{side}")
            name(ch.ck.n, f"CK_c_{side}")
            for k, port in enumerate(ch.cke):
                name(port, f"CKE{k}_{side}")
            for k, port in enumerate(ch.cs):
                name(port, f"CS{k}_{side}")
            for k, port in enumerate(ch.ca):
                name(port, f"CA{k}_{side}")
            for j, lane in enumerate(ch.d):
                for k, port in enumerate(lane.dq):
                    name(port, f"DQ{8 * j + k}_{side}")
                name(lane.dmi, f"DMI{j}_{side}")
                name(lane.dqs.p, f"DQS{j}_t_{side}")
                name(lane.dqs.n, f"DQS{j}_c_{side}")
        for attr in (
            "ODT_CA_A",
            "ODT_CA_B",
            "RESET_n",
            "ZQ0",
            "ZQ1",
            "NC",
            "DNU",
        ):
            name(getattr(comp, attr), attr)
        for attr in ("VDD1", "VDD2", "VDDQ", "VSS"):
            for port in getattr(comp, attr):
                name(port, attr)
        return names

    def test_every_ball_matches_figure_6(self) -> None:
        """All 200 balls carry the signal Figure 6 gives them."""
        expected: dict[str, str] = {}
        for line in FIGURE_6.strip().splitlines():
            row, *labels = line.split()
            for column, label in zip(FIGURE_6_COLUMNS, labels, strict=True):
                expected[f"{row}{column}"] = label
        self.assertEqual(len(expected), 200)

        lp = self.comp.landpattern
        ball_of: dict[int, str] = {}
        for line in FIGURE_6.strip().splitlines():
            row = line.split()[0]
            for column, pad in getattr(lp, row).items():
                ball_of[id(pad)] = f"{row}{column}"
        names = self._port_names()
        got = {
            ball_of[id(pad)]: names[id(port)]
            for pad, port in self.comp.mapping[0].inverse().items()
        }
        self.assertEqual(got, expected)

from jitx.sample import SampleSubstrate
from jitx.test import TestCase

from jitxexamples.components.memories.MT40A1G16TB_062E_F import MT40A1G16TB_062E_F
from jitxexamples.protocols.memory.ddr4 import signal_ports


class TestMT40A1G16TB_062E_F(TestCase):
    def test_ddr4_bundle_maps_one_ball_per_signal(self) -> None:
        """Every DDR4 signal maps to its own ball, and all 96 balls are used.

        The balls checked are the ones carried over from jitx-protocols-ext
        33501cb, not read from the Micron datasheet.
        """
        SampleSubstrate()  # the landpattern reads the current substrate
        comp = MT40A1G16TB_062E_F()
        mapping = comp.mapping[0]
        lp = comp.landpattern
        signals = signal_ports(comp.ddr4)
        self.assertEqual(len(signals), 51)
        self.assertEqual(len({id(mapping[p]) for p in signals}), 51)
        self.assertEqual(len(mapping.inverse()), 96)
        data, acc = comp.ddr4.data, comp.ddr4.acc
        self.assertIs(mapping[data.DQ[0]], lp.G[2])
        self.assertIs(mapping[data.DQS[0].p], lp.G[3])
        self.assertIs(mapping[data.DQS[1].p], lp.B[7])
        self.assertIs(mapping[data.DM_n[0]], lp.E[7])
        self.assertIs(mapping[acc.CK[0].p], lp.K[7])
        self.assertIs(mapping[acc.CK[0].n], lp.K[8])

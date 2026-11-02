"""Tests for the daisy-chain SI pattern.

The shape jitx-interconnect-constraints points at: a ``>>`` chain in the
order driver, ``load0``, ``load1``; code routes in that order; one timing
constraint over both paths; and exactly one routing structure, on the longest
path. A second structure on the shared segment makes the report flag
overlapping and ambiguous structures (module docstring), so the test fails if
one is added. The runtime measurement is in the module docstring.
"""

from __future__ import annotations

from jitx.circuit import Route
from jitx.inspect import extract
from jitx.net import TopologyNet
from jitx.si import Constrain
from jitx.test import TestCase

from jitxexamples.patterns.si_daisy_chain import DaisyChain, DaisyChainDesign


class TestDaisyChain(TestCase):
    def setUp(self) -> None:
        circuit = DaisyChainDesign().circuit
        assert isinstance(circuit, DaisyChain)
        self.c = circuit

    def test_chain_order(self) -> None:
        (chain,) = extract(self.c, TopologyNet)
        self.assertEqual(
            list(chain.sequence), [self.c.drv.io, self.c.load0.io, self.c.load1.io]
        )

    def test_routes_follow_the_chain(self) -> None:
        hops = [(r.source, r.destination) for r in extract(self.c, Route)]
        self.assertEqual(
            hops, [(self.c.drv.io, self.c.load0.io), (self.c.load0.io, self.c.load1.io)]
        )

    def test_one_structure_over_the_longest_path(self) -> None:
        structured = [c for c in extract(self.c, Constrain) if c._structure is not None]
        self.assertEqual(len(structured), 1)
        (topo,) = structured[0].topologies
        self.assertIs(topo.begin, self.c.drv.io)
        self.assertIs(topo.end, self.c.load1.io)

    def test_timing_covers_both_loads(self) -> None:
        self.assertEqual(
            [(t.begin, t.end) for t in self.c.clk_timing.topologies],
            [(self.c.drv.io, self.c.load0.io), (self.c.drv.io, self.c.load1.io)],
        )

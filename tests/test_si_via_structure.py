"""Tests for the via-structure SI pattern.

The shape jitx-interconnect-constraints points at: a ``SingleViaStructure``
around the modeled signal via, netted in by its ``sig_in`` and ``sig_out``
ports, its ``COMMON`` port on a ground net, routes to its ``signal_via`` on
each layer, and a constraint on the outer pads. The runtime measurement is in
the module docstring.
"""

from __future__ import annotations

from jitx.circuit import Route
from jitx.inspect import extract
from jitx.net import Net
from jitx.test import TestCase
from jitxlib.via_structures import PolarViaGroundCage

from jitxexamples.patterns.si_via_model import ExampleSignalVia
from jitxexamples.patterns.si_via_structure import CagedVia, CagedViaDesign


class TestCagedVia(TestCase):
    def setUp(self) -> None:
        circuit = CagedViaDesign().circuit
        assert isinstance(circuit, CagedVia)
        self.c = circuit

    def test_signal_via_is_the_modeled_via_with_a_cage(self) -> None:
        self.assertIsInstance(self.c.vs.signal_via, ExampleSignalVia)
        (cage,) = self.c.vs.ground_cages
        assert isinstance(cage, PolarViaGroundCage)
        self.assertEqual(len(cage.vias), cage.count)

    def test_no_cage_via_sits_on_the_straight_run(self) -> None:
        # The run is the x axis through the signal via at the origin; a cage
        # via within a pad's width of it blocks the routes.
        (cage,) = self.c.vs.ground_cages
        assert isinstance(cage, PolarViaGroundCage)
        for via in cage.vias:
            assert via.transform is not None
            self.assertGreater(abs(via.transform.translation[1]), 0.6)

    def test_common_is_on_gnd_and_the_structure_is_netted_in(self) -> None:
        def members(net: Net) -> set[int]:
            return {id(p) for p in net.connected}

        self.assertEqual(self.c.gnd.name, "GND")
        self.assertEqual(members(self.c.gnd), {id(self.c.vs.COMMON)})
        line_in, line_out = self.c.SIG_DRV, self.c.SIG_RCV
        self.assertEqual(members(line_in), {id(self.c.drv.io), id(self.c.vs.sig_in)})
        self.assertEqual(members(line_out), {id(self.c.vs.sig_out), id(self.c.rcv.io)})

    def test_routes_reach_the_signal_via_on_each_layer(self) -> None:
        hops = {
            (frozenset((r.source, r.destination)), r.layer)
            for r in extract(self.c, Route)
        }
        via = self.c.vs.signal_via
        self.assertEqual(
            hops,
            {
                (frozenset((self.c.drv.io, via)), 0),
                (frozenset((via, self.c.rcv.io)), 1),
            },
        )

    def test_constraint_names_the_outer_pads(self) -> None:
        (topo,) = self.c.line_cst.topologies
        self.assertIs(topo.begin, self.c.drv.io)
        self.assertIs(topo.end, self.c.rcv.io)

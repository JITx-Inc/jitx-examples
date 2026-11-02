"""Tests for the series-part SI pattern.

The shape jitx-interconnect-constraints points at: two ordinary nets either
side of a series resistor, a ``BridgingPinModel`` between the resistor's two
ports, a constraint on the driver and receiver pads (the true ends, not the
resistor), and code routes on each side. The model's values and the
resistor's orientation are pinned because the docstring's measurement
depends on them. The runtime measurement is in the module docstring.
"""

from __future__ import annotations

from jitx.circuit import Route
from jitx.inspect import extract
from jitx.net import TopologyNet
from jitx.si import BridgingPinModel, Constrain
from jitx.test import TestCase

from jitxexamples.patterns.si_series_part import SeriesPart, SeriesPartDesign


class TestSeriesPart(TestCase):
    def setUp(self) -> None:
        circuit = SeriesPartDesign().circuit
        assert isinstance(circuit, SeriesPart)
        self.c = circuit

    def test_resistor_bridges_its_two_ports(self) -> None:
        (model,) = extract(self.c, BridgingPinModel)
        self.assertEqual(set(model.ports), {self.c.res.a, self.c.res.b})
        self.assertAlmostEqual(model.delay.typ * 1e12, 4.0)  # ps
        self.assertAlmostEqual(model.loss.typ, 0.08)

    def test_port_a_faces_the_driver(self) -> None:
        # No PadMapping: ports map to pads in declaration order, so ``a`` is
        # on the first pad.
        res = self.c.res
        assert res.transform is not None and self.c.drv.transform is not None
        pads = []
        for pad in res.landpattern.pads:
            assert pad.transform is not None
            pads.append(res.transform * pad.transform)
        pad_a, pad_b = pads
        drv_x = self.c.drv.transform.translation[0]
        self.assertLess(
            abs(pad_a.translation[0] - drv_x), abs(pad_b.translation[0] - drv_x)
        )

    def test_constraint_spans_the_resistor_end_to_end(self) -> None:
        (cst,) = extract(self.c, Constrain)
        (topo,) = cst.topologies
        self.assertIs(topo.begin, self.c.drv.io)
        self.assertIs(topo.end, self.c.rcv.io)

    def test_routes_close_each_side_without_topology_net(self) -> None:
        hops = {frozenset((r.source, r.destination)) for r in extract(self.c, Route)}
        self.assertEqual(
            hops,
            {
                frozenset((self.c.drv.io, self.c.res.a)),
                frozenset((self.c.res.b, self.c.rcv.io)),
            },
        )
        self.assertEqual(list(extract(self.c, TopologyNet)), [])

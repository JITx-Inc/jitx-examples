"""Tests for the via-model SI pattern.

The shape jitx-interconnect-constraints points at: a design-local subclass of
the substrate's via that adds ``models`` for the layer pair the signal
crosses, a ``PortAttachment`` putting the via on the line, and one route per
layer through it. The runtime measurement is in the module docstring.
"""

from __future__ import annotations

from jitx.circuit import Route
from jitx.inspect import extract
from jitx.net import PortAttachment
from jitx.sample import SampleSubstrate
from jitx.si import Constrain
from jitx.test import TestCase

from jitxexamples.patterns.si_via_model import (
    ExampleSignalVia,
    ViaModel,
    ViaModelDesign,
)


class TestViaModel(TestCase):
    def setUp(self) -> None:
        circuit = ViaModelDesign().circuit
        assert isinstance(circuit, ViaModel)
        self.c = circuit

    def test_via_subclass_models_the_layer_pair_it_spans(self) -> None:
        self.assertTrue(issubclass(ExampleSignalVia, SampleSubstrate.THVia))
        self.assertEqual(list(ExampleSignalVia.models), [(0, 1)])
        model = ExampleSignalVia.models[(0, 1)]
        self.assertAlmostEqual(model.delay.typ * 1e12, 6.0)  # ps
        self.assertAlmostEqual(model.loss.typ, 0.04)

    def test_via_is_attached_to_the_line(self) -> None:
        (attachment,) = extract(self.c, PortAttachment)
        self.assertIs(attachment.port, self.c.drv.io)
        self.assertIs(attachment.attachment, self.c.via)

    def test_one_route_per_layer_through_the_via(self) -> None:
        hops = {
            (frozenset((r.source, r.destination)), r.layer)
            for r in extract(self.c, Route)
        }
        self.assertEqual(
            hops,
            {
                (frozenset((self.c.drv.io, self.c.via)), 0),
                (frozenset((self.c.via, self.c.rcv.io)), 1),
            },
        )

    def test_constraint_names_the_outer_pads(self) -> None:
        (cst,) = extract(self.c, Constrain)
        (topo,) = cst.topologies
        self.assertIs(topo.begin, self.c.drv.io)
        self.assertIs(topo.end, self.c.rcv.io)

"""Tests for the point-to-point SI pattern.

The pattern's shape, which jitx-interconnect-constraints points at: one
ordinary net (no ``>>``), a ``Constrain`` on the two pads with timing, loss
and a single-ended structure, a ``TerminatingPinModel`` on the receiver's
pin, and one code route that closes the path. The tests read the
instantiated design; the runtime measurement is in the module docstring.
Private ``_constraints`` and ``_structure`` are read because ``Constrain``
exposes its limits no other way.
"""

from __future__ import annotations

from jitx.circuit import Route
from jitx.inspect import extract
from jitx.net import TopologyNet
from jitx.sample import SampleSubstrate
from jitx.si import (
    Constrain,
    InsertionLossConstraint,
    TerminatingPinModel,
    TimingConstraint,
)
from jitx.test import TestCase

from jitxexamples.patterns.si_point_to_point import PointToPoint, PointToPointDesign


class TestPointToPoint(TestCase):
    def setUp(self) -> None:
        circuit = PointToPointDesign().circuit
        assert isinstance(circuit, PointToPoint)
        self.c = circuit

    def test_constraint_names_the_two_pads_with_limits_and_structure(self) -> None:
        (cst,) = extract(self.c, Constrain)
        (topo,) = cst.topologies
        self.assertIs(topo.begin, self.c.drv.io)
        self.assertIs(topo.end, self.c.rcv.io)
        kinds = {type(k) for k in cst._constraints}
        self.assertEqual(kinds, {TimingConstraint, InsertionLossConstraint})
        assert cst._structure is not None
        self.assertIs(cst._structure.structure, SampleSubstrate.RS_50)

    def test_receiver_pin_carries_a_terminating_model(self) -> None:
        (model,) = extract(self.c, TerminatingPinModel)
        self.assertIs(model.port, self.c.rcv.io)
        self.assertAlmostEqual(model.delay.typ * 1e12, 10.0)  # ps
        self.assertAlmostEqual(model.loss.typ, 0.2)

    def test_one_code_route_closes_the_path_without_topology_net(self) -> None:
        (route,) = extract(self.c, Route)
        self.assertEqual(
            {route.source, route.destination}, {self.c.drv.io, self.c.rcv.io}
        )
        self.assertEqual(list(extract(self.c, TopologyNet)), [])

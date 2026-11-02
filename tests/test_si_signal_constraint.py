"""Tests for the SignalConstraint SI pattern.

The shape jitx-interconnect-constraints points at: a ``SignalConstraint``
subclass whose ``constrain(src, dst)`` applies one stored
``DiffPairConstraint`` across the crossover (each end's ``tx`` to the other
end's ``rx``), applied to the chips' own bundles, with a ``BridgingPinModel``
on each leg of the coupler in the transmit path. The runtime measurement is
in the module docstring.
"""

from __future__ import annotations

from jitx.inspect import extract
from jitx.si import BridgingPinModel, ConstrainDiffPair, DiffPairConstraint
from jitx.test import TestCase

from jitxexamples.patterns.si_signal_constraint import (
    ExampleLinkConstraint,
    SerialLink,
    SerialLinkDesign,
)


class TestSerialLink(TestCase):
    def setUp(self) -> None:
        circuit = SerialLinkDesign().circuit
        assert isinstance(circuit, SerialLink)
        self.c = circuit

    def test_constraint_is_a_subclass_applied_across_the_crossover(self) -> None:
        self.assertIsInstance(self.c.link_cst, ExampleLinkConstraint)
        (helper,) = extract(self.c.link_cst, DiffPairConstraint)
        host, phy = self.c.host.link, self.c.phy.link
        ends = []
        for cst in helper.constrains:
            assert isinstance(cst, ConstrainDiffPair)
            ends += [(t.begin, t.end) for t in cst.topologies]
        self.assertEqual(ends, [(host.tx, phy.rx), (phy.tx, host.rx)])

    def test_coupler_bridges_each_leg(self) -> None:
        cpl = self.c.coupler
        models = list(extract(cpl, BridgingPinModel))
        bridged = {frozenset(m.ports) for m in models}
        self.assertEqual(
            bridged, {frozenset((cpl.a.p, cpl.b.p)), frozenset((cpl.a.n, cpl.b.n))}
        )
        for m in models:
            self.assertAlmostEqual(m.delay.typ * 1e12, 3.0)  # ps
            self.assertAlmostEqual(m.loss.typ, 0.06)

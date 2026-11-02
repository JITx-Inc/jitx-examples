"""Tests for the differential-pair SI pattern.

The shape jitx-interconnect-constraints points at: ``lane0`` constrained by a
``ConstrainDiffPair`` with a skew window, timing, loss and a differential
structure; ``lane1`` by a ``DiffPairConstraint`` helper stored on the
circuit; a code route per leg. The runtime measurement is in the module
docstring. Private ``_pairwise_constraints``, ``_constraints`` and
``_structure`` are read because the constraint classes expose their limits no
other way.
"""

from __future__ import annotations

from jitx.circuit import Route
from jitx.inspect import extract
from jitx.sample import SampleSubstrate
from jitx.si import (
    ConstrainDiffPair,
    DiffPairConstraint,
    InsertionLossConstraint,
    TimingConstraint,
    TimingDifferenceConstraint,
)
from jitx.test import TestCase

from jitxexamples.patterns.si_diff_pair import DiffPairs, DiffPairsDesign


class TestDiffPairs(TestCase):
    def setUp(self) -> None:
        circuit = DiffPairsDesign().circuit
        assert isinstance(circuit, DiffPairs)
        self.c = circuit

    def test_lane0_constraint(self) -> None:
        cst = self.c.lane0_cst
        (topo,) = cst.topologies
        self.assertIs(topo.begin, self.c.tx.lane0)
        self.assertIs(topo.end, self.c.rx.lane0)
        self.assertEqual(
            [type(k) for k in cst._pairwise_constraints], [TimingDifferenceConstraint]
        )
        kinds = {type(k) for k in cst._constraints}
        self.assertEqual(kinds, {TimingConstraint, InsertionLossConstraint})
        assert cst._structure is not None
        self.assertIs(cst._structure.structure, SampleSubstrate.DRS_100)

    def test_lane1_helper_is_stored_and_constrains_lane1(self) -> None:
        (helper,) = extract(self.c, DiffPairConstraint)
        self.assertIs(helper, self.c.lane1_cst)
        (cst,) = helper.constrains
        assert isinstance(cst, ConstrainDiffPair)
        (topo,) = cst.topologies
        self.assertIs(topo.begin, self.c.tx.lane1)
        self.assertIs(topo.end, self.c.rx.lane1)

    def test_every_leg_has_a_code_route(self) -> None:
        hops = {frozenset((r.source, r.destination)) for r in extract(self.c, Route)}
        tx, rx = self.c.tx, self.c.rx
        legs = {
            frozenset((a, b))
            for a, b in (
                (tx.lane0.p, rx.lane0.p),
                (tx.lane0.n, rx.lane0.n),
                (tx.lane1.p, rx.lane1.p),
                (tx.lane1.n, rx.lane1.n),
            )
        }
        self.assertEqual(hops, legs)

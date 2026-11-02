"""Tests for the bundle-skew SI pattern.

The shape jitx-interconnect-constraints points at: a
``ConstrainReferenceDifference`` whose guide is one leg of ``lane0`` and
whose targets are both legs of ``lane1``, and a ``ConstrainDiffPair`` on both
pairs for intra-pair skew and the structure. Also pins that a ``DiffPair``
guide is rejected, the rule the pattern exists to show. The skew windows
are pinned because the docstring's report depends on them; private
``_pairwise_constraints`` is read because the constraint exposes them no
other way. The runtime measurement is in the module docstring.
"""

from __future__ import annotations

from jitx.net import Topology
from jitx.si import TimingDifferenceConstraint
from jitx.test import TestCase

from jitxexamples.patterns.si_bundle_skew import BundleSkew, BundleSkewDesign


class TestBundleSkew(TestCase):
    def setUp(self) -> None:
        circuit = BundleSkewDesign().circuit
        assert isinstance(circuit, BundleSkew)
        self.c = circuit

    def test_guide_is_one_leg_and_targets_are_both_legs_of_the_other_pair(
        self,
    ) -> None:
        tx, rx = self.c.tx, self.c.rx
        cst = self.c.bundle_cst
        self.assertIs(cst.guide.begin, tx.lane0.p)
        self.assertIs(cst.guide.end, rx.lane0.p)
        self.assertEqual(
            [(t.begin, t.end) for t in cst.topologies],
            [(tx.lane1.p, rx.lane1.p), (tx.lane1.n, rx.lane1.n)],
        )

    def test_windows(self) -> None:
        for cst, window_ps in ((self.c.pairs_cst, 2.0), (self.c.bundle_cst, 10.0)):
            (k,) = cst._pairwise_constraints
            assert isinstance(k, TimingDifferenceConstraint)
            self.assertAlmostEqual(k.min_delta * 1e12, -window_ps)
            self.assertAlmostEqual(k.max_delta * 1e12, window_ps)

    def test_both_pairs_carry_intra_pair_skew(self) -> None:
        tx, rx = self.c.tx, self.c.rx
        self.assertEqual(
            [(t.begin, t.end) for t in self.c.pairs_cst.topologies],
            [(tx.lane0, rx.lane0), (tx.lane1, rx.lane1)],
        )

    def test_a_pair_as_guide_is_rejected(self) -> None:
        from jitx.si import ConstrainReferenceDifference

        tx, rx = self.c.tx, self.c.rx
        with self.assertRaisesRegex(ValueError, "Guide must be a single pin type"):
            ConstrainReferenceDifference(
                Topology(tx.lane0, rx.lane0), Topology(tx.lane1.p, rx.lane1.p)
            )

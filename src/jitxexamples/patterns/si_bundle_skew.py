"""Skew across a bundle of differential pairs, with one leg as the guide.

``ConstrainReferenceDifference(guide, topologies)`` checks the delay of each
topology against the guide's. The guide must run between single pins:
passing a pair raises ``ValueError: Guide must be a single pin type``. So
for skew across pairs, one leg of one pair is the guide, here
``Topology(tx.lane0.p, rx.lane0.p)``, and both legs of the other pair are
the targets. The same call matches data lines to a clock or strobe, with the
clock's single-ended path as the guide.

``timing_difference(window)`` is checked as guide delay minus target delay
against the window as written. The printed ``Target`` drops the sign: a
window of -1000 ps to 0 and one of 0 to 1000 ps both print
``500ps ± 500ps``. Read the verdict from ``group.satisfied``, never the
direction from the text.

The pairs also carry a ``ConstrainDiffPair`` for intra-pair skew and the
differential structure. The limits are illustrative.

Checked with the design-issues query, run as a script from a project
root with that project's runtime running
(jitx 4.6.0rc10, runtime 4.6.0-rc.16)::

    import jitx

    from jitxexamples.patterns.si_bundle_skew import BundleSkewDesign


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(BundleSkewDesign).issues(satisfied=True, wait=30)
            if not report.complete:
                print("report incomplete: raise wait and run again")
            for group in report.groups():
                print("met" if group.satisfied else "NOT MET", group.text)
                if len(group.issues) > 1:
                    for issue in group:
                        print("   ", issue.text)


    if __name__ == "__main__":
        main()

It printed::

    met Skew: 0s - Target: ± 2ps (longer from tx.lane0.p to rx.lane0.p, shorter from tx.lane0.n to rx.lane0.n)
    met Skew: 0s - Target: ± 2ps (longer from tx.lane1.p to rx.lane1.p, shorter from tx.lane1.n to rx.lane1.n)
    met Skew: 0s - Target: ± 10ps (longer from tx.lane0.p to rx.lane0.p, shorter from tx.lane1.p to rx.lane1.p)
    met Skew: 0s - Target: ± 10ps (longer from tx.lane0.p to rx.lane0.p, shorter from tx.lane1.n to rx.lane1.n)
    met Satisfied

Each pair's intra-pair skew gives one line, and the bundle constraint one
line per compared leg: two here, ``lane0.p`` against ``lane1.p`` and against
``lane1.n``.

The last line is the Routing category's group: every code route was made.
It is not a constraint verdict.
"""

from __future__ import annotations

from jitx.circuit import Circuit, Route
from jitx.net import Topology
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.si import ConstrainDiffPair, ConstrainReferenceDifference

from jitxexamples.patterns.si_parts import ExampleTwoLaneChip


class BundleSkew(Circuit):
    """Two differential lanes matched to each other, with one leg of
    ``lane0`` as the guide."""

    def __init__(self) -> None:
        self.tx = ExampleTwoLaneChip().at(-10, 0)
        self.rx = ExampleTwoLaneChip().at(10, 0)

        self.lanes = [self.tx.lane0 + self.rx.lane0, self.tx.lane1 + self.rx.lane1]
        self.routes = [
            Route(src, dst, layer=0)
            for src, dst in (
                (self.tx.lane0.p, self.rx.lane0.p),
                (self.tx.lane0.n, self.rx.lane0.n),
                (self.tx.lane1.p, self.rx.lane1.p),
                (self.tx.lane1.n, self.rx.lane1.n),
            )
        ]

        self.pairs_cst = (
            ConstrainDiffPair(
                [
                    Topology(self.tx.lane0, self.rx.lane0),
                    Topology(self.tx.lane1, self.rx.lane1),
                ]
            )
            .timing_difference(2e-12)
            .structure(SampleSubstrate.DRS_100)
        )

        # The guide is one pin: a DiffPair guide raises "Guide must be a single
        # pin type".
        self.bundle_cst = ConstrainReferenceDifference(
            Topology(self.tx.lane0.p, self.rx.lane0.p),
            [
                Topology(self.tx.lane1.p, self.rx.lane1.p),
                Topology(self.tx.lane1.n, self.rx.lane1.n),
            ],
        ).timing_difference(10e-12)


class BundleSkewDesign(SampleDesign):
    """The matched lanes on the sample board."""

    circuit = BundleSkew()

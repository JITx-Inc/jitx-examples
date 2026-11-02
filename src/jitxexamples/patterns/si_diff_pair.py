"""Intra-pair skew on differential pairs, in the two forms ``jitx.si`` offers.

Two lanes run straight between two fictional chips. ``self.tx.lane0 +
self.rx.lane0`` is one bundle net: it joins ``p`` to ``p`` and ``n`` to
``n``. Each leg gets its own code ``Route``.

``lane0`` is constrained with ``ConstrainDiffPair(Topology(tx.lane0,
rx.lane0))``: ``timing_difference(2e-12)`` is the P-to-N skew window,
``timing`` and ``insertion_loss`` apply to each leg, and
``.structure(SampleSubstrate.DRS_100)`` takes a ``DifferentialRoutingStructure``
(``Constrain.structure`` takes only a single-ended one).

``lane1`` uses ``DiffPairConstraint``, a reusable ``SignalConstraint`` that
holds a skew window, a loss limit and a structure and applies them each time
``constrain(src, dst)`` is called. It sets no delay limit, so its lane gets
``Loss`` and ``Skew`` lines and no ``Time``. Store the helper on ``self``
before calling ``constrain``; an unstored helper is lost during
instantiation.

The limits are illustrative.

Checked with the design-issues query, run as a script from a project
root with that project's runtime running
(jitx 4.6.0rc10, runtime 4.6.0-rc.16)::

    import jitx

    from jitxexamples.patterns.si_diff_pair import DiffPairsDesign


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(DiffPairsDesign).issues(satisfied=True, wait=30)
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

    met Time: 104.529ps - Target: 500ps ± 500ps from tx.lane0.p to rx.lane0.p
    met Time: 104.529ps - Target: 500ps ± 500ps from tx.lane0.n to rx.lane0.n
    met Loss: 0.356db - Target: 0.5db ± 0.5db from tx.lane0.p to rx.lane0.p
    met Loss: 0.356db - Target: 0.5db ± 0.5db from tx.lane0.n to rx.lane0.n
    met Loss: 0.356db - Target: 0.5db ± 0.5db from tx.lane1.p to rx.lane1.p
    met Loss: 0.356db - Target: 0.5db ± 0.5db from tx.lane1.n to rx.lane1.n
    met Skew: 0s - Target: ± 2ps (longer from tx.lane0.p to rx.lane0.p, shorter from tx.lane0.n to rx.lane0.n)
    met Skew: 0s - Target: ± 2ps (longer from tx.lane1.p to rx.lane1.p, shorter from tx.lane1.n to rx.lane1.n)
    met Satisfied

Timing and loss give one line per leg; the skew gives one ``Skew`` line per
pair, naming the longer and the shorter leg. Equal straight routes measure
``0s``.

The last line is the Routing category's group: every code route was made.
It is not a constraint verdict.
"""

from __future__ import annotations

from jitx.circuit import Circuit, Route
from jitx.net import Topology
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.si import ConstrainDiffPair, DiffPairConstraint
from jitx.toleranced import Toleranced

from jitxexamples.patterns.si_parts import ExampleTwoLaneChip


class DiffPairs(Circuit):
    """Two differential lanes between two chips: one constrained with
    ``ConstrainDiffPair``, one with the reusable ``DiffPairConstraint``."""

    def __init__(self) -> None:
        self.tx = ExampleTwoLaneChip().at(-10, 0)
        self.rx = ExampleTwoLaneChip().at(10, 0)

        # A bundle net joins each leg: lane0.p to lane0.p, lane0.n to lane0.n.
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

        self.lane0_cst = (
            ConstrainDiffPair(Topology(self.tx.lane0, self.rx.lane0))
            .timing_difference(2e-12)
            .timing(1e-9)
            .insertion_loss(1.0)
            .structure(SampleSubstrate.DRS_100)
        )

        self.lane1_cst = DiffPairConstraint(
            skew=Toleranced(0, 2e-12), loss=1.0, structure=SampleSubstrate.DRS_100
        )
        self.lane1_cst.constrain(self.tx.lane1, self.rx.lane1)


class DiffPairsDesign(SampleDesign):
    """The two lanes on the sample board."""

    circuit = DiffPairs()

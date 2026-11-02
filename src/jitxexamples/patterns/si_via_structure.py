"""A layer change through a via structure from ``jitxlib.via_structures``, on
ordinary nets.

``SingleViaStructure`` is a ``Circuit`` with ``sig_in``, ``sig_out`` and
``COMMON`` ports around one signal via, here
:py:class:`~jitxexamples.patterns.si_via_model.ExampleSignalVia`, which
carries the via's ``models``. ``PolarViaGroundCage`` rings it with four of
the substrate's through vias at 1.5 mm, on the net that ``COMMON`` joins
(``GND``). The structure nets in like a part, the routes run to its
``signal_via`` on each layer, and the constraint names the outer pads, not
the structure's ports.

``theta=45`` turns the cage so no cage via sits on the straight run into the
signal via. The cage must leave the routes a way in: one that closes the via
off makes the code routes fail (``Unable to find path for requested route``)
and the constraint reports ``Missing Connection on Path``. Size the cage for
the trace and clearance, or leave a gap with ``skips=``.

The measurement counts the signal via's model: 110.529 ps, the same as the
uncaged via in :py:mod:`~jitxexamples.patterns.si_via_model`. The limits are
illustrative.

Checked with the design-issues query, run as a script from a project
root with that project's runtime running
(jitx 4.6.0rc10, runtime 4.6.0-rc.16)::

    import jitx

    from jitxexamples.patterns.si_via_structure import CagedViaDesign


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(CagedViaDesign).issues(satisfied=True, wait=30)
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

    met Time: 110.529ps - Target: 500ps ± 500ps from drv.io to rcv.io
    met Loss: 0.396db ± 0db - Target: 0.5db ± 0.5db from drv.io to rcv.io
    met Satisfied

``DifferentialViaStructure(vias, pitch, ground_cages=..., antipads=...)`` is
the pair form: ``DiffPair`` ports and signal vias ``via_p`` and ``via_n``.
Neither class takes an ``insertion_points`` argument.

The last line is the Routing category's group: every code route was made.
It is not a constraint verdict.
"""

from __future__ import annotations

from jitx.circuit import Circuit, Route
from jitx.layerindex import Side
from jitx.net import Net, Topology
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.si import Constrain
from jitxlib.via_structures import PolarViaGroundCage, SingleViaStructure

from jitxexamples.patterns.si_parts import ExampleChip
from jitxexamples.patterns.si_via_model import ExampleSignalVia


class CagedVia(Circuit):
    """A single-ended line that changes layer through a caged signal via."""

    def __init__(self) -> None:
        self.drv = ExampleChip().at(-10, 0)
        self.rcv = ExampleChip().at(10, 0, on=Side.Bottom)
        self.vs = SingleViaStructure(
            ExampleSignalVia,
            ground_cages=[
                PolarViaGroundCage(SampleSubstrate.THVia, count=4, radius=1.5, theta=45)
            ],
            antipads=[],
        ).at(0, 0)

        self.gnd = Net([self.vs.COMMON], name="GND")
        self.SIG_DRV = self.drv.io + self.vs.sig_in
        self.SIG_RCV = self.vs.sig_out + self.rcv.io
        self.routes = [
            Route(self.drv.io, self.vs.signal_via, layer=0),
            Route(self.vs.signal_via, self.rcv.io, layer=1),
        ]

        self.line_cst = (
            Constrain(Topology(self.drv.io, self.rcv.io))
            .timing(1e-9)
            .insertion_loss(1.0)
            .structure(SampleSubstrate.RS_50)
        )


class CagedViaDesign(SampleDesign):
    """The caged-via line on the sample board."""

    circuit = CagedVia()

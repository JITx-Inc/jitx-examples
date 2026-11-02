"""Point-to-point timing and loss on a single-ended line.

A driver pad joins a receiver pad on one ordinary net. The constraint names
the two pads with ``Topology(begin, end)``; it connects nothing, and no ``>>``
is needed. ``Constrain(...).timing(1e-9).insertion_loss(1.0)`` sets the
limits, and ``.structure(SampleSubstrate.RS_50)`` puts the timed path on a
single-ended routing structure. Without a structure the constraint still
measures, but with a delay and loss that are not the structure's, and the
report adds ``Missing routing structure on Path: ...`` per segment.

The receiver, :py:class:`~jitxexamples.patterns.si_parts.ExampleTerminatedChip`,
carries a ``TerminatingPinModel`` on its pin, so the measurement runs into the
die: the package model's 10 ps and 0.2 dB are added. This line measures
114.529 ps and 0.556 dB; the same 20 mm span with no package model measures
104.529 ps and 0.356 dB (the lanes in
:py:mod:`~jitxexamples.patterns.si_diff_pair`). The limits and the model's
values are illustrative, not from a standard or a datasheet.

The runtime infers the path from routed copper, so one code ``Route`` closes
it. Before routing there is nothing to measure: a copy of this line with no
route (and no package model) reported only
``Unconnected Topology on Path: drv.io, rcv.io``.

Every object the design needs is stored on ``self``: the net, the route and
the constraint. One that is built and not stored logs ``lost during
instantiation`` and never reaches the report.

Checked with the design-issues query, run as a script from a project
root with that project's runtime running
(jitx 4.6.0rc10, runtime 4.6.0-rc.16)::

    import jitx

    from jitxexamples.patterns.si_point_to_point import PointToPointDesign


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(PointToPointDesign).issues(satisfied=True, wait=30)
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

    met Time: 114.529ps - Target: 500ps ± 500ps from drv.io to rcv.io
    met Loss: 0.556db - Target: 0.5db ± 0.5db from drv.io to rcv.io
    met Satisfied

Each limit gives one line per path: ``timing`` a ``Time``, ``insertion_loss``
a ``Loss``. A limit is printed as a window: ``timing(1e-9)`` reads
``500ps ± 500ps``, anything from 0 to 1 ns. ``met`` comes from
``group.satisfied``, the only verdict; the text reads the same met or unmet.

The last line is the Routing category's group: every code route was made.
It is not a constraint verdict.
"""

from __future__ import annotations

from jitx.circuit import Circuit, Route
from jitx.net import Topology
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.si import Constrain

from jitxexamples.patterns.si_parts import ExampleChip, ExampleTerminatedChip


class PointToPoint(Circuit):
    """One single-ended line from a driver pad to a packaged receiver,
    constrained for delay and loss, and closed by one code route."""

    def __init__(self) -> None:
        self.drv = ExampleChip().at(-10, 0)
        self.rcv = ExampleTerminatedChip().at(10, 0)

        self.line = self.drv.io + self.rcv.io
        self.route = Route(self.drv.io, self.rcv.io, layer=0)

        self.line_cst = (
            Constrain(Topology(self.drv.io, self.rcv.io))
            .timing(1e-9)
            .insertion_loss(1.0)
            .structure(SampleSubstrate.RS_50)
        )


class PointToPointDesign(SampleDesign):
    """The point-to-point line on the sample board."""

    circuit = PointToPoint()

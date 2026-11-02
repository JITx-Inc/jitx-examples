"""A daisy chain whose order is part of the design, declared with ``>>``.

A clock driver feeds ``load0`` and then ``load1``, as on a flyby clock or
address bus. ``self.drv.io >> self.load0.io >> self.load1.io`` builds a
``TopologyNet``, which records that order before anything is routed. Store
it like any net. ``>>`` is for this case only; a point-to-point constraint
needs ordinary nets.

The code routes run in chain order, driver to ``load0`` to ``load1``, so the
second path runs through the first load. One ``Constrain`` over both
topologies limits the delay to each load, and the routing structure is
applied once, by a structure-only constraint over the longest path
(``drv.io`` to ``load1.io``). That one structure covers the shorter path
too: no ``Missing routing structure`` line appears for it.

Putting a second structure on the shared ``drv.io`` to ``load0.io`` segment
broke the report: with an extra
``Constrain(Topology(drv.io, load0.io)).structure(RS_50)`` the same design
printed::

    NOT MET Ambiguous routing structures meet at load0.io (2 alternatives)
    met Time: 62.717ps - Target: 500ps ± 500ps from drv.io to load0.io
    met Time: 125.434ps - Target: 500ps ± 500ps from drv.io to load1.io
    NOT MET Overlapping routing structures along path from drv.io to load0.io (1 overlapped)
    met Satisfied

The limits are illustrative.

Checked with the design-issues query, run as a script from a project
root with that project's runtime running
(jitx 4.6.0rc10, runtime 4.6.0-rc.16)::

    import jitx

    from jitxexamples.patterns.si_daisy_chain import DaisyChainDesign


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(DaisyChainDesign).issues(satisfied=True, wait=30)
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

    met Time: 62.717ps - Target: 500ps ± 500ps from drv.io to load0.io
    met Time: 125.434ps - Target: 500ps ± 500ps from drv.io to load1.io
    met Satisfied

The structure-only constraint prints nothing, satisfied or not; its code is
the evidence that it applied. A copy of this design with the chain as a plain
``Net([drv.io, load0.io, load1.io])``, the same routes and the same
constraints, printed the same two ``Time`` lines (62.717 ps and 125.434 ps)
and met: on code routes, the routes fix the order. How the autorouter treats a chain with or
without ``>>`` has not been checked; this pattern routes from code only.

The last line is the Routing category's group: every code route was made.
It is not a constraint verdict.
"""

from __future__ import annotations

from jitx.circuit import Circuit, Route
from jitx.net import Topology
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.si import Constrain

from jitxexamples.patterns.si_parts import ExampleChip


class DaisyChain(Circuit):
    """A clock driver feeding two loads in a fixed order."""

    def __init__(self) -> None:
        self.drv = ExampleChip().at(-12, 0)
        self.load0 = ExampleChip().at(0, 0)
        self.load1 = ExampleChip().at(12, 0)

        self.clk = self.drv.io >> self.load0.io >> self.load1.io
        self.routes = [
            Route(self.drv.io, self.load0.io, layer=0),
            Route(self.load0.io, self.load1.io, layer=0),
        ]

        self.clk_timing = Constrain(
            [Topology(self.drv.io, self.load0.io), Topology(self.drv.io, self.load1.io)]
        ).timing(1e-9)
        self.clk_structure = Constrain(Topology(self.drv.io, self.load1.io)).structure(
            SampleSubstrate.RS_50
        )


class DaisyChainDesign(SampleDesign):
    """The daisy chain on the sample board."""

    circuit = DaisyChain()

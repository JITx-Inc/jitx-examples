"""A single-ended path that changes layer through a via with ``models``.

The driver sits on the top side and the receiver on the bottom side of the
two-layer sample board. The signal leaves the driver on layer 0, drops
through a through via and reaches the receiver on layer 1.
:py:class:`ExampleSignalVia` subclasses the substrate's ``THVia`` and adds
``models = {(0, 1): PinModel(delay=6e-12, loss=0.04)}``, keyed by the layer
pair the signal crosses (illustrative values). The substrate declares the
via class; a design-local subclass adds the models when a constrained path
goes through it.

``PortAttachment(self.drv.io, self.via)`` puts the via on the driver's net,
and the two routes, one per layer, close the path through it. The constraint
still names the driver and receiver pads.

The via adds its model to the measurement: 110.529 ps here, 6 ps more than
the same span on one layer (104.529 ps in
:py:mod:`~jitxexamples.patterns.si_diff_pair`). The same circuit with the
substrate's bare ``THVia`` still measured, 124.529 ps and 0.506 dB, but with
a placeholder model, and each measurement group carried::

    Structure model from [0] to [1] not found in "THVia". Using placeholder model for proxy of drv.io.

That group is reported ``NOT MET`` although its number is in range: the
placeholder is not the via's data.

Checked with the design-issues query, run as a script from a project
root with that project's runtime running
(jitx 4.6.0rc10, runtime 4.6.0-rc.16)::

    import jitx

    from jitxexamples.patterns.si_via_model import ViaModelDesign


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(ViaModelDesign).issues(satisfied=True, wait=30)
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

The limits are illustrative.

The last line is the Routing category's group: every code route was made.
It is not a constraint verdict.
"""

from __future__ import annotations

from jitx.circuit import Circuit, Route
from jitx.layerindex import Side
from jitx.net import PortAttachment, Topology
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.si import Constrain, PinModel

from jitxexamples.patterns.si_parts import ExampleChip


class ExampleSignalVia(SampleSubstrate.THVia):
    """The sample board's through via, with a model for a signal that crosses
    it from layer 0 to layer 1. The 6 ps and 0.04 dB are illustrative; a real
    via takes them from an EM simulation or a measurement."""

    models = {(0, 1): PinModel(delay=6e-12, loss=0.04)}


class ViaModel(Circuit):
    """A single-ended line that changes layer through one modeled via."""

    def __init__(self) -> None:
        self.drv = ExampleChip().at(-10, 0)
        self.rcv = ExampleChip().at(10, 0, on=Side.Bottom)
        self.via = ExampleSignalVia().at(0, 0)

        self.line = self.drv.io + self.rcv.io
        self.via_on_line = PortAttachment(self.drv.io, self.via)
        self.routes = [
            Route(self.drv.io, self.via, layer=0),
            Route(self.via, self.rcv.io, layer=1),
        ]

        self.line_cst = (
            Constrain(Topology(self.drv.io, self.rcv.io))
            .timing(1e-9)
            .insertion_loss(1.0)
            .structure(SampleSubstrate.RS_50)
        )


class ViaModelDesign(SampleDesign):
    """The two-layer line on the sample board."""

    circuit = ViaModel()

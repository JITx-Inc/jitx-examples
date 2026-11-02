"""A single-ended path through a series part, with a ``BridgingPinModel``.

The driver feeds a series resistor whose far side feeds the receiver: two
ordinary nets, one on each side of the part. The constraint names the driver
and receiver pads, the true ends, and the runtime follows the path across
the resistor because
:py:class:`~jitxexamples.patterns.si_parts.ExampleSeriesResistor` carries a
``BridgingPinModel`` between ``a`` and ``b`` (4 ps and 0.08 dB, illustrative).
When the part's own class has no model, add one in the circuit instead:
``self.res_model = BridgingPinModel(self.res.a, self.res.b, delay=..., loss=...)``,
with the values from its datasheet or the user.

The same circuit with a resistor that has no pin model reported no
measurement, only::

    NOT MET No path for signal constraint from drv.io to rcv.io: the ends are only connected through the part between res.a and res.b, which has no pin model. If the signal is meant to pass through it, give it a pin model between them; otherwise check the wiring.

A ``BridgingPinModel`` belongs only on a part with a path through it between
two pins: a series resistor, an AC coupling capacitor, an ESD channel whose
datasheet gives an in-to-out path. A flow-through package whose opposite pin
is not connected inside gets none: its two lands are one net joined by board
copper, and a model there would hide an open line.

The resistor is rotated 270 degrees so ``a`` faces the driver. A code route
the router cannot make reports ``Missing Connection on Path`` and the
constraint does not measure.

Checked with the design-issues query, run as a script from a project
root with that project's runtime running
(jitx 4.6.0rc10, runtime 4.6.0-rc.16)::

    import jitx

    from jitxexamples.patterns.si_series_part import SeriesPartDesign


    def main() -> None:
        with jitx.runtime as rt:
            report = rt.submit(SeriesPartDesign).issues(satisfied=True, wait=30)
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

    met Time: 103.302ps - Target: 500ps ± 500ps from drv.io to rcv.io
    met Loss: 0.418db - Target: 0.5db ± 0.5db from drv.io to rcv.io
    met Satisfied

The measured span covers both routes and the resistor's model. The limits
are illustrative.

The last line is the Routing category's group: every code route was made.
It is not a constraint verdict.
"""

from __future__ import annotations

from jitx.circuit import Circuit, Route
from jitx.net import Topology
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.si import Constrain

from jitxexamples.patterns.si_parts import ExampleChip, ExampleSeriesResistor


class SeriesPart(Circuit):
    """A single-ended line that passes through a series resistor, constrained
    end to end across it."""

    def __init__(self) -> None:
        self.drv = ExampleChip().at(-10, 0)
        self.res = ExampleSeriesResistor().at(0, 0, rotate=270)
        self.rcv = ExampleChip().at(10, 0)

        self.line_in = self.drv.io + self.res.a
        self.line_out = self.res.b + self.rcv.io
        self.routes = [
            Route(self.drv.io, self.res.a, layer=0),
            Route(self.res.b, self.rcv.io, layer=0),
        ]

        self.line_cst = (
            Constrain(Topology(self.drv.io, self.rcv.io))
            .timing(1e-9)
            .insertion_loss(1.0)
            .structure(SampleSubstrate.RS_50)
        )


class SeriesPartDesign(SampleDesign):
    """The series-part line on the sample board."""

    circuit = SeriesPart()

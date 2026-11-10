"""Apply routing structures by tag, with a neck structure on the escape.

Use this pattern when a class of nets takes a routing structure and the
segment that leaves the device needs a narrower one. Two rules do it, and
neither needs ``>>`` or ``Constrain(...).structure``:

1. ``design_constraint(SignalTag(), priority=2).routing_structure(main,
   ref_net=GND)`` on the net's tag applies the main structure to every trace
   of the net.
2. ``design_constraint(EscapeNeckTag(), priority=4).routing_structure(neck,
   ref_net=GND)`` on a tag assigned to the escape ``Route`` object gives that
   segment the neck structure. The higher priority wins on the one segment
   both rules match.

The net is split at a transition: the escape route runs from the device pad
to a code-placed via, and the main route from the via to the far pad. A
``Constrain(Topology(...)).timing(...)`` on the pad-to-pad path asks for a
structure on every segment, so a segment without one shows in the design
issues as ``Missing routing structure``.

Measured on jitx 4.6, building :py:class:`layout_routing_structure_by_tag_design`:
the escape came back 0.15 wide and the main segment 0.3, the widths of the
two structures, and the issues listed the path's ``Time`` line with no
``Missing routing structure``. The same mechanism on 0.4 and 0.15
structures, measured on jitx 4.6, showed that a tag on the net combined with
``IsTrace`` instead of a tag on the ``Route`` necks the whole net, not the
escape.

When ``Constrain(...).structure(...)`` and a ``routing_structure`` rule both
apply to one net, the rule's structure wins, and nothing reports the
overlap (measured on jitx 4.6). Pick one place to apply a structure.

Build structures inside a circuit's ``__init__`` or as class attributes of a
``Substrate``. Built at module level, a ``RoutingStructure`` fails inside
``routing_structure(...)`` with ``TypeError: 'Instantiable' object is not
iterable``. The widths here are illustrative, not solved for an impedance.

The test, ``tests/test_layout_routing_structure_by_tag.py``, checks the
rules' conditions offline. With ``JITX_PATTERN_RUNTIME=1`` and a runtime
started at the project root, it builds the design and measures each
segment's width and reads the issues.
"""

from __future__ import annotations

from jitx.circuit import Circuit, Route
from jitx.constraints import Tag, design_constraint
from jitx.copper import Pour
from jitx.net import Net, Topology
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.shapes.composites import rectangle
from jitx.si import Constrain, RoutingStructure

from jitxexamples.patterns.si_parts import ExampleChip

MAIN_WIDTH = 0.3
"""Trace width of the main structure, in mm."""

NECK_WIDTH = 0.15
"""Trace width of the neck structure on the escape, in mm."""

TRANSITION_X = -7.0
"""Where the escape ends and the main segment starts, in mm."""


class SignalTag(Tag):
    """Nets that take the main structure."""


class EscapeNeckTag(Tag):
    """Escape segments that take the neck structure."""


def _structure(name: str, width: float) -> RoutingStructure:
    return RoutingStructure(
        {
            0: RoutingStructure.Layer(
                trace_width=width, clearance=0.2, velocity=150e9, insertion_loss=0.01
            )
        },
        impedance=50,
        name=name,
    )


class NeckedLine(Circuit):
    """One net from a device pad to a far pad, necked on the escape."""

    def __init__(self) -> None:
        self.main = _structure("MAIN", MAIN_WIDTH)
        self.neck = _structure("NECK", NECK_WIDTH)

        self.device = ExampleChip().at(-10, 0)
        self.far = ExampleChip().at(10, 0)
        self.transition = SampleSubstrate.THVia().at(TRANSITION_X, 0)
        self.sig = Net([self.device.io, self.far.io], name="SIG")
        self.sig += self.transition
        SignalTag().assign(self.sig)

        self.escape = Route(self.device.io, self.transition, layer=0)
        self.run = Route(self.transition, self.far.io, layer=0)
        EscapeNeckTag().assign(self.escape)

        self.timing = Constrain(Topology(self.device.io, self.far.io)).timing(1e-9)

        self.gnd = Net(name="GND")
        self.plane = Pour(rectangle(30, 10), layer=1)
        self.anchor = SampleSubstrate.THVia().at(0, 3)
        self.gnd += self.plane
        self.gnd += self.anchor

        self.main_rule = design_constraint(SignalTag(), priority=2).routing_structure(
            self.main, ref_net=self.gnd
        )
        self.neck_rule = design_constraint(
            EscapeNeckTag(), priority=4
        ).routing_structure(self.neck, ref_net=self.gnd)


class layout_routing_structure_by_tag_design(SampleDesign):
    """The necked line on the sample board."""

    circuit = NeckedLine()

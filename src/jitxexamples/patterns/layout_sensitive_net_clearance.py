"""Keep an RF line away from a switch node with a clearance between the
tags on two nets.

Use this pattern when a sensitive net needs more room from one noisy net
than from everything else. The rule names both tags:
``design_constraint(RFTag(), NoisyTag()).clearance(RF_TO_NOISY)``. It
applies only between copper carrying the two tags, so the RF line keeps the
default spacing to every other net. A rule against ``AnyObject``, such as
``clearance(RFTag(), AnyObject)``, pushes everything away, including the
coplanar ground an RF line needs (see ``layout_cpwg_two_row_fence``).

The design runs one RF line on layer 0 between two pads 30 mm apart. On its
way it crosses two pours on layer 0: a switch-node pour, standing in for a
converter's switch-node copper, and a GND pour. Each pour is split in two by
the line, and each half has its own same-net via, so neither half is removed
as an island.

Measured on jitx 4.6, building
:py:class:`layout_sensitive_net_clearance_design`, with a 1.0 mm rule:

- the switch-node pour stood 1.01 mm from the line's edge on both sides,
  the rule plus 0.01 mm;
- the GND pour stood 0.137 mm from it, the pullback measured on jitx 4.6
  from a trace with no clearance rule;
- both halves of each pour stayed, and the issues listed routing as
  satisfied.

The ``NoisyTag`` sits on the ``SW`` net, not on the pour, and the pour took
the rule. A tag on a net reaches all of that net's copper: its traces,
pours, code-placed vias and pads. So the same rule applies between the RF
line and a switch-node via or pad. This design has two switch-node vias,
the pour's anchors, whose 0.45 mm pads sit about 1.7 mm from the line's
edge, outside the 1.0 mm rule, and no switch-node pad; what it measures is
the pour's voids around the line.

The test, ``tests/test_layout_sensitive_net_clearance.py``, checks the rule
and the tags offline. With ``JITX_PATTERN_RUNTIME=1`` and a runtime started
at the project root, it builds the design and measures how far each pour
pulls back from the line.
"""

from __future__ import annotations

from jitx.circuit import Circuit, Route
from jitx.constraints import Tag, design_constraint
from jitx.copper import Pour
from jitx.net import Net
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.shapes.composites import rectangle

from jitxexamples.patterns.layout_cpwg_two_row_fence import RFEndpoint

RF_TO_NOISY = 1.0
"""Clearance between RF copper and switch-node copper, in mm."""

LINE_LENGTH = 30.0
"""Distance between the RF pads' centres, in mm."""

POUR_SIZE = (8.0, 6.0)
"""Each pour's width and height, in mm."""

SW_POUR_X = -6.0
"""The switch-node pour's centre on the line, in mm."""

GND_POUR_X = 6.0
"""The GND pour's centre on the line, in mm."""

ANCHOR_Y = 2.0
"""The pours' anchor vias sit this far above and below the line, in mm."""


class RFTag(Tag):
    """Sensitive RF nets."""


class NoisyTag(Tag):
    """Noisy nets, such as a converter's switch node."""


class RFNearSwitchNode(Circuit):
    """An RF line crossing a switch-node pour and a GND pour."""

    def __init__(self) -> None:
        half = LINE_LENGTH / 2
        self.source = RFEndpoint().at(-half, 0)
        self.load = RFEndpoint().at(half, 0)
        self.rf = Net([self.source.rf, self.load.rf], name="RF")
        RFTag().assign(self.rf)
        self.route = Route(self.source.rf, self.load.rf, layer=0)

        self.sw = Net(name="SW")
        self.sw_pour = Pour(rectangle(*POUR_SIZE).at(SW_POUR_X, 0), layer=0)
        self.sw_anchors = [
            SampleSubstrate.THVia().at(SW_POUR_X, y) for y in (ANCHOR_Y, -ANCHOR_Y)
        ]
        self.sw += self.sw_pour
        for via in self.sw_anchors:
            self.sw += via
        NoisyTag().assign(self.sw)

        self.gnd = Net(name="GND")
        self.gnd_pour = Pour(rectangle(*POUR_SIZE).at(GND_POUR_X, 0), layer=0)
        self.gnd_anchors = [
            SampleSubstrate.THVia().at(GND_POUR_X, y) for y in (ANCHOR_Y, -ANCHOR_Y)
        ]
        self.gnd += self.gnd_pour
        for via in self.gnd_anchors:
            self.gnd += via

        self.rf_to_noisy = design_constraint(RFTag(), NoisyTag()).clearance(RF_TO_NOISY)


class layout_sensitive_net_clearance_design(SampleDesign):
    """The RF line and the two pours on the sample board."""

    circuit = RFNearSwitchNode()

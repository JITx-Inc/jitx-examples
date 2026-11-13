"""The ball-field tag and the narrower pair structure a tagged route segment
takes.

The link's 85 ohm differential structure does not fit between the FPGA's
balls with its open-field clearance. The segment of a pair's route inside a
ball field takes a narrower structure instead, by a tag on that segment's
``Route`` at priority 4, above the structure the signal constraint applies
to the net (a ``routing_structure`` rule wins over
``Constrain(...).structure`` on the same copper):
:py:class:`BallFieldPairTag` on a pair segment gives it ``DRS_85_FIELD``,
3.4/3.4/3.4 mil with 3.5 mil clearance.

A single-ended line takes no tag: the 46 ohm structure, 3.1 mil wide with
6.2 mil clearance, fits two lines between two of the FPGA's fanout vias and
one between two of the memory's (:py:mod:`.part1_fanout_escape`, "Via
size").

Split each pair's route at a ``PairPoint`` about one ball pitch outside the
outermost ball row it crosses, so the full structure starts clear of the
last balls, and tag the segment between the balls and that point. The
reference board the field geometry comes from widens its pairs a median
0.7 pitch past the last ball row
(:py:mod:`jitxexamples.substrates.reference_18layer`, "Ball-field
geometry").

The same tag stands for "under the device" in UG863's spacing table, so the
spacing rules of :py:mod:`.rules` give a tagged segment the under-device
values.
"""

from __future__ import annotations

from jitx.constraints import Tag, UnaryDesignConstraint, design_constraint
from jitx.net import Net
from jitx.si import DifferentialRoutingStructure


class BallFieldTag(Tag):
    """A route segment inside a ball field. Assign its subclass to the
    segment's ``Route``; this base names it in rule conditions."""


class BallFieldPairTag(BallFieldTag):
    """A differential pair segment inside a ball field."""


def ball_field_rules(
    pair: DifferentialRoutingStructure,
    ref_net: Net,
) -> list[UnaryDesignConstraint]:
    """The ball-field structure rule at priority 4: ``pair`` on segments
    tagged :py:class:`BallFieldPairTag`, referenced to ``ref_net``."""
    return [
        design_constraint(BallFieldPairTag(), priority=4).routing_structure(
            pair, ref_net=ref_net
        ),
    ]

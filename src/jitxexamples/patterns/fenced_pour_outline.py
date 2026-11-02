"""Fence vias along an arbitrary closed outline.

Use this pattern when a row of ground vias has to follow a shape that is not
a route: the antipad opening around a signal-via pair, the perimeter of an RF
cavity, the boundary of a BGA breakout. A ``fence_via`` rule fences whatever
copper it matches, routes as well as pours, and a routing structure can carry
its own fence (``RoutingStructure.Layer.fence``). For a shape with no route
behind it, a tagged pour gives the rule the outline to follow. Three pieces
compose:

1. A rule. ``FenceOutlineTag`` names the outlines to fence, and
   ``design_constraint(FenceOutlineTag()).fence_via(via, pattern)`` asks for
   fence vias of class ``via`` along every object that carries the tag. Here
   the rule is a substrate attribute: JITX finds design constraints by
   walking the design, so a rule takes effect only once the design can reach
   it.
2. A tagged pour. ``fence_pour`` is drawn in the shape to fence, and the tag
   is what makes the rule select it. The generated vias take the pour's net,
   so the pour has to be on the board's ground net: ``FencedOutline`` exposes
   a ``GND`` port, and the circuit that uses it connects that port to its own
   ground. The pour sits on the fence via's stop layer, the convention the
   BGA escape demo follows: ``uGnd_L1_L3`` spans layers 0 to 2, and the pour
   is on layer 2.
3. A KeepOut, optional in general and used here. ``fence_keepout`` covers the
   same outline on the same layer; ``pour=True`` keeps pours from covering
   the area and ``via=True`` keeps auto-placed vias out of it. Use it when
   the opening has to stay clear, as for an antipad or a cavity. Leave it out
   when the area should stay copper, for example a ground region that is
   also a return path. The fence vias are placed with or without it.

``ViaFencePattern.offset`` is the spacing between rows of vias and, while
``initial_offset`` is unset, also the distance from the outline to the
centres of the first row, measured outwards. With the one row used here, the
0.2 mm offset puts the 0.25 mm via pads 0.075 mm clear of the outline, outside
the KeepOut. On this 1.6 mm outline the fence has 15 vias, and the via at the
outline's end sits 1.0 mm from the centre (0.8 mm half-length plus the 0.2 mm
offset).

``input_shape_only`` keeps its default (true), so the rule fences the pour's
pre-isolation outline, the shape as drawn, rather than its post-isolation
shape.

The pour sets no ``isolate``: ``Pour.isolate`` is deprecated since jitx 4.4.
Pour clearance belongs in a design rule.
"""

from jitx import KeepOut, LayerSet, Net, Pour
from jitx.board import Board
from jitx.circuit import Circuit
from jitx.constraints import Tag, ViaFencePattern, design_constraint
from jitx.design import Design
from jitx.net import Port
from jitx.shapes.composites import rectangle

from jitxexamples.substrates.generic_20layer import Generic_Substrate

FENCE_LAYER = 2
"""Conductor layer of the fenced pour (L3-Ground2), where ``uGnd_L1_L3`` stops."""

FENCE_PATTERN = ViaFencePattern(pitch=0.35, offset=0.2, num_rows=1)
"""One row of vias at 0.35 mm pitch, centred 0.2 mm outside the outline."""


class FenceOutlineTag(Tag):
    """Pours with this tag get fence vias along their outline."""


class FencedOutlineSubstrate(Generic_Substrate):
    """The generic 20-layer substrate with the outline fence rule attached."""

    outline_fence = design_constraint(FenceOutlineTag()).fence_via(
        Generic_Substrate.uGnd_L1_L3, FENCE_PATTERN
    )


class FencedOutline(Circuit):
    """One fenced outline: a 1.6 mm by 0.8 mm capsule on layer 2.

    Connect ``GND`` to the board's ground net; the fence pour and its vias
    are on that net.
    """

    GND = Port()

    def __init__(self) -> None:
        outline = rectangle(1.6, 0.8, radius=0.4)

        self.fence_pour = Pour(outline, layer=FENCE_LAYER)
        FenceOutlineTag().assign(self.fence_pour)
        # Unnamed: the port already carries the public name GND.
        self.fence_net = Net([self.GND, self.fence_pour])

        self.fence_keepout = KeepOut(
            outline, layers=LayerSet(FENCE_LAYER), pour=True, via=True
        )


class FencedOutlineBoard(Board):
    """A 20 mm by 20 mm board, with room for the outline."""

    shape = rectangle(20, 20, radius=1)


class fenced_pour_outline_design(Design):
    """The fenced outline on its own board, with the substrate that carries the
    fence rule bound on the design."""

    board = FencedOutlineBoard()
    substrate = FencedOutlineSubstrate()
    circuit = FencedOutline()

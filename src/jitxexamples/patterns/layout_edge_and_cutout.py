"""Keep copper back from the board edge, cutouts and holes with two rules.

Two builtin tags name the board's openings, so these rules need no tag of
your own:

- ``IsBoardEdge`` is the outer edge of the board outline, and only that.
- ``IsHole`` is every opening inside it. Measured on jitx 4.6, it matches a
  hole in the board outline polygon, a circuit ``Cutout`` (a routed slot)
  and a via's drill. The drill of a plated through-hole pad was not tested.

``design_constraint(IsBoardEdge, AnyObject).clearance(EDGE_CLEARANCE)`` keeps
all copper 1.5 mm (``EDGE_CLEARANCE``) from the outer edge, and
``design_constraint(IsHole, AnyObject).clearance(HOLE_CLEARANCE)`` keeps it
0.5 mm (``HOLE_CLEARANCE``) from every opening. The board here has both
kinds of inner opening: ``slot`` is a hole in ``CutoutBoard.shape``, and
``cutout`` is a ``Cutout`` in the circuit. A GND pour larger than the board
shows the pullback from each.

Measured on jitx 4.6, with a pour that reaches every feature:

- The pour stops 1.51 mm from the outer edge, the edge rule plus 0.01 mm.
  Neither the outline slot nor the cutout follows the edge rule.
- It stops 0.5 mm from the slot, from the cutout and from the drill of a via
  on another net (``other_via`` here), each within 0.005 mm, measured from
  the drill, not the via pad.
- The pour stays joined to ``gnd_anchor``, its own net's via. The hole
  pullback applies to the drills of other-net vias.
- With neither rule, the pour stops 0.51 mm from the outer edge, the sample
  substrate's ``min_copper_edge_space`` of 0.5 mm plus 0.01, and 0.206 mm
  from the slot and the cutout. ``min_copper_edge_space`` reaches only the
  outer edge too. The 0.206 mm at the slot and the cutout is just above the
  substrate's ``min_copper_hole_space`` of 0.2032 mm; whether that floor
  sets it was not tested.

Because ``IsHole`` matches via drills, a hole rule wider than the via pad
pulls copper back from other-net vias as well, and no second condition limits
it to the board openings. A second condition narrows the other side of the
rule: ``design_constraint(IsHole, IsPour)`` acts on pour copper only, and via
drills still match it. Measured on jitx 4.6, under a 0.8 mm
``(IsHole, IsPour)`` rule in place of both rules here, the pour stopped
0.8 mm from the slot and the cutout and 0.8018 mm from another net's via
drill.
"""

from jitx.board import Board
from jitx.circuit import Circuit
from jitx.constraints import AnyObject, IsBoardEdge, IsHole, design_constraint
from jitx.copper import Pour
from jitx.design import Design
from jitx.feature import Cutout
from jitx.net import Net
from jitx.sample import SampleSubstrate
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Polygon

EDGE_CLEARANCE = 1.5
"""Copper to the outer board edge, mm."""

HOLE_CLEARANCE = 0.5
"""Copper to any hole, slot or cutout, mm."""

SLOT = [(9, -3), (11, -3), (11, 3), (9, 3)]
"""A 2 mm by 6 mm slot in the board outline, centred at (10, 0)."""


class CutoutBoard(Board):
    """A 40 mm by 30 mm board whose outline polygon has a slot in it."""

    shape = Polygon([(-20, -15), (20, -15), (20, 15), (-20, 15)], holes=[SLOT])


class EdgeAndCutout(Circuit):
    """A GND pour larger than the board, a routed cutout, and a via on
    another net, with the two clearance rules."""

    def __init__(self) -> None:
        self.GND = Net(name="GND")
        self.gnd_pour = Pour(rectangle(50, 40), layer=0)
        self.GND += self.gnd_pour
        # A pour needs copper of its own net inside it, or it comes back
        # empty.
        self.gnd_anchor = SampleSubstrate.THVia().at(0, -8)
        self.GND += self.gnd_anchor

        self.cutout = Cutout(rectangle(4, 2).at(-10, 0))

        self.OTHER = Net(name="OTHER")
        self.other_via = SampleSubstrate.THVia().at(0, 8)
        self.OTHER += self.other_via

        self.edge_rule = design_constraint(IsBoardEdge, AnyObject).clearance(
            EDGE_CLEARANCE
        )
        self.hole_rule = design_constraint(IsHole, AnyObject).clearance(HOLE_CLEARANCE)


class layout_edge_and_cutout_design(Design):
    """The pour, the cutout and the slotted board on the sample substrate."""

    board = CutoutBoard()
    substrate = SampleSubstrate()
    circuit = EdgeAndCutout()

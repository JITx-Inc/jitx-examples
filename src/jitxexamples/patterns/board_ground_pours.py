"""Ground pours on every copper layer, anchored and pulled back from the edge.

A 4-layer board carries one ``GND`` pour per copper layer. Each pour is
drawn larger than the board, ``POUR_OUTLINE``, so its realized copper is
the board's outline less the pullback the rules ask for. Three pieces make
it work:

1. One pour per layer. :py:class:`BoardGroundPours` reads the conductor
   count from the substrate of the design that uses it, so the same circuit
   pours every layer of a 6- or 8-layer substrate too.
2. A same-net anchor on every layer. A pour with no pad or via of its own
   net inside it comes back empty, and an anchor counts only on the layers
   where it has copper. ``gnd_anchor`` is a through via on ``GND``, so one
   via has copper on all four layers and holds all four pours; it is sized
   to the substrate's ``min_drill_diameter`` and ``min_annular_ring``. A via
   that spans only some layers holds only those layers' pours, and the
   others come back empty with no design issue.
3. The board-edge rule that ``layout_edge_and_cutout`` teaches:
   ``design_constraint(IsBoardEdge, AnyObject).clearance(EDGE_CLEARANCE)``,
   with its 1.5 mm ``EDGE_CLEARANCE``. ``IsBoardEdge`` is the outer edge of
   the board outline, and the rule names no layer, so it pulls back the
   inner layers' pours the same distance as the outer ones. Without it the
   pours stop at the substrate's ``min_copper_edge_space`` (0.5 mm on the
   sample fabrication constraints); the rule is the larger, so it decides.

Each pour fills the board up to that distance from its edge, on every layer.

Stitching the pours to each other with a via grid is a ``stitch_via`` rule
on a pour tag, which ``layout_stitched_pour`` teaches. Its generated vias do
not hold a pour: with no anchor of their own, stitched pours come back empty
while the rule still generates their vias. The anchor stays even on a
stitched board.

The test, ``tests/test_board_ground_pours.py``, checks offline that every
layer has a pour and an anchor that reaches it. With
``JITX_PATTERN_RUNTIME=1`` and a runtime started at the project root, it
builds the design and measures each pour's copper and its gap to the board
edge.
"""

from __future__ import annotations

import jitx
from jitx.board import Board
from jitx.circuit import Circuit
from jitx.constraints import AnyObject, IsBoardEdge, design_constraint
from jitx.copper import Pour
from jitx.design import Design
from jitx.net import Net
from jitx.sample import SampleFabConstraints, SampleStackup
from jitx.shapes.composites import rectangle
from jitx.substrate import Substrate
from jitx.via import Via, ViaType

from jitxexamples.patterns.layout_edge_and_cutout import EDGE_CLEARANCE

POUR_OUTLINE = rectangle(50.0, 40.0)
"""Each pour's authored outline, larger than the board on every side, in mm."""

ANCHOR_AT = (-15.0, -10.0)
"""The anchor via's position, inside every pour's realized copper, in mm."""


class GroundPourSubstrate(Substrate):
    """Four copper layers with the sample fabrication constraints."""

    stackup = SampleStackup(4)
    constraints = SampleFabConstraints()

    class THVia(Via):
        """A through via on the substrate's floors: a 0.254 mm drill, the
        ``min_drill_diameter``, in a 0.56 mm pad, for a 0.153 mm annular ring
        against the 0.1524 mm ``min_annular_ring``."""

        start_layer = 0
        stop_layer = -1
        diameter = 0.56
        hole_diameter = 0.254
        type = ViaType.MechanicalDrill


class GroundPourBoard(Board):
    """A 40 mm by 30 mm board with 3 mm corner radii."""

    shape = rectangle(40.0, 30.0, radius=3.0)


class BoardGroundPours(Circuit):
    """A ``GND`` pour on every copper layer, a through via that anchors them
    all, and the board-edge rule."""

    def __init__(self) -> None:
        self.GND = Net(name="GND")
        layers = len(jitx.current.substrate.stackup.conductors)
        self.pours = [Pour(POUR_OUTLINE, layer=layer) for layer in range(layers)]
        for pour in self.pours:
            self.GND += pour
        # A pour comes back empty without copper of its own net inside it on
        # its layer. A through via has copper on every layer.
        self.gnd_anchor = GroundPourSubstrate.THVia().at(*ANCHOR_AT)
        self.GND += self.gnd_anchor

        self.edge_rule = design_constraint(IsBoardEdge, AnyObject).clearance(
            EDGE_CLEARANCE
        )


class board_ground_pours_design(Design):
    """The ground pours on the 4-layer board."""

    board = GroundPourBoard()
    substrate = GroundPourSubstrate()
    circuit = BoardGroundPours()

"""Wider traces and clearances on one heavy copper layer, by layer rule.

Heavier copper etches less precisely, so a fabricator asks for wider traces
and wider gaps on a 2 oz layer than on a 1 oz one. A design rule carries that
per layer: ``OnLayer(i)`` is a condition that matches copper on conductor
layer ``i``. The heavy layer gets floors, and every rule that would
otherwise beat a floor on that layer gets a copy narrowed to the layer.

``HeavyInnerSubstrate`` is a 4-layer stackup with a 70 um (2 oz) first inner
layer; the other three conductors are 35 um. :py:func:`heavy_layer_index`
finds it by walking ``substrate.stackup.conductors`` (0 is the top) by
``thickness``. Two nets are routed between pairs of ``PowerVia``, each layer
under a GND pour: ``PWR``, which carries ``PowerTag``, once each on layers 0,
1 and 2; ``SIG``, which carries no tag, on layers 0 and 1.

The rules sit on one priority ladder, the layout-constraints skill's:

- 0, board defaults: ``IsTrace`` 0.2 mm wide, ``(IsCopper, IsCopper)`` 0.15
  mm apart;
- 1, the trace-to-pour clearance ``(IsTrace, IsPour)`` 0.2 mm, below every
  rule on a net tag so a tag's clearance to pours wins; and the heavy
  layer's floors, ``IsTrace & OnLayer(1)`` 0.5 mm wide and
  ``(IsCopper & OnLayer(1), AnyObject)`` 0.35 mm, with the trace-to-pour
  rule's own form on that layer, ``(IsTrace & OnLayer(1), IsPour)``, at the
  larger of its value and the floor;
- 2, the power nets' rules: ``PowerTag`` 0.4 mm wide and 0.3 mm to any
  object;
- 3, the power rules' copies on the heavy layer,
  ``PowerTag() & OnLayer(1)``, at the floor, since both power values are
  below it.

A floor at 1 loses to every rule at 2 or above that matches the same copper,
with nothing reported; the copies at 3 are what hold the floor for the power
nets. :py:func:`heavy_layer_rules` writes the floors, the trace-to-pour
layer form and the copies from the rules it is given.

Measured on jitx 4.6, at mid-span, with the pour pullback the winning
clearance plus 0.01 mm:

- PWR on layers 0 and 2: 0.4 mm wide, pour 0.31 mm away;
- PWR on layer 1: 0.5 mm wide, pour 0.36 mm away;
- SIG on layer 0: 0.2 mm wide, pour 0.21 mm away;
- SIG on layer 1: 0.5 mm wide, pour 0.36 mm away.

Each piece is needed, measured on jitx 4.6 with that piece left out and no
design issue either time:

- without the copies at 3, PWR on layer 1 came back 0.4 mm wide with the
  pour 0.31 mm away: the power rules at 2 beat both floors;
- without the trace-to-pour layer form, the pour came back 0.21 mm from SIG
  on layer 1: at rung 1, ``(IsTrace, IsPour)`` beat the clearance floor.

``OnLayer.internal()`` matches every inner layer, here both 1 and 2, not
the heavy one alone; name the index when one inner layer differs (measured
on jitx 4.6: a width rule on ``PowerTag() & OnLayer.internal()`` widened
the routes on layers 1 and 2 and left layer 0's).

Keep a requested width at or below the pads the route ends on. On jitx 4.6
a route asked to be wider than its 1.0 mm end pads came back 1.0 mm wide,
the convex hull of the two pads, with no design issue. ``PowerVia`` has a
1.0 mm pad so that the heavy floor fits.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import jitx
from jitx.circuit import Circuit, Route
from jitx.constraints import (
    AnyObject,
    AtomExpr,
    BinaryDesignConstraint,
    BoolExpr,
    BuiltinTag,
    DesignConstraint,
    IsCopper,
    IsPour,
    IsTrace,
    OnLayer,
    Tag,
    UnaryDesignConstraint,
    design_constraint,
)
from jitx.copper import Pour
from jitx.design import Design
from jitx.net import Net
from jitx.sample import (
    Copper,
    Core,
    Prepreg,
    SampleBoard,
    SampleFabConstraints,
    SoldermaskLayer,
)
from jitx.shapes.composites import rectangle
from jitx.stackup import Stackup
from jitx.substrate import Substrate
from jitx.via import Via, ViaType

BOARD_WIDTH = 0.2
"""Board default trace width, mm."""

BOARD_CLEARANCE = 0.15
"""Board default copper-to-copper clearance, mm."""

TRACE_TO_POUR = 0.2
"""Trace-to-pour clearance, mm."""

POWER_WIDTH = 0.4
"""Power trace width, mm."""

POWER_CLEARANCE = 0.3
"""Power copper to any other object, mm."""

HEAVY_MIN_WIDTH = 0.5
"""The heavy layer's trace width floor, mm."""

HEAVY_MIN_CLEARANCE = 0.35
"""The heavy layer's copper clearance floor, mm."""

POWER_ROUTE_Y = {0: 10.0, 1: 0.0, 2: -10.0}
"""The y coordinate of the power route on each routed layer, mm."""

SIGNAL_ROUTE_Y = {0: 4.0, 1: -5.0}
"""The y coordinate of the untagged route on each routed layer, mm."""


def heavy_layer_index(substrate: Substrate, thickness: float | None = None) -> int:
    """The conductor index of the heavy layer, 0 being the top.

    Walks ``substrate.stackup.conductors`` and reads each conductor's
    ``thickness``. With ``thickness`` given, returns the one conductor that
    thick; without it, the one conductor thicker than the rest. Raises
    ``ValueError`` when a conductor has no thickness, when no conductor or
    more than one matches (pass the index directly for a stackup with two
    heavy layers), or when every conductor is equally thick: a layer the
    substrate does not model as heavy is a substrate task first.
    """
    thicknesses: list[float] = []
    for index, conductor in enumerate(substrate.stackup.conductors):
        if conductor.thickness is None:
            raise ValueError(f"conductor {index} has no thickness")
        thicknesses.append(float(conductor.thickness))
    if thickness is None:
        if max(thicknesses) == min(thicknesses):
            raise ValueError(
                f"every conductor is {thicknesses[0]} thick; the substrate models no "
                f"heavy layer"
            )
        thickness = max(thicknesses)
    hits = [i for i, t in enumerate(thicknesses) if math.isclose(t, thickness)]
    if len(hits) != 1:
        raise ValueError(
            f"{len(hits)} conductors are {thickness} thick, not one; pass the index"
        )
    return hits[0]


def _class_tag(condition: BoolExpr, rule: DesignConstraint) -> Tag:
    """The single user tag a class rule's condition names."""
    if isinstance(condition, AtomExpr) and not isinstance(
        condition.atom, (BuiltinTag, OnLayer)
    ):
        return condition.atom
    raise ValueError(
        f"{rule!r}: a copy is written only for a rule whose condition is one tag "
        f"(design_constraint(PowerTag(), ...)); write this rule's layer form by hand"
    )


def _narrowed(tag: Tag, layer: int, exclude: Sequence[Tag]) -> BoolExpr:
    """``tag`` less every excluded tag that is not ``tag``'s own, on ``layer``."""
    condition: Tag | BoolExpr = tag
    for excluded in exclude:
        if not isinstance(tag, type(excluded)):
            condition = condition & ~excluded
    return condition & OnLayer(layer)


def heavy_layer_rules(
    layer: int,
    min_width: float,
    min_clearance: float,
    trace_to_pour: float,
    class_rules: Sequence[DesignConstraint] = (),
    *,
    exclude: Sequence[Tag] = (),
) -> list[DesignConstraint]:
    """The rules that hold one heavy layer's floors, on the skill's ladder.

    Returns, for conductor ``layer``:

    - the floors at priority 1: ``IsTrace & OnLayer(layer)`` at
      ``min_width`` and ``(IsCopper & OnLayer(layer), AnyObject)`` at
      ``min_clearance``;
    - the trace-to-pour rule's layer form at priority 1,
      ``(IsTrace & OnLayer(layer), IsPour)``, at the larger of
      ``trace_to_pour`` and ``min_clearance``, so that on the layer it beats
      both ``(IsTrace, IsPour)`` and the floor;
    - for each rule in ``class_rules`` whose value is below the floor, a copy
      at priority 3 narrowed with ``& OnLayer(layer)``, at the floor. A rule
      at priority 2 or 3 beats the floors at 1 on the layer's copper, with
      nothing reported, so without the copy it would hold its own value
      there. A rule at or above the floor needs no copy.

    ``exclude`` names route tags a width copy must not match, such as a
    sense tag on sense routes that is not a subclass of the class tag:
    ``PowerTag() & ~SenseTag() & OnLayer(layer)``. A tag is not excluded
    from its own rule's copy. Clearance copies are not narrowed by
    ``exclude``: on an excluded route a clearance copy that left it out
    would leave the class's rule at 2, below the floor, beating the floor
    at 1. The cost: a sense clearance above the floor loses to the copy on
    the heavy layer. A sense route on a power net there meets
    ``(SenseTag(), AnyObject)`` at 3, say 0.5, and the copy
    ``(PowerTag() & OnLayer(layer), AnyObject)`` at 3, at the floor. At one
    priority the more specific condition wins, and the copy is more
    specific, so the sense route holds the floor (0.35 in this module), not
    0.5. A user's own ``SenseTag() & OnLayer(layer)`` rule at 3 ties the copy on
    specificity, and what decides a tie is not established. That reasoning
    follows the layout-constraints skill's priority ladder; a sense route on
    a heavy layer was not measured here.

    ``class_rules`` takes only the shapes the layout-constraints skill
    teaches: one-condition ``trace_width`` rules and two-condition
    ``clearance`` rules, at priority 2 or 3, whose (first) condition is one
    tag. Anything else raises ``ValueError``; write its layer form by hand.
    A class that wants a value on the layer above the floor writes its own
    ``& OnLayer(layer)`` rule at 3 and is left out of ``class_rules``.
    """
    on_layer = OnLayer(layer)
    rules: list[DesignConstraint] = [
        design_constraint(IsTrace & on_layer, priority=1).trace_width(min_width),
        design_constraint(IsCopper & on_layer, AnyObject, priority=1).clearance(
            min_clearance
        ),
        design_constraint(IsTrace & on_layer, IsPour, priority=1).clearance(
            max(trace_to_pour, min_clearance)
        ),
    ]
    for rule in class_rules:
        if rule.priority not in (2, 3):
            raise ValueError(
                f"{rule!r}: priority {rule.priority}; copies are written for rules "
                f"at 2 (net-tag rules) or 3"
            )
        if isinstance(rule, UnaryDesignConstraint):
            width = rule.trace_width_constraint
            others = (
                rule.stitch_via_constraint,
                rule.fence_via_constraint,
                rule.thermal_relief_constraint,
                rule.serpentine_params_constraint,
                rule.coupled_pair_params_constraint,
                rule.pour_feature_size_constraint,
                rule.routing_structure_constraint,
            )
            if width is None or any(c is not None for c in others):
                raise ValueError(
                    f"{rule!r}: a one-condition rule must set only a width"
                )
            tag = _class_tag(rule.condition, rule)
            if width.width < min_width:
                rules.append(
                    design_constraint(
                        _narrowed(tag, layer, exclude), priority=3
                    ).trace_width(min_width)
                )
        elif isinstance(rule, BinaryDesignConstraint):
            clearance = rule.clearance_constraint
            if clearance is None:
                raise ValueError(f"{rule!r}: a two-condition rule must set a clearance")
            tag = _class_tag(rule.first, rule)
            if clearance.clearance < min_clearance:
                rules.append(
                    design_constraint(
                        _narrowed(tag, layer, ()), rule.second, priority=3
                    ).clearance(min_clearance)
                )
        else:
            raise ValueError(f"{rule!r}: not a design rule this helper copies")
    return rules


class HeavyInnerStackup(Stackup):
    """Four conductors, top to bottom 35, 70, 35 and 35 um."""

    top_surface = SoldermaskLayer(thickness=0.1)
    l0 = Copper(thickness=0.035, name="Top")
    d0 = Core(thickness=0.55)
    l1 = Copper(thickness=0.070, name="In1 (2 oz)")
    d1 = Prepreg(thickness=0.1)
    l2 = Copper(thickness=0.035, name="In2")
    d2 = Core(thickness=0.55)
    l3 = Copper(thickness=0.035, name="Bottom")
    bottom_surface = SoldermaskLayer(thickness=0.1)


class HeavyInnerSubstrate(Substrate):
    """The 4-layer stackup with the sample fabrication constraints."""

    stackup = HeavyInnerStackup()
    constraints = SampleFabConstraints()

    class PowerVia(Via):
        """A through via with a 1.0 mm pad and a 0.5 mm drill."""

        start_layer = 0
        stop_layer = -1
        diameter = 1.0
        hole_diameter = 0.5
        type = ViaType.MechanicalDrill


class PowerTag(Tag):
    """Power nets."""


class HeavyCopperLayer(Circuit):
    """A power net routed on three layers and an untagged net on two, each
    layer under a GND pour."""

    def __init__(self) -> None:
        self.PWR = Net(name="PWR")
        self.SIG = Net(name="SIG")
        self.GND = Net(name="GND")
        PowerTag().assign(self.PWR)

        self.ends: list[Via] = []
        self.routes: dict[int, Route] = {}
        self.signal_routes: dict[int, Route] = {}
        for net, rows, routes in (
            (self.PWR, POWER_ROUTE_Y, self.routes),
            (self.SIG, SIGNAL_ROUTE_Y, self.signal_routes),
        ):
            for layer, y in rows.items():
                start = HeavyInnerSubstrate.PowerVia().at(-12, y)
                end = HeavyInnerSubstrate.PowerVia().at(12, y)
                self.ends += [start, end]
                net += start
                net += end
                routes[layer] = Route(start, end, layer=layer)
        self.pours: dict[int, Pour] = {}
        for layer in POWER_ROUTE_Y:
            pour = Pour(rectangle(40, 30), layer=layer)
            self.pours[layer] = pour
            self.GND += pour
        # One GND via joins every pour to the net, so none comes back empty.
        self.gnd_anchor = HeavyInnerSubstrate.PowerVia().at(-18, 13)
        self.GND += self.gnd_anchor

        self.heavy_layer = heavy_layer_index(jitx.current.substrate)
        power_width = design_constraint(PowerTag(), priority=2).trace_width(POWER_WIDTH)
        power_clearance = design_constraint(
            PowerTag(), AnyObject, priority=2
        ).clearance(POWER_CLEARANCE)
        # Priority ladder: 0 board defaults; 1 trace to pour and the heavy
        # layer's floors; 2 net-tag rules; 3 their copies on the heavy layer.
        self.rules = [
            design_constraint(IsTrace).trace_width(BOARD_WIDTH),
            design_constraint(IsCopper, IsCopper).clearance(BOARD_CLEARANCE),
            design_constraint(IsTrace, IsPour, priority=1).clearance(TRACE_TO_POUR),
            power_width,
            power_clearance,
            *heavy_layer_rules(
                self.heavy_layer,
                HEAVY_MIN_WIDTH,
                HEAVY_MIN_CLEARANCE,
                TRACE_TO_POUR,
                [power_width, power_clearance],
            ),
        ]


class layout_heavy_copper_layer_design(Design):
    """The routes on the heavy-inner-layer substrate."""

    board = SampleBoard()
    substrate = HeavyInnerSubstrate()
    circuit = HeavyCopperLayer()

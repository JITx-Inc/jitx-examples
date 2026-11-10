"""Code routes on one layer: a plain route, a sketched detour, and per-route
overrides.

Each row of ``CodeRouteBasics`` joins the single pad of two fictional
``ExampleChip`` parts, 20 mm apart, with code routes on layer 0 of the
sample board: one ``Route`` per row, except the tapered row, which splits
into two at a ``RoutePoint``. The rows show four things a code route can say
about the trace it asks for.

1. ``plain``: ``Route(a.io, b.io, layer=0)`` and nothing else. The router
   picks the path; width and clearance come from the routing structure, net
   class or design rules that apply to the net. None applies here. Measured
   on jitx 4.6.0: one straight trace from pad centre to pad centre, 20.0 mm
   long and 0.127 mm wide, the minimum copper width of the sample
   fabrication constraints.

2. ``above`` and ``below``: a column of five ground vias stands across the
   straight path, and a ``Route.Sketch`` tells the router which side to pass.
   ``Route.Sketch(start, turns, end)`` takes a start and end terminal, here the
   two pad centres, and an ordered list of turns between them. The turns come
   from ``designer_placed_detour_turns``, two points 3 mm off the row's axis
   on the chosen side. Measured on jitx 4.6.0, the route passes the column on
   the named side and crosses the column's centre line 1.916 mm from the
   axis, just clear of the outermost via pad. The same row with no sketch
   passed below, so it is the ``above`` row that shows the sketch at work.

   A turn is a hint, not a waypoint. The realized path stayed 1.623 mm from
   each turn: it bends only as far as the obstacle needs. With nothing in the
   way, a single turn 3 mm off the axis left the route straight. A route
   ``KeepOut`` in place of the vias behaves the same way: the turns picked the
   side, and the route crossed 2.064 mm from the axis. Turns are read in the
   frame of the circuit that declares the route; a child circuit placed with a
   180 degree rotation still passed on its own sketched side.

3. ``configured``: ``Route.Config(trace_width=0.3, trace_space=0.4,
   destination_target=Route.Target.rectangle(0.6, 0.3))``, with a ground pour
   around the row so the trace space shows as the pour's pullback from the
   trace. The ``Route.Config`` docstring states the rule for every field:
   fields set here can't be changed in the physical design view; change the
   code instead. The other fields stay editable there. Measured on jitx
   4.6.0, the trace is 0.3 mm wide and the pour stops 0.402 mm from it.
   Also measured on jitx 4.6.0: ``trace_width`` and ``trace_space`` set here
   win over a design rule for the same route, and ``pair_space`` wins over a
   routing structure; the other fields were not compared. A ``trace_width``
   of 0.08 mm realized at 0.127 mm, the sample board's minimum copper width,
   with no issue reported (cause inferred; the fabrication minimum was not
   varied). A routing structure's 0.08 mm trace width was not raised to the
   minimum and raised no issue.

   The rectangle target ends the trace in a 0.6 mm by 0.3 mm rectangle
   centred on the destination pad: a square end that reaches the pad's far
   edge, where the default end is a round cap centred on the pad. Its height
   matches the trace width on purpose, because a target wider or narrower
   than the trace tapers the route (row 4). JITX does not check that a
   target stays inside the pad. A custom target can't be combined with
   ``envelope_overhead``, the length-matching setting that
   ``serpentine_sections`` uses: ``Route.Config`` raises ``ValueError``.

4. ``tapered``: a 0.15 mm trace that widens into the whole 0.6 mm square
   pad of ``ExampleChip`` over its last 1.0 mm. A route target is the way to
   taper a trace into a pad of a different width. A target wider or
   narrower than the trace tapers the whole route it is on, from the trace
   width at the route's start to the target's extent across the trace at
   the target, so the taper is as long as that route. To keep the line at
   one width and taper only at the pad, split it at a ``RoutePoint`` and put
   the target on the short last route. The ``Route.Target`` docstring places
   the target in the pad's own frame, so that extent is the rectangle's
   height for a trace that runs along the pad's x axis, as here, and its
   width for one that runs along y.

   The row is two routes: ``Route.Config(trace_width=0.15)`` from the source
   pad to a ``RoutePoint`` ``TAPER_LENGTH`` (1.0 mm) before the destination
   pad's near edge, then ``Route.Config(trace_width=0.15,
   destination_target=Route.Target.rectangle(0.6, 0.6))`` into the pad. The
   0.15 mm is a little over the sample board's 0.127 mm minimum copper
   width, so it is not raised to it. The target is the pad's own outline,
   so the copper meets the pad at its full width and stays inside it.
   Measured on jitx 4.6.0, the first route is 0.15 mm wide along its whole
   length, and the last widens in a straight line from 0.15 mm at the route
   point to 0.6 mm at the pad's near edge, 0.376 mm halfway. With the same
   target on one route from pad to pad, the taper ran the whole 19.7 mm from
   the source pad's centre to the pad's near edge, 0.378 mm wide halfway
   between the pads. Other targets taper the same way: with
   ``Route.Target.FIT`` on a 0.6 mm pad, a 0.3 mm trace was 0.452 mm wide
   halfway along, and a ``Route.Target.circle(radius=0.25)`` gave 0.4 mm.

Every row is its own net between its two pads. The vias and the pour are on
one ``GND`` net; the via inside the pour, at the row's end, ties the pour to
it.

The runtime tests in ``tests/test_code_route_basics.py`` measure the realized
rows of this design.
"""

from __future__ import annotations

from jitx import Net, Pour
from jitx.circuit import Circuit, Route
from jitx.controlpoint import RoutePoint
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.shapes.composites import rectangle

from jitxexamples.patterns.si_parts import ExampleChip

PAD_X = 10.0
"""Each row's chips sit at x = -PAD_X and x = PAD_X, in mm."""

PLAIN_Y = 18.0
"""y of the plain route's row, in mm."""

ABOVE_Y = 6.0
"""y of the row whose route is sketched to pass above the vias, in mm."""

BELOW_Y = -6.0
"""y of the row whose route is sketched to pass below the vias, in mm."""

CONFIGURED_Y = -18.0
"""y of the row whose route sets ``Route.Config``, in mm."""

TAPERED_Y = 0.0
"""y of the row whose route tapers into its destination pad, in mm: between
the two sketched rows, clear of both via columns."""

VIA_COUNT = 5
"""Vias in each obstacle column."""

VIA_PITCH = 0.75
"""Spacing of the obstacle vias along the column, in mm."""

CONFIG = Route.Config(
    trace_width=0.3,
    trace_space=0.4,
    destination_target=Route.Target.rectangle(0.6, 0.3),
)
"""The configured row's overrides: width and clearance in mm, and a square
destination end as long as the pad and as wide as the trace."""

TAPER_RUN = Route.Config(trace_width=0.15)
"""The tapered row's first route: a 0.15 mm trace at one width."""

TAPER = Route.Config(
    trace_width=0.15,
    destination_target=Route.Target.rectangle(0.6, 0.6),
)
"""The tapered row's last route: the same trace, and a destination target
the size of the 0.6 mm square pad, so the trace widens to the pad's full
width."""

TAPER_LENGTH = 1.0
"""How far before the destination pad's near edge the taper starts, in mm."""

PAD_HALF = 0.3
"""Half the side of ``ExampleChip``'s 0.6 mm square pad, in mm."""


def designer_placed_detour_turns(row_y: float, side: int) -> list[tuple[float, float]]:
    """Sketch turns that send a row's route past its via column.

    A designer would usually place these interactively, dragging the route
    to one side of the obstacle; they are written here so the example is
    complete. On jitx 4.6.0, ``rd.layout.modify(route, turns=...)`` on a
    sketched code route was refused (``RequestRejected``, "sketch of route
    [...] is set in code (code-placed)"); with the sketch removed from code,
    the same edit was accepted and moved the route to the other side of the
    column. An interactive drag was not tried. To draw the detour
    interactively, delete the sketch from code first.

    ``side`` is ``1`` to pass above the column and ``-1`` to pass below it.
    The turns sit 3 mm off the row's axis, beyond the column's outermost via
    pad.
    """
    return [(-3.0, row_y + 3.0 * side), (3.0, row_y + 3.0 * side)]


class CodeRouteBasics(Circuit):
    """Five rows of code routes: plain, sketched above and below a via
    column, configured inside a ground pour, and tapered into its
    destination pad."""

    def __init__(self) -> None:
        self.GND = Net(name="GND")

        # 1. A plain code route.
        self.plain_a = ExampleChip().at(-PAD_X, PLAIN_Y)
        self.plain_b = ExampleChip().at(PAD_X, PLAIN_Y)
        self.plain_net = Net([self.plain_a.io, self.plain_b.io])
        self.plain = Route(self.plain_a.io, self.plain_b.io, layer=0)

        # 2. Two routes past a via column, told which side by a sketch.
        self.vias: list[SampleSubstrate.THVia] = []
        self.sketched_chips: list[ExampleChip] = []
        self.sketched_nets: list[Net] = []
        self.above = self._detour_row(ABOVE_Y, 1)
        self.below = self._detour_row(BELOW_Y, -1)

        # 3. A configured route inside a ground pour.
        self.configured_a = ExampleChip().at(-PAD_X, CONFIGURED_Y)
        self.configured_b = ExampleChip().at(PAD_X, CONFIGURED_Y)
        self.configured_net = Net([self.configured_a.io, self.configured_b.io])
        self.configured = Route(
            self.configured_a.io, self.configured_b.io, layer=0, config=CONFIG
        )
        self.pour = Pour(rectangle(30.0, 6.0).at(0.0, CONFIGURED_Y), layer=0)
        self.pour_via = SampleSubstrate.THVia().at(13.5, CONFIGURED_Y - 2.0)
        self.GND += self.pour
        self.GND += self.pour_via

        # 4. A route that tapers into its destination pad.
        self.tapered_a = ExampleChip().at(-PAD_X, TAPERED_Y)
        self.tapered_b = ExampleChip().at(PAD_X, TAPERED_Y)
        self.taper_start = RoutePoint(layer=0).at(
            PAD_X - PAD_HALF - TAPER_LENGTH, TAPERED_Y
        )
        self.tapered_net = Net(
            [self.tapered_a.io, self.tapered_b.io, self.taper_start.port]
        )
        self.tapered_run = Route(
            self.tapered_a.io, self.taper_start, layer=0, config=TAPER_RUN
        )
        self.tapered = Route(self.taper_start, self.tapered_b.io, layer=0, config=TAPER)

    def _detour_row(self, row_y: float, side: int) -> Route:
        """Two chips at height ``row_y``, a via column between them, and a
        route sketched to pass the column on ``side``."""
        a = ExampleChip().at(-PAD_X, row_y)
        b = ExampleChip().at(PAD_X, row_y)
        self.sketched_chips += [a, b]
        self.sketched_nets.append(Net([a.io, b.io]))
        first = row_y - (VIA_COUNT - 1) * VIA_PITCH / 2
        column = [
            SampleSubstrate.THVia().at(0.0, first + k * VIA_PITCH)
            for k in range(VIA_COUNT)
        ]
        self.vias += column
        for via in column:
            self.GND += via
        sketch = Route.Sketch(
            Route.Sketch.Terminal((-PAD_X, row_y)),
            designer_placed_detour_turns(row_y, side),
            Route.Sketch.Terminal((PAD_X, row_y)),
        )
        return Route(a.io, b.io, layer=0, sketch=sketch)


class code_route_basics_design(SampleDesign):
    """The five rows on the 50 mm sample board."""

    circuit = CodeRouteBasics()

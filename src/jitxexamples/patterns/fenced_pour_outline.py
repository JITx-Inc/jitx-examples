"""Fence vias along an arbitrary closed outline.

Use this pattern when a row of ground vias has to follow a shape that is not
a route: the antipad opening around a signal-via pair, the perimeter of an RF
cavity, the boundary of a BGA breakout. A ``fence_via`` rule fences the pours
it matches. On jitx 4.6 it fences no route, whether its tag is on the route
or on its net, and reports no issue; a route's fence comes from its routing
structure (``RoutingStructure.Layer.fence``). With the tag on a net, the rule
fences that net's pours, placing the same vias as the tag on the pour. A
tagged pour gives the rule the outline to follow. The module has two
examples: ``FencedOutline``, a ring outside an opening that stays clear, and
``CavityRing``, a closed ring inside a ground cavity pour. Three pieces
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
the KeepOut. The 0.4 mm pitch is the closest the generic substrate allows
for this via: its 0.1 mm drills then sit 0.3 mm apart, the substrate's
``min_hole_to_hole``, and JITX does not check it. The 0.25 mm pads need no
copper spacing: the fence vias are all on GND, and clearance is not enforced
between copper of the same net. On this 1.6 mm outline the
fence has 13 vias, and the via at the outline's end sits 1.0 mm from the
centre (0.8 mm half-length plus the 0.2 mm offset). Measured on jitx 4.6:
13 vias 0.407 mm apart, the end via 1.0004 mm from the centre, no design
issues. The pour itself comes back empty there, since the KeepOut covers it
and nothing else of its net is inside it, and the fence is still placed
along its drawn outline.

``CavityRing`` turns the fence inwards. A negative ``offset`` and
``initial_offset`` put the row inside the outline, so the vias land in the
cavity pour's own copper and join it to the GND plane on layer 2. Measured on
jitx 4.6 with ``CAVITY_PATTERN``: 24 vias, centres 0.5 mm inside the 8 mm by
6 mm outline at 1.0 mm spacing, one at each corner, so the ring is closed; no
design issues. The ring's vias do not anchor the pour: with ``anchor``
moved outside the cavity, the cavity pour came back empty. ``anchor`` is a
code-placed GND via that keeps the cavity pour and the plane from being
dropped as islands. The fab sets the closest the ring can be:
``CAVITY_PATTERN.pitch`` is at least one via pad, since JITX thins a pitch
below the pad without a design issue, and keeps ``min_hole_to_hole`` between
drills, which JITX does not check either.

``input_shape_only`` keeps its default (true), so the rule fences the pour's
pre-isolation outline, the shape as drawn, rather than its post-isolation
shape.

The pour sets no ``isolate``: ``Pour.isolate`` is deprecated since jitx 4.4.
Pour clearance belongs in a design rule.

:py:func:`fence_count_range` gives the via count to expect along an outline
before a build is checked: it returns 12 to 14 for ``FencedOutline`` (13
measured) and 23 to 24 for ``CavityRing``, whose offset outline is exactly
24 pitches long (24 measured).
"""

import math

import shapely

from jitx import KeepOut, LayerSet, Net, Pour
from jitx.board import Board
from jitx.circuit import Circuit
from jitx.constraints import Tag, ViaFencePattern, design_constraint
from jitx.design import Design
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.substrate import FabricationConstraints
from jitx.via import Via
from shapely.geometry.base import BaseGeometry

from jitxexamples.patterns.layout_stitched_pour import min_stitch_pitch
from jitxexamples.substrates.generic_20layer import Generic_Substrate

FENCE_LAYER = 2
"""Conductor layer of the fenced pour (L3-Ground2), where ``uGnd_L1_L3`` stops."""

FENCE_PATTERN = ViaFencePattern(pitch=0.4, offset=0.2, num_rows=1)
"""One row of vias at 0.4 mm pitch, centred 0.2 mm outside the outline."""


def _is_square(outline: BaseGeometry) -> bool:
    """True when ``outline`` is a polygon with four equal sides and four
    right-angled corners."""
    if not isinstance(outline, shapely.Polygon) or outline.interiors:
        return False
    corners = list(outline.exterior.simplify(0).coords)[:-1]
    if len(corners) != 4:
        return False
    sides = [math.dist(corners[i - 1], c) for i, c in enumerate(corners)]
    if max(sides) - min(sides) > 1e-9 * max(sides):
        return False
    for i, (x, y) in enumerate(corners):
        (px, py), (nx, ny) = corners[i - 1], corners[(i + 1) % 4]
        ax, ay, bx, by = px - x, py - y, nx - x, ny - y
        if abs(ax * bx + ay * by) > 1e-9 * math.hypot(ax, ay) * math.hypot(bx, by):
            return False
    return True


def fence_count_range(
    outline: BaseGeometry,
    initial_offset: float,
    pitch: float,
    via: type[Via],
    fab: FabricationConstraints,
) -> tuple[int, int]:
    """The fence via counts to accept per row along a pour outline, lowest
    first.

    ``outline`` is the pour's drawn outline in any frame, and
    ``initial_offset`` the row's offset, positive outward and negative
    inward. For row k of a pattern, pass the pattern's ``initial_offset +
    (k - 1) * offset`` (the pattern's ``initial_offset`` defaults to its
    ``offset``). Every measured
    outline fence had one row; multi-row outline fences were not measured.
    L is the length of the outline offset by ``initial_offset``, its corners
    kept square:

    - an outward offset of a square whose L is a whole number of pitches
      gives ``L / pitch`` vias: the offset keeps each corner square, with one
      via on its diagonal. Measured on jitx 4.6 on one case, 36 vias outside
      an 8 by 8 pour at offset 0.5, pitch 1.0 (L 36);
    - anything else gives ``floor(L / pitch) - 1`` to ``ceil(L / pitch)``,
      never below 0: the runtime changes the spacing to close the ring
      (measured on jitx 4.6: 26 vias 0.6 inside an 8 by 8 pour at pitch
      1.0, 19 around a 2.5 radius circle at offset 0.5, 13 around this
      module's capsule and 24 inside its cavity). Outward offsets of
      rectangles that are not square, and of a square whose L is not a whole
      number of pitches, were not measured and take this range.

    Raises ``ValueError`` for a pitch below :py:func:`min_stitch_pitch`
    for ``via`` and ``fab``, the larger of two bounds. Below one via pad
    the runtime thins the fence, so no count from L applies (measured on
    jitx 4.6 on a pour outline: 40 vias, every other site, at pitch 0.3
    with a 0.45 pad). Below the drill plus ``min_hole_to_hole`` the
    runtime fills every site but the fab cannot drill them (measured on
    jitx 4.6 on a stitch grid: 289 vias at pitch 0.5, drill edges 0.2
    apart against a 0.254 minimum, with no issue).

    The range assumes the pattern sets neither ``min_pitch`` nor
    ``max_pitch``, which change how many vias the runtime places (measured
    on jitx 4.6: pitch 0.3 with ``min_pitch`` 0.6 gave 38, not 40).

    Count the generated vias that sit on the offset outline at the pitch; a
    distance band alone does not separate a fence from a stitch grid.
    """
    floor = min_stitch_pitch(via, fab)
    if pitch < floor:
        raise ValueError(
            f"fence pitch {pitch} mm is below {floor:.3f} mm, the smallest the "
            f"runtime fills without thinning and the fab can drill for {via.__name__}"
        )
    ring = outline.buffer(initial_offset, join_style="mitre")
    if ring.is_empty:
        raise ValueError(f"an offset of {initial_offset} leaves no outline")
    count = ring.length / pitch
    low = math.floor(count + 1e-9)
    if initial_offset > 0 and _is_square(outline) and abs(count - round(count)) < 1e-9:
        return low, low
    return max(low - 1, 0), math.ceil(count - 1e-9)


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


CAVITY_LAYER = 0
"""Conductor layer of the cavity pour (L1-Ground1)."""

CAVITY_VIA = Generic_Substrate.TH_Via
"""The ring via: the generic substrate's through via, pad 0.5 mm, drill 0.25 mm."""

CAVITY_PATTERN = ViaFencePattern(
    pitch=1.0, offset=-0.5, initial_offset=-0.5, num_rows=1
)
"""One row of vias at 1.0 mm pitch, centred 0.5 mm inside the cavity outline."""


class CavityRingTag(Tag):
    """Pours with this tag get a ring of vias inside their outline."""


class CavityRing(Circuit):
    """An 8 mm by 6 mm GND cavity pour on layer 0 with a closed via ring
    inside its outline, joined to a GND plane on layer 2.

    Connect ``GND`` to the board's ground net. The ring rule is an attribute
    of the circuit, so it reaches any design that uses the circuit.
    """

    GND = Port()

    def __init__(self) -> None:
        self.cavity_pour = Pour(rectangle(8, 6), layer=CAVITY_LAYER)
        CavityRingTag().assign(self.cavity_pour)
        self.plane = Pour(rectangle(12, 10), layer=FENCE_LAYER)
        self.anchor = CAVITY_VIA().at(0, 0)
        # Unnamed: the port already carries the public name GND.
        self.cavity_net = Net([self.GND, self.cavity_pour, self.plane, self.anchor])
        self.ring_rule = design_constraint(CavityRingTag()).fence_via(
            CAVITY_VIA, CAVITY_PATTERN
        )


class cavity_ring_design(Design):
    """The cavity ring on the fenced outline's board and the generic substrate."""

    board = FencedOutlineBoard()
    substrate = Generic_Substrate()
    circuit = CavityRing()

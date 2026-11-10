"""Stitch a ground pour with vias from a design rule.

A ``stitch_via`` rule fills a pour with vias on a grid, so nobody places them
by hand and the grid follows the pour when its outline changes. Three pieces
compose:

1. A tag on the pour. ``StitchedPourTag`` is assigned to the top-layer GND
   pour, and ``design_constraint(StitchedPourTag()).stitch_via(via, grid)``
   asks for vias of class ``via`` on ``grid`` inside every pour that carries
   the tag. The vias take the pour's net (measured on jitx 4.6: the 32
   generated vias here are on ``GND``).
2. A pitch checked against the substrate. ``checked_stitch_grid`` refuses a
   pitch below one via pad, or one at which neighbouring drills would sit
   closer than ``min_hole_to_hole``, read from the fabrication constraints of
   the substrate of the design that uses the circuit
   (``jitx.current.substrate``). The pads need no copper spacing: clearance
   is not enforced between copper of the same net, and the stitch vias take
   the pour's net.
   JITX does not check this: on jitx 4.6 a pitch below the via
   pad is thinned to every other site and a pitch that breaks
   ``min_hole_to_hole`` is placed as asked, both with no design issue
   (measured with the sample substrate's 0.45 mm via: pitch 0.4 kept a
   checkerboard, pitch 0.5 put drills 0.2 mm apart).
3. A same-net anchor. A pour with no pad or via of its own net inside it
   comes back empty, and the rule's own stitch vias do not hold it. The
   runtime still places every stitch via on the removed pour's footprint,
   and reports no issue (measured on jitx 4.6, on a 10 mm square pour with
   a 2.0 mm grid: an empty pour and 25 vias). ``gnd_anchor`` is a
   code-placed GND via inside the pour.

What the runtime does with the grid, measured on jitx 4.6:

- The grid is absolute. Sites are multiples of the pitch from the board
  origin (0, 0), not from the pour, so moving a pour by less than a pitch
  moves its outline across a fixed lattice. The pour here is centred off the
  lattice on purpose.
- ``inset`` is measured from the via pad edge, not the via centre, to the
  computed pour boundary. That boundary already includes the pour's pullback
  from other-net copper, so a site is kept when a circle of radius
  ``pad / 2 + inset`` around it fits inside the computed pour copper.
- A site that fails is dropped. No via is moved or shrunk, and nothing is
  reported. The SIG route that crosses the pour here clears a band of sites.

The bottom-layer GND plane is not tagged. The through vias join it to the top
pour, which is what stitching is for.

To check a build, :py:func:`expected_stitch_sites` derives the sites a rule
must fill from the captured pours, and every one of them should hold a
generated via.
"""

import math
from collections.abc import Sequence

import jitx
from jitx.circuit import Circuit, Route
from jitx.constraints import (
    SquareViaStitchGrid,
    Tag,
    ViaStitchPattern,
    design_constraint,
)
from jitx.copper import Pour
from jitx.net import Net
from jitx.sample import SampleDesign, SampleSubstrate
from jitx.shapes.composites import rectangle
from jitx.substrate import FabricationConstraints
from jitx.via import Via
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from shapely.prepared import prep

STITCH_VIA = SampleSubstrate.THVia
"""The stitch via: the sample substrate's through via, pad 0.45 mm, drill 0.3 mm."""

STITCH_PITCH = 1.5
"""Centre-to-centre spacing of the stitch grid, mm."""

STITCH_INSET = 0.4
"""Via pad edge to computed pour boundary, mm."""

POUR_CENTER = (2.3, 1.1)
"""Centre of the stitched pour, deliberately off the 1.5 mm lattice."""


def min_stitch_pitch(via: type[Via], fab: FabricationConstraints) -> float:
    """Smallest pitch the runtime fills without thinning and the fab can drill.

    Pads: one pad diameter, since the runtime thins a pitch below the pad to
    a checkerboard; same-net pads need no copper spacing, because clearance
    is not enforced between copper of the same net. Drills: one hole diameter
    plus ``min_hole_to_hole``, an edge-to-edge spacing.
    """
    return max(float(via.diameter), via.hole_diameter + fab.min_hole_to_hole)


def checked_stitch_grid(
    via: type[Via], fab: FabricationConstraints, pitch: float, inset: float
) -> SquareViaStitchGrid:
    """A square stitch grid, refused when ``pitch`` is below ``min_stitch_pitch``."""
    floor = min_stitch_pitch(via, fab)
    if pitch < floor:
        raise ValueError(
            f"stitch pitch {pitch} mm is below {floor:.3f} mm, the larger of one "
            f"{via.__name__} pad (a smaller pitch thins the grid) and its drill "
            f"plus min_hole_to_hole"
        )
    return SquareViaStitchGrid(pitch=pitch, inset=inset)


INSET_SLACK = 0.02
"""Extra clearance, in mm, past ``inset`` before a stitch site is required.

Measured on jitx 4.6 by moving a row of sites toward the pour edge in 0.01
to 0.03 steps: the predicted threshold (pad radius plus inset, plus any
pullback) fell inside each keep or drop window. The nearest kept row sat
at most 0.018 past the predicted threshold, in two windows: drop at 0.86,
keep at 0.88, against 0.862; and drop at 0.55, keep at 0.58, against 0.562.
Where inside a window a site starts to hold was not measured, so a site
within 0.02 of the threshold is not required."""


def expected_stitch_sites(
    pours: Sequence[BaseGeometry],
    via: type[Via],
    grid: ViaStitchPattern,
    fab: FabricationConstraints,
    *,
    pads: Sequence[BaseGeometry] = (),
    placed_vias: Sequence[tuple[float, float]] = (),
    leave_out: BaseGeometry | None = None,
) -> set[tuple[float, float]]:
    """The lattice sites a square ``stitch_via`` rule must fill, in board frame.

    ``pours`` is the computed copper of every pour the rule stitches, each
    ``Pour.shape`` after capture in board frame; a through via crosses them
    all, so a site has to fit in each. ``pads`` is the pad copper near the
    pours, ``placed_vias`` the centres of the vias the design places in code,
    and ``leave_out`` a region whose sites are not required, such as the band
    a fence on the same pour displaces (measured on jitx 4.6: an inward fence
    0.6 in removed the stitch ring 1.0 in).

    A site is required when all of these hold, from what was measured on
    jitx 4.6:

    - it sits on a multiple of the pitch from the board origin (0, 0), not
      from the pour;
    - the via pad grown by ``grid.inset`` and by :py:data:`INSET_SLACK`
      lies inside every pour's computed copper, whose outline already
      includes the pullback from other-net copper; a site that fails is
      dropped, never moved or shrunk. A site that clears by less than the
      slack is not required either way;
    - its via pad comes no closer than ``min_copper_copper_space`` to a pad.
      Sites over pads were dropped on every layer; where a site near a pad
      starts to drop was not measured, so this is a margin for that edge,
      not a pitch requirement;
    - its centre is at least one via pad plus ``min_copper_copper_space``
      from a code-placed via. Sites 0.5 or closer to a code-placed via were
      dropped with 0.5 via pads, and the threshold between that and the next
      lattice site was not measured, so the same margin applies. The margin
      assumes each code-placed via has the stitch via's pad; for a larger
      code-placed via, pass its pad among ``pads`` instead;
    - its centre is outside ``leave_out``.

    A generated via that is not in the returned set is not a failure: the
    runtime may fill a site this derivation leaves out. Raises
    ``ValueError`` for a grid that is not a ``SquareViaStitchGrid`` (only the
    square lattice was measured), for no pours or an empty one, which would
    leave nothing to check, and for a pitch below
    :py:func:`min_stitch_pitch`, where the runtime thins the grid instead of
    filling it.
    """
    if not isinstance(grid, SquareViaStitchGrid):
        raise ValueError(
            f"{type(grid).__name__}: only a SquareViaStitchGrid's sites are derived"
        )
    if not pours:
        raise ValueError("no pours given, so there are no sites to require")
    for i, pour in enumerate(pours):
        if pour.is_empty:
            raise ValueError(
                f"pour {i} is empty: the rule has no copper there to stitch"
            )
    pitch, inset = grid.pitch, grid.inset
    floor = min_stitch_pitch(via, fab)
    if pitch < floor:
        raise ValueError(
            f"stitch pitch {pitch} mm is below {floor:.3f} mm, the smallest the "
            f"runtime fills without thinning and the fab can drill for {via.__name__}"
        )
    pad_radius = float(via.diameter) / 2
    space = fab.min_copper_copper_space
    inner = [prep(p.buffer(-(pad_radius + inset + INSET_SLACK))) for p in pours]
    minx = max(p.bounds[0] for p in pours)
    miny = max(p.bounds[1] for p in pours)
    maxx = min(p.bounds[2] for p in pours)
    maxy = min(p.bounds[3] for p in pours)
    sites: set[tuple[float, float]] = set()
    for i in range(math.floor(minx / pitch), math.ceil(maxx / pitch) + 1):
        for j in range(math.floor(miny / pitch), math.ceil(maxy / pitch) + 1):
            x, y = i * pitch, j * pitch
            site = Point(x, y)
            if not all(p.contains(site) for p in inner):
                continue
            if any(site.distance(pad) < pad_radius + space for pad in pads):
                continue
            if any(math.dist((x, y), v) < 2 * pad_radius + space for v in placed_vias):
                continue
            if leave_out is not None and leave_out.covers(site):
                continue
            sites.add((round(x, 6), round(y, 6)))
    return sites


class StitchedPourTag(Tag):
    """Pours with this tag are filled with stitch vias."""


class StitchedPour(Circuit):
    """A 12 mm by 9 mm GND pour on the top layer, stitched by rule, with a
    GND plane on the bottom layer and a SIG route crossing the pour."""

    def __init__(self) -> None:
        cx, cy = POUR_CENTER
        self.GND = Net(name="GND")
        self.gnd_pour = Pour(rectangle(12, 9).at(cx, cy), layer=0)
        StitchedPourTag().assign(self.gnd_pour)
        self.GND += self.gnd_pour

        self.gnd_plane = Pour(rectangle(30, 30), layer=1)
        self.GND += self.gnd_plane

        # Half a pitch off the lattice in both axes, so the anchor sits as far
        # from every stitch site as it can.
        self.gnd_anchor = STITCH_VIA().at(-2.25, -0.75)
        self.GND += self.gnd_anchor

        # Other-net copper through the pour: the pour pulls back from it and
        # the stitch sites near it are dropped.
        self.SIG = Net(name="SIG")
        self.sig_start = STITCH_VIA().at(-7, 4.5)
        self.sig_end = STITCH_VIA().at(11, 4.5)
        self.SIG += self.sig_start
        self.SIG += self.sig_end
        self.sig_route = Route(self.sig_start, self.sig_end, layer=0)

        # The fab floors come from the substrate of whatever design uses
        # this circuit.
        fab = jitx.current.substrate.constraints
        self.stitch_rule = design_constraint(StitchedPourTag()).stitch_via(
            STITCH_VIA, checked_stitch_grid(STITCH_VIA, fab, STITCH_PITCH, STITCH_INSET)
        )


class layout_stitched_pour_design(SampleDesign):
    """The stitched pour on the sample board and substrate."""

    circuit = StitchedPour()

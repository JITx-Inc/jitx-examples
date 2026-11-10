"""A board's default layout rules, and tagged nets whose rules override them.

Rules sit at three levels, and each level has its own home:

1. Fab floors live on the substrate. ``SampleSubstrate.constraints`` holds
   the fabricator's minimums (``min_copper_width``,
   ``min_copper_copper_space`` and the rest). They are limits, not choices:
   the rules below must not go under them, and ``check_against_fab``
   refuses a rule that would.
2. Board defaults live on the ``Design``. ``layout_default_rules_design``
   sets a 0.2 mm trace width for every trace (``IsTrace``), a 0.2 mm
   clearance between any two copper objects (``IsCopper``, ``IsCopper``) and
   a thermal relief for every pad (``IsPad``).
3. Rules on tags assigned to nets override the defaults at a higher
   priority. ``PowerTag`` is assigned to the power net and ``GroundTag`` to
   the ground net, and a priority-2 rule gives the nets carrying either tag
   a 0.5 mm trace. Nets tagged ``PowerTag`` also get a 0.3 mm clearance to
   any object.

The default relief is part of the defaults, not an extra. On jitx 4.6 a pad
that no ``thermal_relief`` rule matches is joined to its pour with no relief
at all: the pour meets the pad on every side. ``IsPad`` gives every pad a
relief, here four 0.25 mm spokes across a 0.25 mm gap. A relief rule at a
higher priority than the ``IsPad`` rule overrides it where it matches. Keyed
on a net tag, it relieves every pad on the net. Keyed on a tag on a pad, a
landpattern or a component, it picks out some of a net's pads;
``layout_thermal_classes`` shows such tags, one relief class per pad size.
Here ``GroundTag`` carries a width rule only, so the GND pads take the
``IsPad`` relief.

The circuit has one power route, one signal route and two GND pads inside a
GND pour. GND is not routed, so the ``GroundTag`` width rule has nothing to
act on in this design. Measured on jitx 4.6:

- the SIG route is 0.2 mm wide and the pour stops 0.21 mm from it, the
  default clearance plus 0.01 mm;
- the VCC route is 0.5 mm wide and the pour stops 0.31 mm from it, the
  ``PowerTag`` clearance plus 0.01 mm;
- each GND pad meets the pour through four spokes 0.25 mm wide across a
  0.25 mm gap.

Here the tag rules' values are also the larger ones, so these numbers alone
do not show whether priority or the larger value decided. A separate run
with the tag rules' values set below the defaults (0.15 mm width and
clearance) gave a 0.15 mm VCC route with the pour 0.16 mm from it: the
higher-priority tag rule applied.
"""

from jitx.circuit import Circuit, Route
from jitx.component import Component
from jitx.constraints import (
    AnyObject,
    BinaryDesignConstraint,
    DesignConstraint,
    IsCopper,
    IsPad,
    IsTrace,
    Tag,
    UnaryDesignConstraint,
    design_constraint,
)
from jitx.copper import Pour
from jitx.feature import Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Net, Port
from jitx.sample import SampleDesign
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Polyline
from jitx.substrate import FabricationConstraints
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.transform import Transform

DEFAULT_WIDTH = 0.2
"""Trace width for any trace no tag rule covers, mm."""

DEFAULT_CLEARANCE = 0.2
"""Clearance between any two copper objects, mm."""

RELIEF_GAP = 0.25
"""Gap between a pad and its pour, mm."""

RELIEF_SPOKE = 0.25
"""Width of each thermal spoke, mm."""

RELIEF_SPOKES = 4
"""Spokes per pad."""

POWER_WIDTH = 0.5
"""Trace width for power and ground nets, mm."""

POWER_CLEARANCE = 0.3
"""Clearance from power copper to any other object, mm."""


class PowerTag(Tag):
    """Power nets."""


class GroundTag(Tag):
    """Ground nets."""


def check_against_fab(
    rules: list[DesignConstraint], fab: FabricationConstraints
) -> list[DesignConstraint]:
    """Return ``rules`` unchanged, or raise if one goes under a fab floor.

    Widths are checked against ``min_copper_width``; clearances and relief
    gaps and spokes against ``min_copper_copper_space`` and
    ``min_copper_width``.
    """
    for rule in rules:
        values: list[tuple[str, float, float]] = []
        if isinstance(rule, UnaryDesignConstraint):
            if (tw := rule.trace_width_constraint) is not None:
                values.append(("trace width", tw.width, fab.min_copper_width))
            if (tr := rule.thermal_relief_constraint) is not None:
                space = fab.min_copper_copper_space
                values.append(("relief gap", tr.gap_distance, space))
                values.append(("relief spoke", tr.spoke_width, fab.min_copper_width))
        elif isinstance(rule, BinaryDesignConstraint):
            if (cl := rule.clearance_constraint) is not None:
                space = fab.min_copper_copper_space
                values.append(("clearance", cl.clearance, space))
        for what, value, floor in values:
            if value < floor:
                raise ValueError(f"{what} {value} mm is under the fab floor {floor} mm")
    return rules


class _SquarePad(Pad):
    def __init__(self, size: float) -> None:
        self.shape = rectangle(size, size)
        self.soldermask = Soldermask(rectangle(size + 0.1, size + 0.1))


class _TwoPadLandpattern(Landpattern):
    def __init__(self) -> None:
        self.p1 = _SquarePad(1.0).at(-1.5, 0)
        self.p2 = _SquarePad(1.0).at(1.5, 0)


class _TwoPinSymbol(Symbol):
    a = Pin(at=(-2, 0), length=1, direction=Direction.Left)
    b = Pin(at=(2, 0), length=1, direction=Direction.Right)
    body = Polyline(0.1, [(-1, 0), (1, 0)])


class TwoPad(Component):
    """A fictional part: two 1 mm square pads 3 mm apart."""

    reference_designator_prefix = "U"
    mpn = "EXAMPLE-2PAD"
    manufacturer = "Example"

    def __init__(self) -> None:
        self.landpattern = _TwoPadLandpattern()
        self.symbol = _TwoPinSymbol()
        self.a = Port()
        self.b = Port()
        self.mappings = [
            SymbolMapping({self.a: self.symbol.a, self.b: self.symbol.b}),
            PadMapping({self.a: self.landpattern.p1, self.b: self.landpattern.p2}),
        ]


class DefaultRulesCircuit(Circuit):
    """A VCC route and a SIG route through a GND pour, and two GND pads in it."""

    def __init__(self) -> None:
        self.src = TwoPad()
        self.dst = TwoPad()
        # Turned 90 degrees, so each part's pad a is at y -1.5 and pad b at
        # y 1.5, and the two routes run straight and parallel.
        self.place(self.src, Transform((-10, 0), 90))
        self.place(self.dst, Transform((10, 0), 90))
        self.VCC = Net([self.src.a, self.dst.a], name="VCC")
        self.SIG = Net([self.src.b, self.dst.b], name="SIG")
        PowerTag().assign(self.VCC)
        self.vcc_route = Route(self.src.a, self.dst.a, layer=0)
        self.sig_route = Route(self.src.b, self.dst.b, layer=0)

        self.gnd_part = TwoPad()
        self.place(self.gnd_part, Transform.translate(0, -5))
        self.GND = Net([self.gnd_part.a, self.gnd_part.b], name="GND")
        GroundTag().assign(self.GND)
        self.gnd_pour = Pour(rectangle(30, 16), layer=0)
        self.GND += self.gnd_pour


class layout_default_rules_design(SampleDesign):
    """The circuit on the sample board, with the board defaults and the
    power and ground tag rules on the design."""

    circuit = DefaultRulesCircuit()

    def __init__(self) -> None:
        fab = self.substrate.constraints
        self.rules = check_against_fab(
            [
                design_constraint(IsTrace).trace_width(DEFAULT_WIDTH),
                design_constraint(IsCopper, IsCopper).clearance(DEFAULT_CLEARANCE),
                design_constraint(IsPad).thermal_relief(
                    RELIEF_GAP, RELIEF_SPOKE, RELIEF_SPOKES
                ),
                design_constraint(PowerTag() | GroundTag(), priority=2).trace_width(
                    POWER_WIDTH
                ),
                design_constraint(PowerTag(), AnyObject, priority=2).clearance(
                    POWER_CLEARANCE
                ),
            ],
            fab,
        )

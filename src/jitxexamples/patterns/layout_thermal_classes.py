"""Thermal relief sized per pad class, a direct connect for a power pad, and
a pad that no relief rule matches.

A design rule's condition is made of tags, so it cannot ask how big a pad is.
To give small and large pads different reliefs, measure each landpattern's
pads in Python, put a class tag on each pad, and key one relief rule on each
class tag. On a real board, also keep an ``IsPad`` relief rule at a priority
below the class rules, as ``layout_default_rules`` does: without it, every
pad you did not tag joins its pour solidly, and no design issue reports it.
This design leaves that rule out to show the solid join. The pieces:

- ``tag_pads_by_size`` visits a component's pads, measures the narrow side of
  each pad's shape, and assigns ``SmallPadRelief`` below 1.0 mm
  (``SMALL_PAD_LIMIT``) and ``LargePadRelief`` from there up.
- ``SMALL_RELIEF`` (a 0.2 mm gap, two 0.2 mm spokes) and ``LARGE_RELIEF``
  (a 0.3 mm gap, four 0.4 mm spokes) give each class its relief. A small pad
  gets two narrow spokes, so the relief does not swallow it; a large pad gets
  four wide ones, so it carries current.
- ``DirectConnectTag`` on the power part's exposed pad, with a rule at a
  higher priority, joins that pad to the pour solidly. The rule set has no
  direct-connect effect, so the rule is a relief whose spoke width is the
  pad's diagonal: the spokes overlap until no gap is left. A pad that no
  relief rule matches also joins solidly, but the direct connect is still
  written as a rule, for two reasons: here ``tag_pads_by_size`` also gives
  the exposed pad ``LargePadRelief``, and on a board with an ``IsPad``
  default every pad is matched. Either way the solid join has to win by
  priority.
- The ``untagged`` part is the same part as the large one, 1.6 mm pads, with
  no class tag, and the design has no ``IsPad`` rule, so no relief rule
  matches its pads. It shows what a pad gets with no rule: a solid join to
  the pour, with no void and no design issue. Do not copy that omission:
  the ``IsPad`` rule in ``layout_default_rules`` gives such a pad a relief.

Where the tag goes follows from which pads the rule is for. A relief rule
keyed on a tag assigned to a net reaches every pad on that net. A pad-size
class depends on the pad, not the net: the one GND net here has small, large
and exposed pads, so the class tags go on the pads. A tag on a landpattern or
a component also works, for a part whose pads all take one class. ``IsPad``
reaches every pad. When two relief rules match one pad, the higher priority
wins. At equal priority the same rule won on repeated runs in testing, but
the rule that decides the winner is not established, so give overlapping
classes different priorities.

All parts are on GND inside one GND pour on the top layer. Measured on jitx
4.6 from the computed pour copper around each pad:

- each small pad has a 0.2 mm gap and two 0.2 mm spokes;
- each large pad has a 0.3 mm gap and four 0.4 mm spokes;
- the exposed pad meets the pour on every side, with no void;
- each pad of the untagged part meets the pour on every side, with no void.
"""

from jitx.circuit import Circuit
from jitx.component import Component
from jitx.constraints import (
    Tag,
    ThermalRelief,
    UnaryDesignConstraint,
    design_constraint,
)
from jitx.copper import Pour
from jitx.feature import Soldermask
from jitx.inspect import visit
from jitx.landpattern import Landpattern, Pad, PadMapping, PadShape
from jitx.net import Net, Port
from jitx.sample import SampleDesign
from jitx.shapes import Shape
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Polyline
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.transform import Transform

SMALL_PAD_LIMIT = 1.0
"""Pads whose narrow side is under this, in mm, take the small-pad relief."""

SMALL_RELIEF = ThermalRelief(gap_distance=0.2, spoke_width=0.2, num_spokes=2)
"""Relief for small pads: 0.2 mm gap, two 0.2 mm spokes."""

LARGE_RELIEF = ThermalRelief(gap_distance=0.3, spoke_width=0.4, num_spokes=4)
"""Relief for large pads: 0.3 mm gap, four 0.4 mm spokes."""

DIRECT_CONNECT_GAP = 0.2
"""Gap of the direct-connect relief, mm; the spokes close it."""


class SmallPadRelief(Tag):
    """Pads whose narrow side is under ``SMALL_PAD_LIMIT``."""


class LargePadRelief(Tag):
    """Pads whose narrow side is ``SMALL_PAD_LIMIT`` or more."""


class DirectConnectTag(Tag):
    """Pads joined to their pour with no relief."""


def pad_size(pad: Pad) -> tuple[float, float]:
    """Width and height of a pad's copper shape, mm."""
    shape: Shape = pad.shape.shape if isinstance(pad.shape, PadShape) else pad.shape
    x0, y0, x1, y1 = shape.to_shapely().g.bounds
    return x1 - x0, y1 - y0


def tag_pads_by_size(part: Component) -> None:
    """Assign each pad of ``part`` the relief class its measured size calls for."""
    for _, pad in visit(part, Pad):
        if min(pad_size(pad)) < SMALL_PAD_LIMIT:
            SmallPadRelief().assign(pad)
        else:
            LargePadRelief().assign(pad)


class _RectPad(Pad):
    def __init__(self, width: float, height: float) -> None:
        self.shape = rectangle(width, height)
        self.soldermask = Soldermask(rectangle(width + 0.1, height + 0.1))


class _TwoPinSymbol(Symbol):
    a = Pin(at=(-2, 0), length=1, direction=Direction.Left)
    b = Pin(at=(2, 0), length=1, direction=Direction.Right)
    body = Polyline(0.1, [(-1, 0), (1, 0)])


class _ChipLandpattern(Landpattern):
    def __init__(self, width: float, height: float, pitch: float) -> None:
        self.p1 = _RectPad(width, height).at(-pitch / 2, 0)
        self.p2 = _RectPad(width, height).at(pitch / 2, 0)


class ChipPart(Component):
    """A fictional two-pad part with ``width`` by ``height`` mm pads."""

    reference_designator_prefix = "C"
    mpn = "EXAMPLE-CHIP"
    manufacturer = "Example"

    def __init__(self, width: float, height: float, pitch: float) -> None:
        self.landpattern = _ChipLandpattern(width, height, pitch)
        self.symbol = _TwoPinSymbol()
        self.a = Port()
        self.b = Port()
        self.mappings = [
            SymbolMapping({self.a: self.symbol.a, self.b: self.symbol.b}),
            PadMapping({self.a: self.landpattern.p1, self.b: self.landpattern.p2}),
        ]


class _PowerLandpattern(Landpattern):
    def __init__(self) -> None:
        self.exposed = _RectPad(3.0, 3.0).at(0, 0)
        self.sense = _RectPad(0.6, 0.6).at(0, -2.5)


class PowerPart(Component):
    """A fictional power part: a 3 mm exposed pad and a 0.6 mm sense pad."""

    reference_designator_prefix = "U"
    mpn = "EXAMPLE-POWER"
    manufacturer = "Example"

    def __init__(self) -> None:
        self.landpattern = _PowerLandpattern()
        self.symbol = _TwoPinSymbol()
        self.gnd = Port()
        self.sense = Port()
        self.mappings = [
            SymbolMapping({self.gnd: self.symbol.a, self.sense: self.symbol.b}),
            PadMapping(
                {
                    self.gnd: self.landpattern.exposed,
                    self.sense: self.landpattern.sense,
                }
            ),
        ]


def _relief_rule(
    condition: Tag, relief: ThermalRelief, priority: int
) -> UnaryDesignConstraint:
    return design_constraint(condition, priority=priority).thermal_relief(
        relief.gap_distance, relief.spoke_width, relief.num_spokes
    )


class ThermalClasses(Circuit):
    """A small-pad part, a large-pad part, an untagged copy of the large-pad
    part and a power part, all on GND in one GND pour, with a relief class per
    pad size, a direct connect and no default relief."""

    def __init__(self) -> None:
        self.small = ChipPart(0.6, 0.6, 1.6)
        self.large = ChipPart(1.6, 1.6, 4.0)
        self.untagged = ChipPart(1.6, 1.6, 4.0)
        self.power = PowerPart()
        self.place(self.small, Transform.translate(-13, 0))
        self.place(self.large, Transform.translate(-5, 0))
        self.place(self.untagged, Transform.translate(5, 0))
        self.place(self.power, Transform.translate(13, 0))
        self.GND = Net(
            [
                self.small.a,
                self.small.b,
                self.large.a,
                self.large.b,
                self.untagged.a,
                self.untagged.b,
                self.power.gnd,
                self.power.sense,
            ],
            name="GND",
        )
        self.gnd_pour = Pour(rectangle(36, 14), layer=0)
        self.GND += self.gnd_pour

        # The untagged part is left out on purpose: no relief rule matches it.
        for part in (self.small, self.large, self.power):
            tag_pads_by_size(part)
        # The exposed pad also has LargePadRelief from its size; the direct
        # connect rule's higher priority wins.
        exposed = self.power.landpattern.exposed
        DirectConnectTag().assign(exposed)

        width, height = pad_size(exposed)
        diagonal = (width**2 + height**2) ** 0.5
        self.rules = [
            _relief_rule(SmallPadRelief(), SMALL_RELIEF, priority=3),
            _relief_rule(LargePadRelief(), LARGE_RELIEF, priority=3),
            design_constraint(DirectConnectTag(), priority=4).thermal_relief(
                DIRECT_CONNECT_GAP, diagonal, 4
            ),
        ]


class layout_thermal_classes_design(SampleDesign):
    """The four parts and their pour on the sample board."""

    circuit = ThermalClasses()

"""
0826-1G1T-23-F / Gigabit RJ45 MagJack
=====================================

This module provides a component definition for the Bel Fuse 0826-1G1T-23-F,
a tab-up RJ45 jack with integrated 1000Base-T magnetics and two green LEDs, and
a circuit that provides the ethernet MDI protocols through pin assignment.

Every number here comes from Bel Fuse drawing 08261G1T23-F, revision F:

- page 2, schematic and LED polarity table: pin functions;
- page 3, front and side views: body width, height and length;
- page 4, recommended PCB footprint (component side view): hole positions and
  diameters, and the areas to keep clear of vias and pads.

The drawing dimensions are in inches (millimetres for reference). Each page's
title block gives its own tolerance for three-place inch dimensions: +/-0.010
on page 3, which the package body takes, and +/-0.004 on page 4, the footprint.
Positions below are written in inches from the drawing's datum, the midpoint
between the two mounting posts, with +y toward the front (cable) face, and
converted to millimetres.

The drawing also states facts with no field here: the cable-side termination
(four 75 Ohm resistors and a 1000 pF 2 kV capacitor to SHIELD) is inside the
jack, so the jack has no cable-side pins; LED forward voltage is 2.2 V typical
at 20 mA; hipot isolation is 1500 Vrms; operating temperature is 0 to 70 C.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import override

from jitx.anchor import Anchor
from jitx.circuit import Circuit
from jitx.common import Polarized
from jitx.component import Component
from jitx.feature import KeepOut
from jitx.landpattern import PadMapping
from jitx.layerindex import LayerSet
from jitx.net import DiffPair, Net, Port, provide
from jitx.shapes import Shape
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle
from jitx.toleranced import Toleranced
from jitx.transform import Transform
from jitxlib.landpatterns.courtyard import (
    CourtyardGeneratorMixin,
    ExcessCourtyardGenerator,
)
from jitxlib.landpatterns.grid_layout import (
    GridLayoutInterface,
    GridPosition,
    LinearNumbering,
)
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.landpatterns.pads import (
    GridPadShapeGeneratorMixin,
    NPTHPad,
    THPadAdjustment,
    THPadConfig,
)
from jitxlib.landpatterns.silkscreen.outlines import PackageBased, SilkscreenOutline
from jitxlib.protocols.ethernet.mdi.mdi1000base_t import MDI1000BaseT
from jitxlib.protocols.ethernet.mdi.mdi100base_tx import MDI100BaseTX
from jitxlib.symbols.box import BoxSymbol, PinGroup, Row

INCH = 25.4
"""Millimetres per inch; the drawing's standard unit is the inch."""

BODY_TOLERANCE = 0.010 * INCH
"""Page 3, title block: the tolerance for three-place inch dimensions."""

BODY_WIDTH = 0.642 * INCH
"""Page 3, front view."""

BODY_HEIGHT = 0.536 * INCH
"""Page 3, front view."""

BODY_LENGTH = 1.290 * INCH
"""Page 3, side view, front face to the rear of the body."""

BODY_FRONT = 0.430
"""Page 3 side view (0.305 + 0.125) and page 4 keep-out view: the front face
is 0.430 inch in front of the mounting posts."""

BODY_CENTER_Y = BODY_FRONT - BODY_LENGTH / INCH / 2.0
"""Body center from the datum, in inches."""

SIGNAL_HOLE = 0.035 * INCH
"""Page 4: 12 signal leads, 0.035 inch +0.005/-0.000."""

LED_HOLE = 0.040 * INCH
"""Page 4: 4 LED leads, 0.040 inch +0.005/-0.000."""

SHIELD_HOLE = 0.062 * INCH
"""Page 4: 2 places."""

POST_HOLE = 0.128 * INCH
"""Page 4: 2 places, the non-plated mounting posts."""

POST_X = 0.500 / 2.0
"""Page 4: posts 0.500 inch apart, on the datum line."""

SHIELD_X = 0.635 / 2.0
"""Page 4: shield holes 0.635 inch apart, 0.0675 inch outboard of the posts."""

SHIELD_Y = 0.125
"""Page 4: shield holes 0.125 inch in front of the posts."""

PIN_POSITIONS: dict[int, tuple[float, float]] = {
    # Page 4. Row 1, 0.600 inch behind the posts, 0.080 inch pitch.
    1: (-0.200, -0.600),
    2: (-0.120, -0.600),
    3: (-0.040, -0.600),
    4: (0.040, -0.600),
    5: (0.120, -0.600),
    6: (0.200, -0.600),
    # Row 2, 0.700 inch behind the posts, offset 0.040 inch from row 1.
    7: (-0.240, -0.700),
    8: (-0.160, -0.700),
    9: (-0.080, -0.700),
    10: (0.080, -0.700),
    11: (0.160, -0.700),
    12: (0.240, -0.700),
    # LED row, 0.800 inch behind the posts: 13 to 16 span 0.480 inch, 14 to
    # 15 span 0.280 inch.
    13: (-0.240, -0.800),
    14: (-0.140, -0.800),
    15: (0.140, -0.800),
    16: (0.240, -0.800),
}
"""Lead positions in inches from the datum, by pin number."""


class Bel_0826_1G1T_23_F(Circuit):
    """
    0826-1G1T-23-F Connector Module

    This is the preferred usage point for this connector component.

    The user is expected to use a :py:meth:`~jitx.circuit.Circuit.require`
    statement to extract the 1000Base-T or 100Base-T interface for their
    application. Pair A is TRD1 (RJ45 pins 1 and 2), B is TRD2 (3 and 6),
    C is TRD3 (4 and 5) and D is TRD4 (7 and 8).
    """

    CT = {i: Port() for i in range(1, 5)}
    """Device-side center taps, ``CT[n]`` on TRCTn, one per pair (A to D)."""

    LED1 = Polarized()
    """Green LED 1: anode pin 14, cathode pin 13."""

    LED2 = Polarized()
    """Green LED 2: anode pin 16, cathode pin 15."""

    SHIELD = Port()
    """Chassis shield; the internal cable-side termination returns here."""

    J: Bel_0826_1G1T_23_F.Component
    """The actual connector component instance with landpattern."""

    def __init__(self) -> None:
        self.J = Bel_0826_1G1T_23_F.Component()

        self.TRCT = {i: self.CT[i] + self.J.TRCT[i] for i in range(1, 5)}
        self.LED1_A = self.LED1.a + self.J.LED1_A
        self.LED1_C = self.LED1.c + self.J.LED1_C
        self.LED2_A = self.LED2.a + self.J.LED2_A
        self.LED2_C = self.LED2.c + self.J.LED2_C
        self.shield = Net([self.SHIELD])
        for p in self.J.SHIELD.values():
            self.shield += p

        self += MDI1000BaseT.Provide(
            (self.J.TRD[1], self.J.TRD[2], self.J.TRD[3], self.J.TRD[4])
        )

    @provide(MDI100BaseTX)
    def provide_mdi100base_tx(
        self, mdi100base_tx: MDI100BaseTX
    ) -> list[dict[Port, Port]]:
        return [
            {
                mdi100base_tx.TX.p: self.J.TRD[1].p,
                mdi100base_tx.TX.n: self.J.TRD[1].n,
                mdi100base_tx.RX.p: self.J.TRD[2].p,
                mdi100base_tx.RX.n: self.J.TRD[2].n,
            }
        ]

    class Component(Component):
        """
        Gigabit MagJack, 12 cores, tab up

        RJ45 connector with integrated 1000Base-T magnetics and two green LEDs.
        This is the base physical connector. It encodes part information
        including the symbol and landpattern.

        Use the circuit instead of this component directly unless you need
        custom handling.
        """

        manufacturer = "Bel Fuse"
        mpn = "0826-1G1T-23-F"
        datasheet = "https://www.belfuse.com/media/drawings/products/magjack%20ICMs/dr-mag-0826-1g1t-23-f.pdf"
        reference_designator_prefix = "J"

        TRD = {i: DiffPair() for i in range(1, 5)}
        """Device-side pair n: TRDn+ is ``.p``, TRDn- is ``.n``."""

        TRCT = {i: Port() for i in range(1, 5)}
        """Device-side center tap of pair n."""

        LED1_A = Port()
        LED1_C = Port()
        LED2_A = Port()
        LED2_C = Port()
        SHIELD = {i: Port() for i in range(1, 3)}

        def __init__(self) -> None:
            lp = Bel_0826_1G1T_23_F.Landpattern()
            self.landpattern = lp
            # Page 2 schematic and LED polarity table.
            self.pad_mapping = PadMapping(
                {
                    self.TRCT[3]: lp.p[1],
                    self.TRD[3].n: lp.p[2],
                    self.TRD[3].p: lp.p[3],
                    self.TRD[2].p: lp.p[4],
                    self.TRD[2].n: lp.p[5],
                    self.TRCT[2]: lp.p[6],
                    self.TRCT[4]: lp.p[7],
                    self.TRD[4].p: lp.p[8],
                    self.TRD[4].n: lp.p[9],
                    self.TRD[1].n: lp.p[10],
                    self.TRD[1].p: lp.p[11],
                    self.TRCT[1]: lp.p[12],
                    self.LED1_C: lp.p[13],
                    self.LED1_A: lp.p[14],
                    self.LED2_C: lp.p[15],
                    self.LED2_A: lp.p[16],
                    self.SHIELD[1]: lp.p[17],
                    self.SHIELD[2]: lp.p[18],
                }
            )
            pairs = [
                PinGroup([self.TRD[i].p, self.TRCT[i], self.TRD[i].n])
                for i in range(1, 5)
            ]
            self.symbol = BoxSymbol(
                rows=[
                    Row(
                        left=pairs,
                        right=[
                            PinGroup([self.LED1_A, self.LED1_C]),
                            PinGroup([self.LED2_A, self.LED2_C], pre_margin=1.0),
                            PinGroup(list(self.SHIELD.values()), pre_margin=1.0),
                        ],
                    ),
                ],
                columns=[],
            )

    class Landpattern(
        GridPadShapeGeneratorMixin,
        CourtyardGeneratorMixin,
        SilkscreenOutline,
        LinearNumbering,
        GridLayoutInterface,
    ):
        """Page 4 footprint. Pads 1 to 16 are the drawing's pins, 17 and 18
        the left and right shield holes; the mounting posts are non-plated."""

        mounts: Sequence[NPTHPad]

        @override
        def _generate_layout(self) -> Iterator[GridPosition]:
            at = Transform.translate
            for pin, (x, y) in PIN_POSITIONS.items():
                row = 0 if pin <= 12 else 1
                yield GridPosition(row=row, column=pin, pose=at(x * INCH, y * INCH))
            for column, x in enumerate((-SHIELD_X, SHIELD_X)):
                yield GridPosition(
                    row=2, column=column, pose=at(x * INCH, SHIELD_Y * INCH)
                )

        @override
        def _pad_shape(self, pos: GridPosition) -> Shape:
            match pos.row:
                case 0:
                    return Circle(diameter=SIGNAL_HOLE)
                case 1:
                    return Circle(diameter=LED_HOLE)
                case 2:
                    return Circle(diameter=SHIELD_HOLE)
                case _:
                    raise ValueError(f"Unknown row {pos.row}")

        @override
        def _build(self) -> None:
            self.mounts = []
            super()._build()
            del self.mounts  # ensure it's at the end of the traversal.
            self.mounts = [
                NPTHPad(Circle(diameter=POST_HOLE)).at(-POST_X * INCH, 0.0),
                NPTHPad(Circle(diameter=POST_HOLE)).at(POST_X * INCH, 0.0),
            ]

        def __init__(self) -> None:
            super().__init__()
            # Place the land pattern origin at the body center.
            self.at(0.0, -BODY_CENTER_Y * INCH)
            self.pad_config(THPadConfig(copper=THPadAdjustment()))
            pkg = RectanglePackage(
                width=Toleranced(BODY_WIDTH, BODY_TOLERANCE),
                length=Toleranced(BODY_LENGTH, BODY_TOLERANCE),
                height=Toleranced(BODY_HEIGHT, BODY_TOLERANCE),
            )
            assert self.transform  # set by self.at above
            pkg.transform = self.transform.inverse()
            self.package_body(pkg)
            self.silkscreen_outline(PackageBased())
            self.keepout = [
                KeepOut(shape, LayerSet(0), pour=True) for shape in build_keepout()
            ]
            self.courtyard(ExcessCourtyardGenerator())


def build_keepout() -> list[Shape]:
    """Page 4 keep-out view, in the datum frame: the shaded areas to keep
    clear of vias and pads. Outer edges 0.702 inch apart, inner edges 0.472
    inch apart. A bar 0.120 inch deep along the front face, legs from the
    front face to 0.290 inch behind it, and blocks from 0.965 to 1.220 inch
    behind it."""
    outer = 0.702 / 2.0
    inner = 0.472 / 2.0
    leg = outer - inner
    return [
        rectangle(0.702 * INCH, 0.120 * INCH, anchor=Anchor.N).at(
            0.0, BODY_FRONT * INCH
        ),
        rectangle(leg * INCH, 0.290 * INCH, anchor=Anchor.NW).at(
            -outer * INCH, BODY_FRONT * INCH
        ),
        rectangle(leg * INCH, 0.290 * INCH, anchor=Anchor.NE).at(
            outer * INCH, BODY_FRONT * INCH
        ),
        rectangle(leg * INCH, (1.220 - 0.965) * INCH, anchor=Anchor.NW).at(
            -outer * INCH, (BODY_FRONT - 0.965) * INCH
        ),
        rectangle(leg * INCH, (1.220 - 0.965) * INCH, anchor=Anchor.NE).at(
            outer * INCH, (BODY_FRONT - 0.965) * INCH
        ),
    ]


Device: type[Bel_0826_1G1T_23_F] = Bel_0826_1G1T_23_F

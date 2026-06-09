"""
JD0-0001NL / RJ45 Ethernet Connector
====================================

This module provides a component definition for the JD0-0001NL / RJ45
connector, including a circuit using pin assingment to provide ethernet
protocols.
"""

from __future__ import annotations
from collections.abc import Sequence
from typing import override

from jitx.anchor import Anchor
from jitx.circuit import Circuit
from jitx.common import Polarized
from jitx.component import Component
from jitx.feature import KeepOut
from jitx.layerindex import LayerSet
from jitx.net import DiffPair, Net, Port, provide
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


JD0_0001NL_LENGTH = 21.35
JD0_0001NL_WIDTH = 15.90
JD0_0001NL_HEIGHT = 13.63
JD0_0001NL_TOL = 0.25

JD0_0001NL_CENTER_TX = (2.24 - JD0_0001NL_WIDTH / 2.0, 10.75 - JD0_0001NL_LENGTH / 2.0)
"""The mechanical drawing for this part shows the origin as one of the
mechanical mounting holes and all measurements are made from that datum. For the
landpattern, we would like the origin to be the center of mass. This is the
transform which translates the center of mass to the mechanical origin.
"""


class JD0_0001NL(Circuit):
    """
    JD0-0001NL Connector Module

    This is the preferred usage point for this connector component.

    The user is expected to use a :py:meth:`~jitx.circuit.Circuit.require`
    statement to extract the 1000Base-T or 100Base-T interface for their
    application.
    """

    CT = Port()
    """Device-Side Center Tap - Non-Isolated"""

    ISO_CT = Port()
    """Isolated Cable-Side Center Tap - Isolated"""

    LED_G = Polarized()
    """Green Status LED"""

    LED_Y = Polarized()
    """Yellow Status LED"""

    SHIELD = Port()
    """Chassis Shield Connection for the Connector"""

    J: JD0_0001NL.Component
    """The actual connector component instance with landpattern."""

    def __init__(self):
        self.J = JD0_0001NL.Component()

        self.nets = [
            self.CT + self.J.CT,
            self.ISO_CT + self.J.ISO_CT,
            self.LED_G.a + self.J.LED_G_A,
            self.LED_G.c + self.J.LED_G_C,
            self.LED_Y.a + self.J.LED_Y_A,
            self.LED_Y.c + self.J.LED_Y_C,
        ]
        self.shield = Net([self.SHIELD])

        for p in self.J.SHIELD.values():
            self.shield += p

        self += MDI1000BaseT.Provide((self.J.DA, self.J.DB, self.J.DC, self.J.DD))

    @provide(MDI100BaseTX)
    def provide_mdi100base_tx(self, mdi100base_tx: MDI100BaseTX):
        return [
            {
                mdi100base_tx.TX.p: self.J.DA.p,
                mdi100base_tx.TX.n: self.J.DA.n,
                mdi100base_tx.RX.p: self.J.DB.p,
                mdi100base_tx.RX.n: self.J.DB.n,
            }
        ]

    class Component(Component):
        """
        CONN JACK 1PORT 1000 BASE-T PCB

        RJ45 Connector supporting 1000Base-T Ethernet

        This is the base physical connector. It encodes
        part information including the symbol and landpattern.

        We suggest leveraging the circuit instead of this component directly unless
        you need to add some custom handling.
        """

        name = "553-2359-ND"
        manufacturer = "Pulse Electronics"
        mpn = "JD0-0001NL"
        datasheet = "https://productfinder.pulseelectronics.com/api/open/part-attachments/datasheet/JD0-0001NL"
        reference_designator_prefix = "J"

        CT = Port()
        DA = DiffPair()
        DB = DiffPair()
        DC = DiffPair()
        DD = DiffPair()
        ISO_CT = Port()
        LED_G_A = Port()
        LED_G_C = Port()
        LED_Y_A = Port()
        LED_Y_C = Port()
        SHIELD = {i: Port() for i in range(1, 3)}

        def __init__(self):
            self.landpattern = JD0_0001NL.Landpattern()
            self.symbol = BoxSymbol(
                rows=[
                    Row(
                        left=[
                            PinGroup(
                                [
                                    self.DA.p,
                                    self.DA.n,
                                    self.DB.p,
                                    self.DB.n,
                                    self.DC.p,
                                    self.DC.n,
                                    self.DD.p,
                                    self.DD.n,
                                ]
                            )
                        ],
                        right=[
                            PinGroup([self.LED_G_A, self.LED_G_C]),
                            PinGroup([self.LED_Y_A, self.LED_Y_C], pre_margin=1.0),
                        ],
                    ),
                    Row(
                        left=[PinGroup([self.CT])],
                        right=[
                            PinGroup([self.ISO_CT]),
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
        mounts: Sequence[NPTHPad]

        @override
        def _generate_layout(self):
            at = Transform.translate

            # P1-P10, row 0-1
            pitch = 2.54
            y0 = (8.89, 6.35)
            x0 = (0, 1.27)
            for i in range(10):
                row = i & 1
                column = i // 2
                yield GridPosition(
                    row=row, column=column, pose=at(x0[row] + pitch * column, y0[row])
                )

            # P11-P14, row 2
            y = -4.06
            for i, x in [(0, -0.93), (1, 1.62), (2, 9.82), (3, 11.43 + 0.93)]:
                yield GridPosition(row=2, column=i, pose=at(x, y))

            # shield, row "3"
            y = 3.05
            for i, x in [(0, -2.14), (1, 13.57)]:
                yield GridPosition(row=3, column=i, pose=at(x, y))

            # mounting holes are NPTH, so we don't generate pads for them.

        @override
        def _pad_shape(self, pos: GridPosition):
            match pos.row:
                case 0 | 1:
                    return Circle(diameter=0.9)
                case 2:
                    return Circle(diameter=1.2)
                case 3:
                    return Circle(diameter=1.6)
                case _:
                    raise ValueError(f"Unknown row {pos.row}")

        @override
        def _build(self):
            self.mounts = []
            super()._build()
            del self.mounts  # ensure it's at the end of the traversal.
            self.mounts = [
                NPTHPad(Circle(diameter=3.25)).at(0.0, 0.0),
                NPTHPad(Circle(diameter=3.25)).at(11.43, 0.0),
            ]

        def __init__(self):
            super().__init__()
            # place landpattern at center of mass
            self.at(JD0_0001NL_CENTER_TX)
            self.pad_config(THPadConfig(copper=THPadAdjustment()))
            pkg = RectanglePackage(
                width=Toleranced(JD0_0001NL_WIDTH, JD0_0001NL_TOL),
                length=Toleranced(JD0_0001NL_LENGTH, JD0_0001NL_TOL),
                height=Toleranced(JD0_0001NL_HEIGHT, JD0_0001NL_TOL),
            )

            # compensate center for package body
            assert self.transform  # set by self.at above
            pkg.transform = self.transform.inverse()
            self.package_body(pkg)
            self.silkscreen_outline(PackageBased())
            self.keepout = [
                KeepOut(shape, LayerSet(0), pour=True) for shape in self.build_keepout()
            ]
            # use radius of shield mount pad so courtyard can cover it
            self.courtyard(ExcessCourtyardGenerator(1.6 / 2))

        def build_keepout(self):
            small_ko_box_width = 2.24 - 0.93
            small_ko_box_length = 2.0
            large_ko_box_width = 12.72 + 1.29
            large_ko_box_length = 10.75 - 8.05
            return [
                rectangle(small_ko_box_width, small_ko_box_length, anchor=Anchor.NE).at(
                    13.67, 2.0
                ),
                rectangle(small_ko_box_width, small_ko_box_length, anchor=Anchor.NE).at(
                    -0.93, 2.0
                ),
                rectangle(large_ko_box_width, large_ko_box_length, anchor=Anchor.NW).at(
                    -1.29, -8.05
                ),
            ]


Device: type[JD0_0001NL] = JD0_0001NL

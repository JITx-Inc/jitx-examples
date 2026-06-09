"""
TOGIA Side-firing Red LED
===========================

Component definition for TOGIA Side firing LEDs
"""

from jitx.anchor import Anchor
from jitx.component import Component
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.landpattern import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolygon, ArcPolyline, Polygon, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol
from jitx.symbol import SymbolMapping
from jitx.transform import Transform


class RectangleSmdPad(Pad):
    shape = rectangle(1, 0.9)
    paste = [
        Paste(rectangle(1.102, 1.002)),
    ]
    soldermask = [
        Soldermask(rectangle(1.102, 1.002)),
    ]


class RectangleSmdPad1(Pad):
    shape = rectangle(0.8, 1.2)
    paste = [
        Paste(rectangle(0.902, 1.302)),
    ]
    soldermask = [
        Soldermask(rectangle(0.902, 1.302)),
    ]


class LandpatternLED_SMD_3P_L3_2_W1_0_RD_RED(Landpattern):
    p = {
        1: RectangleSmdPad1().at(Transform((-1.527, 0.067), 90)),
        2: RectangleSmdPad1().at(Transform((1.473, 0.067), 90)),
        3: RectangleSmdPad().at(Transform((-0.027, -0.44), 180)),
    }

    customlayer = [
        Custom(Text(">VALUE", 0.5, Anchor.W).at((-0.75, 1.6466)), name="Fab"),
        Custom(ArcPolyline(0.06, [Arc((-1.627, 1.316), 0.03, 0, -360)]), name="Fab"),
        Custom(
            ArcPolygon(
                [
                    (1.625, -0.393),
                    (1.624, -0.393),
                    (1.438, -0.393),
                    (1.438, 0.532),
                    (1.624, 0.532),
                    (1.624, -0.393),
                    (1.625, -0.393),
                    (1.625, -0.393),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (1.07, -0.006),
                    (1.07, -0.005),
                    (1.071, 0.182),
                    (1.995, 0.182),
                    (1.995, -0.005),
                    (1.07, -0.005),
                    (1.07, -0.006),
                    (1.07, -0.006),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (-1.995, 0.053),
                    (-1.995, 0.054),
                    (-1.995, 0.24),
                    (-1.07, 0.24),
                    (-1.07, 0.054),
                    (-1.995, 0.054),
                    (-1.995, 0.053),
                    (-1.995, 0.053),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (-0.897, 0.824),
                    (0.833, 0.824),
                    Arc((-0.027, 0.42), 0.893, 45.0011, 44.9988),
                    Arc((-0.027, 0.396), 0.917, 90, 45),
                    (-0.897, 0.824),
                    (-0.897, 0.824),
                ]
            ),
            name="Fab",
        ),
    ]
    silkscreen = [
        Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 2.6466))),
        # Silkscreen(Polyline(0.254, [(-0.717, 0.814), (0.621, 0.814)])),
        # Silkscreen(ArcPolyline(0.254, [
        #     Arc((-0.002, 0.479), 1.087, 167.999, -152.9977)])),
        # Silkscreen(ArcPolygon([
        #     (-0.467, 0.644),
        #     (-0.467, 0.104),
        #     (-0.627, 0.104),
        #     (-0.627, 0.644),
        #     (-0.467, 0.644),
        #     (-0.467, 0.644)])),
        # Silkscreen(Text("L", 0.3937, Anchor.C).at((1.283, -1.5))),
    ]

    courtyard = Courtyard(rectangle(3.99, 1.882))
    model3d = Model3D(
        "togialed_TJ_S3210SW5TGLC2R_A5.stp",
        position=(0, -0.6, 0),
        scale=(1, 1, 1),
        rotation=(0, 0, 0),
    )


class SymbolTJ_S3210SW5TGLC2R_A5(Symbol):
    p = {
        1: Pin((-1, 0), 3, Direction.Left),
        2: Pin((1, 0), 3, Direction.Right),
        3: Pin((0, -1), 3, Direction.Down),
    }
    value_label = Text(">VALUE", 0.55559, Anchor.C).at((0, 4.98741))
    reference_designator = Text(">REF", 0.55559, Anchor.C).at((0, 5.77481))
    shapes = [
        Polyline(0.254, [(-1, 2), (-2.4, 3.4)]),
        Polyline(0.254, [(-0.2, 2.8), (-1.6, 4.2)]),
        Polyline(0.254, [(-1, -1.4), (-1, 1.4)]),
        Polygon([(1, -1.2), (-1, 0), (1, 1.4)]),
        Polygon([(-2.4, 3.4), (-1.6, 3), (-2, 2.6)]),
        Polygon([(-1.6, 4.2), (-0.8, 3.8), (-1.2, 3.4)]),
    ]


class TJ_S3210SW5TGLC2R_A5(Component):
    """
    Togia side-firing LED
    Red 1206  Light Emitting Diodes (LED) ROHS
    """

    name = "C273626"
    manufacturer = "TOGIALED"
    mpn = "TJ-S3210SW5TGLC2R-A5"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_1810181735_TOGIALED-TJ-S3210SW5TGLC2R-A5_C273626.pdf"
    reference_designator_prefix = "D"
    landpattern = LandpatternLED_SMD_3P_L3_2_W1_0_RD_RED()

    a = Port()
    """The anode of the LED"""
    c = Port()
    """The cathode of the LED"""
    nc = Port()

    symbol = SymbolTJ_S3210SW5TGLC2R_A5()
    mappings = [
        SymbolMapping({c: symbol.p[1], a: symbol.p[2], nc: symbol.p[3]}),
        PadMapping(
            {
                c: landpattern.p[1],
                a: landpattern.p[2],
                nc: landpattern.p[3],
            }
        ),
    ]


Device: type[TJ_S3210SW5TGLC2R_A5] = TJ_S3210SW5TGLC2R_A5

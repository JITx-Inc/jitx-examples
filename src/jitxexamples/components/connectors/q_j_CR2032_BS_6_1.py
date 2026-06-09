from jitx.anchor import Anchor
from jitx.component import Component
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.landpattern import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolygon, ArcPolyline, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol
from jitx.symbol import SymbolMapping


class RectangleSmdPad(Pad):
    shape = rectangle(4.2, 3.8)
    paste = Paste(rectangle(4.302, 3.902))
    soldermask = Soldermask(rectangle(4.302, 3.902))


class LandpatternBAT_TH_CR2032_BS_6_1(Landpattern):
    p = {
        1: RectangleSmdPad().at((14.385, 0)),
        2: RectangleSmdPad().at((-14.385, 0)),
    }

    value_label = Custom(Text(">VALUE", 0.5, Anchor.W).at((-0.75, 8.8581)), name="Fab")
    customlayer = [
        Custom(ArcPolyline(0.06, [Arc((15.65, 8), 0.03, 0, -360)]), name="Fab"),
        Custom(
            ArcPolygon(
                [(9.652, 8.0765), (11.126, 8.0765), (11.126, 6.6035), (9.652, 8.0765)]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (-10.3, 6.7),
                    (-9.2, 6.7),
                    (-9.2, 6.6),
                    (-10.3, 6.6),
                    (-10.3, 6.7),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [Arc((-9.75, 6.6495), 0.85, 0, 90), Arc((-9.75, 6.6495), 0.95, 90, -90)]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    Arc((-9.75, 6.6495), 0.85, 270.0017, 89.9949),
                    Arc((-9.75, 6.6505), 0.95, 359.9985, -89.9954),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    Arc((-9.75, 6.6495), 0.85, 90.0086, 90),
                    Arc((-9.75, 6.6495), 0.95, 179.9923, -89.9893),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    Arc((-9.75, 6.6495), 0.85, 180.0034, 89.9897),
                    Arc((-9.75, 6.6495), 0.95, 270.0046, -90.0092),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    Arc((9.75, -6.6505), 0.85, 90.0068, 89.9983),
                    Arc((9.75, -6.6505), 0.95, 179.9969, -89.9908),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    Arc((9.75, -6.6505), 0.85, 180.0034, 89.9897),
                    Arc((9.75, -6.6505), 0.95, 270.0046, -90.0046),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    Arc((9.75, -6.6505), 0.85, 359.9983, 90),
                    Arc((9.75, -6.6495), 0.95, 89.9985, -90.0031),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    Arc((9.75, -6.6495), 0.85, 270.0017, 89.9949),
                    Arc((9.75, -6.6505), 0.95, 0, -89.9985),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (9.2, -6.5995),
                    (10.3, -6.5995),
                    (10.3, -6.6995),
                    (9.2, -6.6995),
                    (9.2, -6.5995),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (9.7, -7.2005),
                    (9.7, -6.1005),
                    (9.8, -6.1005),
                    (9.8, -7.2005),
                    (9.7, -7.2005),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (11.05, -8.0005),
                    (-11.05, -8.0005),
                    (-11.35, -8.0005),
                    (-11.35, -8.1505),
                    (11.05, -8.1505),
                    Arc((11.1, -8.0505), 0.1, 270, 90),
                    Arc((11.1, 8.0495), 0.1, 0, 90),
                    (-11.35, 8.1495),
                    (-11.35, 8.0495),
                    (-11.35, 7.9995),
                    Arc((9.7, 6.6495), 1.35, 90, -90),
                    (11.05, -8.0005),
                    (11.05, -8.0005),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (-11.35, 7.9995),
                    (-11.35, -8.0005),
                    (-11.05, -8.0005),
                    (-11.05, 7.9995),
                    (-11.35, 7.9995),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (11.2, 3.5495),
                    Arc((14.25, 3.4995), 0.05, 90, -90),
                    Arc((14.25, 2.0995), 0.05, 0, -90),
                    Arc((14.25, 2.0995), 0.05, 270, -90),
                    (14.2, 3.4495),
                    (11.2, 3.4495),
                    (11.2, 3.5495),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (11.2, -3.5505),
                    Arc((14.25, -3.5005), 0.05, 270, 90),
                    Arc((14.25, -2.0995), 0.05, 359.9709, 90.0291),
                    Arc((14.25, -2.1005), 0.05, 90, 90.0291),
                    (14.2, -3.4505),
                    (11.2, -3.4505),
                    (11.2, -3.5505),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (-11.2, 3.5505),
                    Arc((-14.25, 3.5005), 0.05, 90.0291, 89.9709),
                    Arc((-14.25, 2.0995), 0.05, 179.9709, 90),
                    Arc((-14.25, 2.1005), 0.05, 270, 90.0582),
                    (-14.2, 3.4505),
                    (-11.2, 3.4505),
                    (-11.2, 3.5505),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (-11.2, -3.5495),
                    Arc((-14.25, -3.4995), 0.05, 269.9709, -89.9418),
                    Arc((-14.25, -2.0995), 0.05, 180.0291, -90),
                    Arc((-14.25, -2.0995), 0.05, 90, -90),
                    (-14.2, -3.4495),
                    (-11.2, -3.4495),
                    (-11.2, -3.5495),
                ]
            ),
            name="Fab",
        ),
        Custom(
            ArcPolygon(
                [
                    (-11.85, 8.0995),
                    (-11.6, 8.0995),
                    (-11.6, -8.1005),
                    (-11.85, -8.1005),
                    (-11.85, 8.0495),
                    (-11.85, 8.0995),
                ]
            ),
            name="Fab",
        ),
    ]
    reference_designator = Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 9.8581)))
    silkscreen = [
        Silkscreen(Polyline(0.152, [(11.126, -8.0765), (11.126, -1.9835)])),
        Silkscreen(Polyline(0.152, [(-9.2, 6.6495), (-10.3, 6.6495)])),
        Silkscreen(Polyline(0.152, [(9.2, -6.6505), (10.3, -6.6505)])),
        Silkscreen(Polyline(0.152, [(9.75, -7.2005), (9.75, -6.1005)])),
        Silkscreen(Polyline(0.152, [(11.126, 1.9835), (11.126, -2.0565)])),
        Silkscreen(Polyline(0.152, [(-11.8, 8.0495), (-11.8, -8.0525)])),
        Silkscreen(
            Polyline(
                0.152,
                [
                    (-11.8, 8.0735),
                    (-11.65, 8.0735),
                    (-11.65, -8.0765),
                    (-11.8, -8.0765),
                ],
            )
        ),
        Silkscreen(Polyline(0.152, [(-14.25, -3.5005), (-11.126, -3.5005)])),
        Silkscreen(Polyline(0.152, [(-14.25, -3.5005), (-14.25, -2.0805)])),
        Silkscreen(Polyline(0.152, [(-14.25, 3.4995), (-14.25, 2.0805)])),
        Silkscreen(Polyline(0.152, [(-14.25, 3.4995), (-11.126, 3.4995)])),
        Silkscreen(Polyline(0.152, [(14.25, -3.5005), (11.126, -3.5005)])),
        Silkscreen(Polyline(0.152, [(14.25, -3.5005), (14.25, -2.0805)])),
        Silkscreen(Polyline(0.152, [(14.25, 3.4995), (14.25, 2.0805)])),
        Silkscreen(Polyline(0.152, [(14.25, 3.4995), (11.126, 3.4995)])),
        Silkscreen(
            Polyline(0.152, [(9.64, 8.0765), (9.665, 8.0765), (11.126, 6.6145)])
        ),
        Silkscreen(Polyline(0.152, [(-11.126, 8.0765), (11.126, 8.0765)])),
        Silkscreen(Polyline(0.152, [(11.126, 8.0765), (11.126, 1.9835)])),
        Silkscreen(Polyline(0.152, [(-11.126, -8.0765), (11.126, -8.0765)])),
        Silkscreen(ArcPolyline(0.152, [Arc((0, -0.0005), 10, 126.1317, 107.6751)])),
        Silkscreen(ArcPolyline(0.152, [Arc((0, -0.0005), 10, 306.1316, 107.6751)])),
        Silkscreen(ArcPolyline(0.152, [Arc((9.75, -6.6505), 0.918, 0, -360)])),
        Silkscreen(ArcPolyline(0.152, [Arc((-9.75, 6.6495), 0.918, 0, -360)])),
        Silkscreen(
            ArcPolygon(
                [
                    (-11.05, 8.1525),
                    (-11.05, -1.9505),
                    (-11.35, -2.0005),
                    (-11.355, 1.9325),
                    (-11.355, 8.1525),
                    (-11.05, 8.1525),
                ]
            )
        ),
        Silkscreen(
            ArcPolygon(
                [
                    (-11.05, -8.1525),
                    (-11.05, -1.9325),
                    (-11.355, -1.9325),
                    (-11.355, -8.1525),
                    (-11.05, -8.1525),
                ]
            )
        ),
        Silkscreen(
            ArcPolygon(
                [(9.652, 8.0765), (11.126, 8.0765), (11.126, 6.6035), (9.652, 8.0765)]
            )
        ),
    ]
    courtyard = Courtyard(rectangle(33.072, 16.305))
    model = Model3D(
        "q_j_CR2032_BS_6_1.stp",
        position=(0, 0, 0),
        scale=(1, 1, 1),
        rotation=(0, 0, 0),
    )


class SymbolCR2032_BS_6_1(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    p = {
        1: Pin((-1, 0), 3, Direction.Left),
        2: Pin((1, 0), 3, Direction.Right),
    }
    value = Text(">VALUE", 0.55559, Anchor.C).at((0, 2.58741))
    ref = Text(">REF", 0.55559, Anchor.C).at((0, 3.37481))
    shapes = [
        Polyline(0.254, [(-1, 1.8), (-1, -1.4)]),
        Polyline(0.254, [(-0.4, 1), (-0.4, -0.8)]),
        Polyline(0.254, [(0.2, 1.8), (0.2, -1.4)]),
        Polyline(0.254, [(0.8, 1), (0.8, -0.8)]),
    ]


class CR2032_BS_6_1(Component):
    "Battery base CR2032 SMD  Battery Connectors ROHS"

    name = "C70377"
    manufacturer = "Q&J"
    mpn = "CR2032-BS-6-1"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_1811061923_Q-J-CR2032-BS-6-1_C70377.pdf"
    reference_designator_prefix = "J"

    landpattern = LandpatternBAT_TH_CR2032_BS_6_1()
    pos = Port()
    neg = Port()
    symbol = SymbolCR2032_BS_6_1()
    mappings = [
        SymbolMapping({pos: symbol.p[1], neg: symbol.p[2]}),
        PadMapping(
            {
                pos: landpattern.p[1],
                neg: landpattern.p[2],
            }
        ),
    ]


Device: type[CR2032_BS_6_1] = CR2032_BS_6_1

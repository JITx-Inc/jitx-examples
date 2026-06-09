from functools import partial
from jitx.anchor import Anchor
from jitx.common import Power
from jitx.component import Component
from jitx.container import inline
from jitx.feature import Custom, Paste, Silkscreen, Soldermask, Courtyard
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolygon, ArcPolyline, Circle, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol


class RectanglePad(Pad):
    shape = rectangle(4.15, 4.2)
    soldermask = Soldermask(rectangle(4.25, 4.3))
    paste = Paste(rectangle(4.25, 4.3))


class CirclePad(Pad):
    shape = Circle(radius=3.5)
    soldermask = Soldermask(Circle(radius=3.551))
    paste = Paste(Circle(radius=3.551))


Fab = partial(Custom, name="Fab")


class MY_1632_03(Component):
    """Battery button CR1632 SMD  Battery Connectors ROHS"""

    manufacturer = "MYOUNG"
    mpn = "MY-1632-03"
    datasheet = (
        "https://datasheet.lcsc.com/lcsc/2109301830_MYOUNG-MY-1632-03_C2902337.pdf"
    )
    reference_designator_prefix = "J"

    vout = Power()

    @inline
    class symbol(Symbol):
        pad_name_size = 0.5
        pin_name_size = 0.5

        p = {
            1: Pin((-1, 0), length=3, direction=Direction.Left),
            2: Pin((1, 0), length=3, direction=Direction.Right),
        }

        value = Text(">VALUE", size=1).at(0, 2)
        reference = Text(">REF", size=1).at(0, 3)

        shapes = [
            Polyline(0.2, [(-1, 1.8), (-1, -1.4)]),
            Polyline(0.2, [(-0.4, 1), (-0.4, -0.8)]),
            Polyline(0.2, [(0.2, 1.8), (0.2, -1.4)]),
            Polyline(0.2, [(0.8, 1), (0.8, -0.8)]),
        ]

    @inline
    class landpattern(Landpattern):
        p = {
            1: RectanglePad().at(10, -2.413),
            2: CirclePad().at(0, -2.413),
            3: RectanglePad().at(-10, -2.413),
        }

        labels = [
            Silkscreen(Text(">REF", size=0.5, anchor=Anchor.W).at(-0.75, 7.675)),
            Fab(Text(">VALUE", size=0.5, anchor=Anchor.W).at(-0.75, 6.675)),
        ]

        silkscreen = [
            Silkscreen(shape)
            for shape in [
                Polyline(0.254, [(-3.175, 5.842), (-8.001, 1.016), (-8.001, -0.081)]),
                Polyline(0.254, [(3.175, 5.842), (8.001, 1.016), (8.001, -0.081)]),
                Polyline(0.254, [(-3.175, 5.842), (3.175, 5.842)]),
                Polyline(0.254, [(8.001, -4.744), (8.001, -5.842)]),
                Polyline(0.254, [(-8.001, -4.744), (-8.001, -5.842)]),
                ArcPolygon(
                    [
                        (-1.524, 3.429),
                        (1.524, 3.429),
                        (1.524, 3.175),
                        (-1.524, 3.175),
                        (-1.524, 3.429),
                    ]
                ),
                ArcPolygon(
                    [
                        (-0.127, 1.778),
                        (-0.127, 4.826),
                        (0.127, 4.826),
                        (0.127, 1.778),
                        (-0.127, 1.778),
                    ]
                ),
            ]
        ]
        fab_drawing = [
            Fab(Polyline(0.254, [(3.302, -4.953), (3.302, -0.635)])),
            Fab(Polyline(0.254, [(3.302, -4.953), (5.588, -4.953), (5.588, -0.635)])),
            Fab(
                Polyline(0.254, [(-5.588, -4.953), (-3.302, -4.953), (-3.302, -0.635)])
            ),
            Fab(Polyline(0.254, [(-5.588, -4.953), (-5.588, -0.635)])),
            Fab(ArcPolyline(0.254, [(Arc((4.445, -0.635), 1.143, 0, 180))])),
            Fab(ArcPolyline(0.254, [(Arc((-4.445, -0.635), 1.143, 0, 180))])),
            Fab(ArcPolyline(0.254, [(Arc((-4.362, -5.185), 3.698, 190.234, 94.385))])),
            Fab(ArcPolyline(0.254, [(Arc((4.362, -5.185), 3.698, 349.766, -94.385))])),
            Fab(ArcPolyline(0.254, [(Arc((0, -12.182), 4.843, 44.922, 90.156))])),
            Fab(ArcPolyline(0.06, [(Arc((-11.651, -8.798), 0.03, 0, -360))])),
            Fab(ArcPolyline(0.254, [(Arc((4.445, -0.508), 1.984, 0, -360))])),
            Fab(ArcPolyline(0.254, [(Arc((-4.445, -0.508), 1.984, 0, -360))])),
            Fab(
                ArcPolygon(
                    [
                        (-1.524, 3.429),
                        (1.524, 3.429),
                        (1.524, 3.175),
                        (-1.524, 3.175),
                        (-1.524, 3.429),
                    ]
                )
            ),
            Fab(
                ArcPolygon(
                    [
                        (-0.127, 1.778),
                        (-0.127, 4.826),
                        (0.127, 4.826),
                        (0.127, 1.778),
                        (-0.127, 1.778),
                    ]
                )
            ),
            Fab(
                ArcPolygon(
                    [
                        Arc((-3.175, 5.842), 0.127, 90, -180),
                        Arc((3.175, 5.842), 0.127, 270, -180),
                    ]
                )
            ),
            Fab(
                ArcPolygon(
                    [
                        (-7.874, 0.964),
                        Arc((-8.001, -0.081), 0.127, 0, -180),
                        Arc((-8.001, 1.017), 0.127, 180.011, -45.003),
                        Arc((-3.175, 5.842), 0.127, 135, -180),
                    ]
                )
            ),
            Fab(
                ArcPolygon(
                    [
                        Arc((8.001, 1.017), 0.127, 44.992, -45.003),
                        Arc((8.001, -0.081), 0.127, 0, -180),
                        (7.874, 0.964),
                        Arc((3.175, 5.842), 0.127, 225, -180),
                    ]
                )
            ),
        ]
        courtyard = Courtyard(rectangle(24.25, 11.938))

    mapping = PadMapping(
        {
            vout.Vp: [landpattern.p[1], landpattern.p[3]],
            vout.Vn: landpattern.p[2],
        }
    )


Device: type[MY_1632_03] = MY_1632_03

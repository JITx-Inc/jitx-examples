from jitx.anchor import Anchor
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.container import inline
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolygon, ArcPolyline, Circle, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol
from jitxlib.parts import Capacitor


class CirclePad(Pad):
    shape = Circle(radius=0.35)
    soldermask = Soldermask(Circle(radius=0.401))
    paste = Paste(Circle(radius=0.401))


class AP3722AT(Circuit):
    @inline
    class mic(Component):
        manufacturer = "ALLPOWER(ShenZhen Quan Li Semiconductor)"
        mpn = "AP3722AT"
        datasheet = "https://datasheet.lcsc.com/lcsc/2011200934_ALLPOWER-ShenZhen-Quan-Li-Semiconductor-AP3722AT_C918198.pdf"
        reference_designator_prefix = "U"

        VDD = Port()
        GND = [Port() for _ in range(2)]
        OUT = Port()

        @inline
        class landpattern(Landpattern):
            p = {
                1: CirclePad().at(0.575, 1.346),
                2: CirclePad().at(0.575, -1.313),
                3: CirclePad().at(-0.575, -1.313),
                4: CirclePad().at(-0.575, 1.346),
            }

            silkscreens = [
                Silkscreen(Text(">REF", 0.5, Anchor.W).at(-0.75, 3.849)),
                Silkscreen(Polyline(0.254, [(-1.2, 2.016), (1.2, 2.016)])),
                Silkscreen(Polyline(0.254, [(-1.2, -2.016), (1.2, -2.016)])),
                Silkscreen(Polyline(0.254, [(1.2, 2.016), (1.2, -1.984)])),
                Silkscreen(Polyline(0.254, [(-1.2, 2.016), (-1.2, -2.016)])),
                Silkscreen(ArcPolyline(0.2, [Arc((1.6, 1.516), 0.1, 0, -360)])),
            ]

            custom_fabs = [
                Custom(Text(">VALUE", 0.5, Anchor.W).at(-0.75, 2.849), name="Fab"),
                Custom(
                    ArcPolyline(0.06, [Arc((1.12, 1.896), 0.03, 0, -360)]),
                    name="Fab",
                ),
                Custom(
                    ArcPolyline(0.35, [Arc((0, 0.716), 0.175, 0, -360)]),
                    name="Fab",
                ),
                Custom(
                    ArcPolygon(
                        [
                            (1.12, 1.896),
                            (0.92, 1.896),
                            (0.92, 1.896),
                            (1.12, 1.696),
                            (1.12, 1.896),
                        ]
                    ),
                    name="Fab",
                ),
            ]
            courtyard = Courtyard(rectangle(2.654, 4.286))

        @inline
        class symbol(Symbol):
            pin_name_size = 0.7
            pad_name_size = 0.7
            VDD = Pin((-5, 1), 2, direction=Direction.Left)
            GND = [
                Pin((-5, -1), 2, Direction.Left),
                Pin((5, -1), 2, Direction.Right),
            ]
            OUT = Pin((5, 1), 2, Direction.Right)

            value = Text(">VALUE", 0.5, Anchor.C).at(0, 3.5)
            reference = Text(">REF", 0.5, Anchor.C).at(0, 4.2)
            art = [
                rectangle(10, 6),
                Circle(radius=0.3).at(-4, 2),
            ]

    vin = Power()
    out = Port()

    def __init__(self):
        self.nets = [
            self.vin.Vp + self.mic.VDD,
            self.vin.Vn + self.mic.GND[0],
            self.mic.GND[0] + self.mic.GND[1],
            self.out + self.mic.OUT,
        ]

        self.byp = Capacitor(capacitance=0.1e-6).insert(
            self.mic.VDD, self.mic.GND[0], short_trace=True
        )


Device: type[AP3722AT] = AP3722AT

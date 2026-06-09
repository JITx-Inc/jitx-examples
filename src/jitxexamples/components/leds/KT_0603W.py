# This file is generated based on the parts database query below:
#     from jitx.circuit import Circuit
#     from jitxlib.parts import Part
#     class Example(Circuit):
#         def __init__(self):
#            self.part = Part(mpn="KT-0603W", manufacturer="Hubei_KENTO_Elec")
#
# File Location: components/Hubei_KENTO_Elec/KT_0603W.py
# To use this component:
#     from .components.Hubei_KENTO_Elec import KT_0603W
#     class Example(Circuit):
#         u1 = KT_0603W.Device()
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polygon, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.transform import Transform


class RectangleSmdPad(Pad):
    shape = rectangle(0.8, 0.8)
    solder_mask = [Soldermask(rectangle(0.902, 0.902))]
    paste = [Paste(rectangle(0.902, 0.902))]


class LandpatternLED0603_R_RD_WHITE(Landpattern):
    name = "LED0603-R-RD_WHITE"
    p = {
        1: RectangleSmdPad().at(Transform((0.8765, -0.0005), 90)),
        2: RectangleSmdPad().at(Transform((-0.8255, -0.0005), 90)),
    }
    pcb_layer_reference = Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 2.6961)))
    pcb_layer_value = Custom(
        Text(">VALUE", 0.5, Anchor.W).at((-0.75, 1.6961)), name="Fab"
    )
    silkscreen = [
        Silkscreen(Polyline(0.254, [(1.7905, -0.8635), (1.7905, 0.8635)])),
        Silkscreen(Polyline(0.254, [(1.7905, 0.8635), (0.3175, 0.8635)])),
        Silkscreen(Polyline(0.254, [(1.7905, -0.8635), (0.3175, -0.8635)])),
        Silkscreen(Polyline(0.254, [(-0.2665, 0.8635), (-1.4345, 0.8635)])),
        Silkscreen(Polyline(0.254, [(-0.2915, -0.8635), (-1.4345, -0.8635)])),
        Silkscreen(
            Polyline(
                0.254,
                [
                    (-1.4345, -0.8635),
                    (-1.7905, -0.5085),
                    (-1.7905, 0.5075),
                    (-1.4345, 0.8635),
                ],
            )
        ),
        Silkscreen(Polyline(0.203, [(0.1015, -0.4065), (0.1015, 0.3805)])),
        Silkscreen(Polyline(0.203, [(0.1015, -0.0075), (-0.0735, -0.0075)])),
    ]
    custom_layer = [
        Custom(ArcPolyline(0.06, [Arc((0.8255, 0.4005), 0.03, 0, -360)]), name="Fab"),
        Custom(
            Polygon(
                [
                    (-1.1675, 0.0495),
                    (-0.5075, 0.0495),
                    (-0.5075, -0.1025),
                    (-1.1675, -0.1025),
                    (-1.1675, 0.0495),
                ]
            ),
            name="Fab",
        ),
        Custom(
            Polygon(
                [
                    (0.9615, -0.2755),
                    (0.9615, 0.3855),
                    (1.1135, 0.3855),
                    (1.1135, -0.2755),
                    (0.9615, -0.2755),
                ]
            ),
            name="Fab",
        ),
        Custom(
            Polygon(
                [
                    (0.6865, 0.1015),
                    (1.3465, 0.1015),
                    (1.3465, -0.0505),
                    (0.6865, -0.0505),
                    (0.6865, 0.1015),
                ]
            ),
            name="Fab",
        ),
    ]
    courtyard = [Courtyard(rectangle(3.835, 1.981))]
    model3ds = [
        Model3D(
            "KT_0603W.stp",
            position=(0.0, 0.0, 0.0),
            scale=(1.0, 1.0, 1.0),
            rotation=(0.0, 0.0, 0.0),
        )
    ]


class Symbol0603White_light_C2290(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    K = Pin((1, -1), 3, Direction.Right)
    A = Pin((-1, -1), 3, Direction.Left)
    layer_reference = Text(">REF", 0.55559, Anchor.C).at((0, 3.97481))
    layer_value = Text(">VALUE", 0.55559, Anchor.C).at((0, 3.18741))
    draws = [
        Polyline(0.254, [(1.6, 0.2), (3.00001, 1.6)]),
        Polyline(0.254, [(0.8, 1), (2.2, 2.4)]),
        Polyline(0.254, [(1, 0.6), (1, -2.60001)]),
        Polygon([(3.00001, 1.6), (2.2, 1.2), (2.60001, 0.8)]),
        Polygon([(2.2, 2.4), (1.4, 2), (1.8, 1.6)]),
        Polygon([(-1, -2.2), (1, -1), (-1, 0.4)]),
    ]


class KT_0603W(Component):
    manufacturer = "Hubei KENTO Elec"
    mpn = "KT-0603W"
    reference_designator_prefix = "D"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_2305091500_Hubei-KENTO-Elec-KT-0603W_C2290.pdf"
    K = Port()
    A = Port()
    landpattern = LandpatternLED0603_R_RD_WHITE()
    symbol = Symbol0603White_light_C2290()
    cmappings = [
        SymbolMapping({K: symbol.K, A: symbol.A}),
        PadMapping({K: landpattern.p[2], A: landpattern.p[1]}),
    ]


Device: type[KT_0603W] = KT_0603W

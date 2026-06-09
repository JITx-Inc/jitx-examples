# This file is generated based on the parts database query below:
#     from jitx.circuit import Circuit
#     from jitxlib.parts import Part
#     class Example(Circuit):
#         def __init__(self):
#            self.part = Part(mpn="KT-0603Y", manufacturer="Hubei_KENTO_Elec")
#
# File Location: components/Hubei_KENTO_Elec/KT_0603Y.py
# To use this component:
#     from .components.Hubei_KENTO_Elec import KT_0603Y
#     class Example(Circuit):
#         u1 = KT_0603Y.Component()
from jitx.anchor import Anchor
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polygon, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.transform import Transform
from jitx.component import Component as JITXComponent


class RectangleSmdPad(Pad):
    shape = rectangle(0.8, 0.8)
    solder_mask = [Soldermask(rectangle(0.902, 0.902))]
    paste = [Paste(rectangle(0.902, 0.902))]


class LandpatternLED0603_R_RD(Landpattern):
    name = "LED0603-R-RD"
    p = {
        1: RectangleSmdPad().at(Transform((0.851, 0), 90)),
        2: RectangleSmdPad().at(Transform((-0.851, 0), 90)),
    }
    pcb_layer_reference = Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 2.5316)))
    pcb_layer_value = Custom(
        Text(">VALUE", 0.5, Anchor.W).at((-0.75, 1.5316)), name="Fab"
    )
    silkscreen = [
        Silkscreen(Polyline(0.15, [(0.29, 0.751), (1.44, 0.751)])),
        Silkscreen(Polyline(0.15, [(1.44, 0.751), (1.44, -0.729)])),
        Silkscreen(Polyline(0.15, [(0.29, -0.749), (1.44, -0.749)])),
        Silkscreen(Polyline(0.15, [(-0.09, -0.751), (-1.14, -0.751)])),
        Silkscreen(Polyline(0.15, [(-1.44, -0.351), (-1.44, -0.451), (-1.14, -0.751)])),
        Silkscreen(Polyline(0.15, [(-1.44, 0.349), (-1.44, -0.351)])),
        Silkscreen(Polyline(0.15, [(-1.44, 0.349), (-1.44, 0.449), (-1.14, 0.749)])),
        Silkscreen(Polyline(0.15, [(-0.09, 0.749), (-1.14, 0.749)])),
        Silkscreen(Polyline(0.203, [(0.076, -0.406), (0.076, 0.381)])),
        Silkscreen(Polyline(0.203, [(0.076, -0.008), (-0.099, -0.008)])),
    ]
    custom_layer = [
        Custom(ArcPolyline(0.06, [Arc((0.8, -0.4), 0.03, 0, -360)]), name="Fab"),
        Custom(
            Polygon(
                [
                    (0.661, 0.102),
                    (1.321, 0.102),
                    (1.321, -0.051),
                    (0.661, -0.051),
                    (0.661, 0.102),
                ]
            ),
            name="Fab",
        ),
        Custom(
            Polygon(
                [
                    (0.936, -0.275),
                    (0.936, 0.385),
                    (1.088, 0.385),
                    (1.088, -0.275),
                    (0.936, -0.275),
                ]
            ),
            name="Fab",
        ),
        Custom(
            Polygon(
                [
                    (-1.193, 0.05),
                    (-0.533, 0.05),
                    (-0.533, -0.103),
                    (-1.193, -0.103),
                    (-1.193, 0.05),
                ]
            ),
            name="Fab",
        ),
    ]
    courtyard = [Courtyard(rectangle(3.03, 1.652))]
    model3ds = [
        Model3D(
            "KT_0603G.stp",
            position=(0.0, 0.0, 0.0),
            scale=(1.0, 1.0, 1.0),
            rotation=(0.0, 0.0, 0.0),
        )
    ]


class Symbol0603YYellow_light_90_110(Symbol):
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


class KT_0603Y(JITXComponent):
    manufacturer = "Hubei KENTO Elec"
    mpn = "KT-0603Y"
    reference_designator_prefix = "D"
    datasheet = ""
    K = Port()
    A = Port()
    landpattern = LandpatternLED0603_R_RD()
    symbol = Symbol0603YYellow_light_90_110()
    cmappings = [
        SymbolMapping({K: symbol.K, A: symbol.A}),
        PadMapping({K: landpattern.p[2], A: landpattern.p[1]}),
    ]


Device: type[KT_0603Y] = KT_0603Y

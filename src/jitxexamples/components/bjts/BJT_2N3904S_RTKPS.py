from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component as JITXComponent
from jitx.circuit import Circuit
from jitx.landpattern import Landpattern, Pad
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polygon, Polyline, Text
from jitx.feature import Paste, Silkscreen, Soldermask, Custom, Courtyard
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.transform import Transform


class RectangleSmdPad(Pad):
    shape = rectangle(0.7, 1.25)
    solder_mask = [Soldermask(rectangle(0.802, 1.352))]
    paste = [Paste(rectangle(0.802, 1.352))]


class LandpatternSOT_23_3_L2_9_W1_3_P1_90_LS2_4_TR(Landpattern):
    name = "SOT-23-3_L2.9-W1.3-P1.90-LS2.4-TR"
    p = {
        1: RectangleSmdPad().at(Transform((1.2495, 0.95), 270)),
        2: RectangleSmdPad().at(Transform((1.2495, -0.95), 270)),
        3: RectangleSmdPad().at(Transform((-1.2495, 0), 270)),
    }
    pcb_layer_reference = Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 3.3316)))
    pcb_layer_value = Custom(
        Text(">VALUE", 0.5, Anchor.W).at((-0.75, 2.3316)), name="Fab"
    )
    silkscreen = [
        Silkscreen(
            Polyline(0.254, [(0.1645, -1.46), (-0.6505, -1.46), (-0.6505, -0.8)])
        ),
        Silkscreen(
            Polyline(
                0.254,
                [
                    (-0.6505, 0.8),
                    (-0.6505, 1.46),
                    (-0.6505, 0.8),
                    (-0.6505, 1.46),
                    (0.1645, 1.46),
                ],
            )
        ),
        Silkscreen(Polyline(0.2, [(0.8995, -0.3), (0.8995, 0.3)])),
    ]
    custom_layer = [
        Custom(ArcPolyline(0.06, [Arc((1.1995, 1.45), 0.03, 0, -360)]), name="Fab"),
        Custom(ArcPolyline(0.254, [Arc((1.4955, 0.945), 0.127, 0, -360)]), name="Fab"),
    ]
    courtyard = [Courtyard(rectangle(3.301, 3.252))]
    # model3ds = [
    #     Model3D(
    #         "BJT_2N3904S_RTKPS.stp",
    #         position=(0.0, 0.0, 0.0),
    #         scale=(1.0, 1.0, 1.0),
    #         rotation=(0.0, 0.0, 0.0),
    #     )
    # ]


class Symbol2n3904S_RTK_PS_C18536(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    B = Pin((0, 0), 2, Direction.Left)
    C = Pin((2, 2), 2, Direction.Up)
    E = Pin((2, -2), 2, Direction.Down)
    layer_reference = Text(">REF", 0.55559, Anchor.C).at((0, 3.57481))
    layer_value = Text(">VALUE", 0.55559, Anchor.C).at((0, 2.78741))
    draws = [
        Polyline(0.254, [(2, 2), (0, 0.6)]),
        Polyline(0.254, [(0, -0.6), (2, -2)]),
        Polyline(0.254, [(0, 1.8), (0, -1.8)]),
        Polygon([(2, -2), (1.4, -1), (0.8, -1.8)]),
    ]


class Component(JITXComponent):
    """Epitaxial Planar NPN Transistor"""

    manufacturer = "KEC Semicon"
    mpn = "2N3904S-RTK/PS"
    reference_designator_prefix = "Q"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_KEC-Semicon-2N3904S-RTK-PS_C18536.pdf"
    B = Port()
    C = Port()
    E = Port()
    landpattern = LandpatternSOT_23_3_L2_9_W1_3_P1_90_LS2_4_TR()
    symbol = Symbol2n3904S_RTK_PS_C18536()
    cmappings = [
        SymbolMapping({B: symbol.B, C: symbol.C, E: symbol.E}),
        PadMapping({B: landpattern.p[2], C: landpattern.p[3], E: landpattern.p[1]}),
    ]


class BJT_2N3904S_RTKPS(Circuit):
    """
    BJT-2N3904S-RTKPS NPN Transistor Module
    """

    b = Port()  # Base
    c = Port()  # Collector
    e = Port()  # Emitter

    # Create the transistor instance using database part
    bjt = Component()

    # Net connections
    nets = [
        bjt.B + b,
        bjt.C + c,
        bjt.E + e,
    ]


Device: type[BJT_2N3904S_RTKPS] = BJT_2N3904S_RTKPS

from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component as JITXComponent
from jitx.circuit import Circuit
from jitx.landpattern import Landpattern, Pad
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polyline, Text, Circle
from jitx.feature import Custom, Paste, Silkscreen, Soldermask, Courtyard
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping


class RectangleSmdPad(Pad):
    shape = rectangle(1, 0.7)
    solder_mask = [Soldermask(rectangle(1.102, 0.802))]
    paste = [Paste(rectangle(1.102, 0.802))]


class LandpatternTSOP_6_L3_0_W1_5_P0_95_LS2_8_BR(Landpattern):
    name = "TSOP-6_L3.0-W1.5-P0.95-LS2.8-BR"
    p = {
        1: RectangleSmdPad().at((1.2, -0.95)),
        2: RectangleSmdPad().at((1.2, 0)),
        3: RectangleSmdPad().at((1.2, 0.95)),
        4: RectangleSmdPad().at((-1.2, 0.95)),
        5: RectangleSmdPad().at((-1.2, 0)),
        6: RectangleSmdPad().at((-1.2, -0.95)),
    }
    pcb_layer_reference = Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 3.4326)))
    pcb_layer_value = Custom(
        Text(">VALUE", 0.5, Anchor.W).at((-0.75, 2.4326)), name="Fab"
    )
    silkscreen = [
        Silkscreen(Polyline(0.254, [(-0.9, 1.6), (0.9, 1.6)])),
        Silkscreen(Polyline(0.254, [(-0.9, -1.6), (0.9, -1.6)])),
        Silkscreen(ArcPolyline(0.254, [Arc((1.35, -1.68), 0.127, 0, -360)])),
    ]
    custom_layer = [
        Custom(ArcPolyline(0.06, [Arc((1.375, -1.5), 0.03, 0, -360)]), name="Fab"),
        Custom(ArcPolyline(0.254, [Arc((1.577, -0.943), 0.127, 0, -360)]), name="Fab"),
    ]
    courtyard = [Courtyard(rectangle(3.502, 3.454))]
    model3ds = [
        Model3D(
            "AO6409.stp",
            position=(0.0, 0.0, 0.0),
            scale=(1.0, 1.0, 1.0),
            rotation=(0.0, 0.0, 0.0),
        )
    ]


class SymbolAO6409(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    D0 = Pin((-4, 2), 2, Direction.Left)
    D1 = Pin((-4, 0), 2, Direction.Left)
    G = Pin((-4, -2), 2, Direction.Left)
    S = Pin((4, -2), 2, Direction.Right)
    D2 = Pin((4, 0), 2, Direction.Right)
    D3 = Pin((4, 2), 2, Direction.Right)
    layer_reference = Text(">REF", 0.55559, Anchor.C).at((0, 4.87481))
    layer_value = Text(">VALUE", 0.55559, Anchor.C).at((0, 4.08741))
    draws = [rectangle(8.00002, 8.00002), Circle(radius=0.3).at((-3.00001, 3.00001))]


class Component(JITXComponent):
    """p-channel mosfet"""

    manufacturer = "Alpha & Omega Semicon"
    mpn = "AO6409"
    reference_designator_prefix = "Q"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_1809192121_Alpha---Omega-Semicon-AO6409_C115833.pdf"
    D0 = Port()
    D1 = Port()
    G = Port()
    S = Port()
    D2 = Port()
    D3 = Port()
    landpattern = LandpatternTSOP_6_L3_0_W1_5_P0_95_LS2_8_BR()
    symbol = SymbolAO6409()
    cmappings = [
        SymbolMapping(
            {
                D0: symbol.D0,
                D1: symbol.D1,
                G: symbol.G,
                S: symbol.S,
                D2: symbol.D2,
                D3: symbol.D3,
            }
        ),
        PadMapping(
            {
                D0: landpattern.p[1],
                D1: landpattern.p[2],
                G: landpattern.p[3],
                S: landpattern.p[4],
                D2: landpattern.p[5],
                D3: landpattern.p[6],
            }
        ),
    ]


class AO6409(Circuit):
    """
    MOS-A06409 Module
    P-channel MOSFET module with safety checks and electrical properties
    """

    d = Port()  # Drain
    g = Port()  # Gate
    s = Port()  # Source

    # AO6409 P-channel MOSFET from Alpha & Omega Semicon
    mosfet = Component()
    # Circuit connections
    nets = [
        # MOSFET drain connections (multiple drain pins connected together)
        mosfet.D0 + d,
        mosfet.D1 + d,
        mosfet.D2 + d,
        mosfet.D3 + d,
        # MOSFET gate connection
        mosfet.G + g,
        # MOSFET source connection
        mosfet.S + s,
    ]


Device: type[AO6409] = AO6409

from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.landpattern import Landpattern, Pad
from jitx.layerindex import Side
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polygon, Polyline, Text
from jitx.feature import Finish, Paste, Silkscreen, Soldermask
from jitx.symbol import Direction, Pin, Symbol
from jitxlib.symbols.box import BoxSymbol, Row, PinGroup


class RectSMDPad(Pad):
    rect = rectangle(0.250013, 0.68001)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class C294620(Landpattern):
    p = {
        1: RectSMDPad().at(-1.0, -0.434989, on=Side.Top),
        2: RectSMDPad().at(-0.499873, -0.434989, on=Side.Top),
        3: RectSMDPad().at(0.0, -0.434989, on=Side.Top),
        4: RectSMDPad().at(0.500127, -0.434989, on=Side.Top),
        5: RectSMDPad().at(1.0, -0.434989, on=Side.Top),
        6: RectSMDPad().at(1.0, 0.434963, on=Side.Top),
        7: RectSMDPad().at(0.500127, 0.434963, on=Side.Top),
        8: RectSMDPad().at(0.0, 0.434963, on=Side.Top),
        9: RectSMDPad().at(-0.499873, 0.434963, on=Side.Top),
        10: RectSMDPad().at(-1.0, 0.434963, on=Side.Top),
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 3.016015))
    value_text = Finish(Text(">VALUE", 1.0, Anchor.C).at(0.0, -3.016015))
    ref_alt_text = Finish(Text("REF**", 1.0, Anchor.C).at(0.0, -5.016015))

    silk_lines = [
        Silkscreen(Polyline(0.254001, [(-1.35997, 1.016015), (-1.359995, -1.015989)])),
        Silkscreen(Polyline(0.254001, [(-1.359995, -1.015989), (1.359995, -1.015989)])),
        Silkscreen(Polyline(0.254001, [(1.359995, 1.016015), (1.359995, -1.016015)])),
        Silkscreen(Polyline(0.254001, [(-1.35997, 1.016015), (1.359995, 1.016015)])),
    ]

    silk_arcs = [
        Silkscreen(
            ArcPolyline(0.059995, [Arc((-1.250013, -0.500368), 0.029998, 0.0, 360.0)])
        ),
        Silkscreen(
            ArcPolyline(
                0.254001, [Arc((-1.016002, -1.397142), 0.0635000000000001, 0.0, 360.0)]
            )
        ),
    ]

    finish_arc = Finish(
        ArcPolyline(0.2, [Arc((-1.016002, -0.508014), 0.1, 0.0, 360.0)])
    )

    # model = Model3D(
    #    "../../3d-models/C294620.wrl",
    #    position=(0, 0, 0),
    #    scale=(1, 1, 1),
    #    rotation=(0, 0, -270)
    # )


class PUSB3FR4_Symbol(Symbol):
    pin_name_size = 0.6
    pad_name_size = 0.6

    CH1 = Pin(at=(-3, -3), direction=Direction.Left, length=1)
    nc0 = Pin(at=(3, -3), direction=Direction.Right, length=1)
    CH2 = Pin(at=(-3, -4), direction=Direction.Left, length=1)
    GND0 = Pin(at=(-3, -5), direction=Direction.Left, length=1)
    CH3 = Pin(at=(-3, -6), direction=Direction.Left, length=1)
    CH4 = Pin(at=(-3, -7), direction=Direction.Left, length=1)
    nc3 = Pin(at=(3, -7), direction=Direction.Right, length=1)
    nc2 = Pin(at=(3, -6), direction=Direction.Right, length=1)
    GND1 = Pin(at=(3, -5), direction=Direction.Right, length=1)
    nc1 = Pin(at=(3, -4), direction=Direction.Right, length=1)

    ref_text = Text(">REF", 1.27, Anchor.C).at(0.0, 1.27)
    value_text = Text(">VALUE", 1.27, Anchor.C).at(0.0, -2.54)

    component_box = Polygon(
        [(3.0, -2.0), (-3.0, -2.0), (-3.0, -8.0), (3.0, -8.0), (3.0, -2.0)]
    )
    pin1_indicator = Polygon(
        [(-2.5, -2.5), (-2.35, -2.5), (-2.35, -2.35), (-2.5, -2.35), (-2.5, -2.5)]
    )


class PUSB3FR4(Component):
    """System-level ESD protection for USB"""

    mpn = "PUSB3FR4"
    reference_designator_prefix = "U"

    CH1 = Port()
    CH2 = Port()
    GND = Port()
    CH3 = Port()
    CH4 = Port()

    landpattern = C294620()
    symbol = BoxSymbol(rows=[Row(left=[PinGroup([CH1, CH2, GND, CH3, CH4])])])
    # Pin mappings based on the pin-properties from the original Stanza file

    mappings = [
        PadMapping(
            {
                CH1: [landpattern.p[1], landpattern.p[10]],
                CH2: [landpattern.p[2], landpattern.p[9]],
                GND: [landpattern.p[3], landpattern.p[8]],
                CH3: [landpattern.p[4], landpattern.p[7]],
                CH4: [landpattern.p[5], landpattern.p[6]],
            }
        ),
    ]

    # Property for datasheet URL
    datasheet = (
        "https://datasheet.lcsc.com/lcsc/1810081417_Nexperia-PUSB3FR4_C294620.pdf"
    )


Device: type[PUSB3FR4] = PUSB3FR4

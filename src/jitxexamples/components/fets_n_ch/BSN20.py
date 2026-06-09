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


class RectSMDPad(Pad):
    rect = rectangle(1.070003, 0.6)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class C116157(Landpattern):
    p = {
        1: RectSMDPad().at(1.235077, -0.949962, on=Side.Top),
        2: RectSMDPad().at(1.235077, 0.949962, on=Side.Top),
        3: RectSMDPad().at(-1.235077, 0.0, on=Side.Top),
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 3.536195))
    value_text = Finish(Text(">VALUE", 1.0, Anchor.C).at(0.0, -3.536195))
    ref_alt_text = Finish(Text("REF**", 1.0, Anchor.C).at(0.0, -5.536195))

    silk_lines = [
        Silkscreen(Polyline(0.1524, [(0.876073, 1.536195), (-0.876327, 1.536195)])),
        Silkscreen(Polyline(0.1524, [(-0.876327, -1.536195), (-0.876327, -0.49459)])),
        Silkscreen(Polyline(0.1524, [(0.876073, 0.455398), (0.876073, -0.455398)])),
        Silkscreen(Polyline(0.1524, [(0.876073, -1.536195), (-0.876327, -1.536195)])),
        Silkscreen(Polyline(0.1524, [(-0.876327, 1.536195), (-0.876327, 0.49459)])),
    ]

    silk_arcs = [
        Silkscreen(
            ArcPolyline(
                0.059995, [Arc((1.399873, -1.459995), 0.0299970000000001, 0.0, 360.0)]
            )
        ),
    ]

    finish_arc = Finish(
        ArcPolyline(0.2, [Arc((1.65113, -0.949962), 0.100077, 0.0, 360.0)])
    )

    # model = Model3D(
    #     "../../3d-models/C116157.wrl",
    #     position=(0, 0, 0),
    #     scale=(1, 1, 1),
    #     rotation=(0, 0, -180)
    # )


class BSN20_Symbol(Symbol):
    pin_name_size = 0.6
    pad_name_size = 0.6

    G = Pin(at=(-2, -5), direction=Direction.Left, length=1)  # Gate
    S = Pin(at=(0, -6), direction=Direction.Down, length=1)  # Source
    D = Pin(at=(0, -4), direction=Direction.Up, length=1)  # Drain

    ref_text = Text(">REF", 1.27, Anchor.C).at(0.0, 1.27)
    value_text = Text(">VALUE", 1.27, Anchor.C).at(0.0, -2.54)

    # MOSFET symbol elements
    # Gate line
    gate_line = Polyline(0.0, [(-2, -5), (-1, -5)])

    # Source line
    source_line = Polyline(0.0, [(0, -5), (-1, -5)])

    # Drain line
    drain_line = Polyline(0.0, [(0, -4), (-1, -4)])

    # Channel lines
    channel_lines = [
        Polyline(0.0, [(-1, -5), (0, -5), (0, -6), (1, -6), (1, -5)]),
        Polyline(0.0, [(-1, -4), (0, -4), (0, -4), (1, -4), (1, -4)]),
    ]

    # Arrow elements
    arrows = [
        Polyline(0.0, [(0.6, -4), (0.7, -4), (1.3, -4), (1.4, -4)]),
    ]

    # Connection lines
    connection_lines = [
        Polyline(0.0, [(-1, -5), (-1, -5)]),
        Polyline(0.0, [(-1, -5), (-1, -5)]),
        Polyline(0.0, [(-1, -4), (-1, -4)]),
        Polyline(0.0, [(-1, -5), (-1, -5)]),
        Polyline(0.0, [(-1, -5), (-1, -5)]),
        Polyline(0.0, [(-1, -4), (-1, -4)]),
    ]

    # MOSFET symbol polygons
    gate_polygon = Polygon([(-1, -5), (-0.4, -4), (-0.4, -5), (-1, -5)])
    drain_polygon = Polygon([(1, -4), (1.3, -5), (0.7, -5), (1, -4)])


class BSN20(Component):
    """N-channel enhancement mode field-effect transistor"""

    mpn = "BSN20"
    reference_designator_prefix = "Q"

    G = Port()  # Gate
    S = Port()  # Source
    D = Port()  # Drain

    landpattern = C116157()
    symbol = BSN20_Symbol()

    # Pin mappings based on the pin-properties from the original Stanza file
    mappings = [
        PadMapping(
            {
                G: [landpattern.p[1]],  # Gate to pin 1
                S: [landpattern.p[2]],  # Source to pin 2
                D: [landpattern.p[3]],  # Drain to pin 3
            }
        ),
    ]

    # Property for datasheet URL
    datasheet = "https://datasheet.lcsc.com/lcsc/1811021114_Shikues-BSN20_C116157.pdf"


Device: type[BSN20] = BSN20

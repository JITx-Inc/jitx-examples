from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.landpattern import Landpattern, Pad
from jitx.layerindex import Side
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polyline, Text
from jitx.feature import Finish, Paste, Silkscreen, Soldermask, Cutout
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup


class RectSMDPad1(Pad):
    rect = rectangle(0.9, 1.8)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class RectSMDPad2(Pad):
    rect = rectangle(1.1, 0.929997)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class C778186(Landpattern):
    p = {
        1: RectSMDPad1().at(-2.250064, 2.440932, on=Side.Top),
        2: RectSMDPad1().at(0.749936, 2.440932, on=Side.Top),
        3: RectSMDPad1().at(2.249809, 2.440932, on=Side.Top),
        4: RectSMDPad2().at(3.799975, 1.544056, on=Side.Top),
        5: RectSMDPad2().at(3.799975, -0.725946, on=Side.Top),
        6: RectSMDPad2().at(-3.799975, -0.725946, on=Side.Top),
        7: RectSMDPad2().at(-3.799975, 1.544056, on=Side.Top),
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 4.440932))
    value_text = Finish(Text(">VALUE", 1.0, Anchor.C).at(0.0, -4.440932))
    ref_alt_text = Finish(Text("REF**", 1.0, Anchor.C).at(0.0, -6.440932))

    silk_lines = [
        Silkscreen(Polyline(0.254001, [(3.299898, -0.052794), (3.299898, 0.871006)])),
        Silkscreen(
            Polyline(0.254001, [(-0.000127, -2.440932), (-0.000127, -0.940856)])
        ),
        Silkscreen(Polyline(0.254001, [(3.199873, -0.940856), (-3.200127, -0.940856)])),
        Silkscreen(Polyline(0.254001, [(0.09177, 1.759068), (-1.591974, 1.759068)])),
        Silkscreen(Polyline(0.254001, [(1.299949, -2.440932), (-0.000127, -2.440932)])),
        Silkscreen(Polyline(0.254001, [(1.299949, -0.940856), (1.299949, -2.440932)])),
        Silkscreen(Polyline(0.254001, [(-3.300152, -0.052794), (-3.300152, 0.871006)])),
        Silkscreen(Polyline(0.254001, [(1.59177, 1.759068), (1.407976, 1.759068)])),
    ]

    silk_arcs = [
        Silkscreen(
            ArcPolyline(
                0.059995, [Arc((-3.852654, 2.770574), 0.0299969999999998, 0.0, 360.0)]
            )
        ),
    ]

    # Cutout circles (mounting holes)
    cutout_circles = [
        Cutout(Circle(radius=0.4249935).at(1.5, 0.409182)),
        Cutout(Circle(radius=0.4249935).at(-1.5, 0.409182)),
    ]

    # Solder mask circles
    solder_mask_circles = [
        Soldermask(Circle(radius=0.4249935).at(1.5, 0.409182)),
        Soldermask(Circle(radius=0.4249935).at(-1.5, 0.409182)),
    ]

    # model = Model3D(
    #     "../../3d-models/C778186.wrl",
    #     position=(0, 0, 0),
    #     scale=(1, 1, 1),
    #     rotation=(0, 0, 0)
    # )


# class MK_12C02_G025_Symbol(Symbol):
#     pin_name_size = 0.6
#     pad_name_size = 0.6

#     p1 = Pin(at=(-2, -5), direction=Direction.Down, length=1)
#     p2 = Pin(at=(0, -5), direction=Direction.Down, length=1)
#     p3 = Pin(at=(2, -5), direction=Direction.Down, length=1)
#     p4 = Pin(at=(3, -5), direction=Direction.Down, length=2)
#     p5 = Pin(at=(4, -5), direction=Direction.Down, length=2)
#     p6 = Pin(at=(-3, -5), direction=Direction.Down, length=2)
#     p7 = Pin(at=(-4, -5), direction=Direction.Down, length=2)

#     ref_text = Text(">REF", 1.27, Anchor.C).at(0.0, 1.27)
#     value_text = Text(">VALUE", 1.27, Anchor.C).at(0.0, -2.54)

#     # Switch symbol rectangles
#     switch_rectangles = [
#         Polygon([(0.8, -4.7), (-0.8, -4.7), (-0.8, -5.3), (0.8, -5.3)]),  # Center
#         Polygon([(-1.2, -4.7), (-2.8, -4.7), (-2.8, -5.3), (-1.2, -5.3)]),  # Left
#         Polygon([(2.8, -4.7), (1.2, -4.7), (1.2, -5.3), (2.8, -5.3)]),  # Right
#     ]

#     # Switch connection lines
#     connection_lines = [
#         Polyline(0.0, [(2, -4), (2, -4)]),
#         Polyline(0.0, [(0, -3), (-2, -3), (-2, -4), (-1, -4)]),
#         Polyline(0.0, [(2, -4), (1, -4)]),
#         Polyline(0.0, [(0, -4), (-0, -4)]),
#         Polyline(0.0, [(-2, -4), (-2, -4)]),
#         Polyline(0.0, [(2, -4), (2, -3), (0, -3), (0, -4), (0, -4)]),
#     ]


class MK_12C02_G025(Component):
    """G-Switch"""

    mpn = "MK-12C02-G025"
    reference_designator_prefix = "SW"

    # Switch terminals
    p = Port()  # Common terminal
    t = {1: Port(), 2: Port()}

    # Contact pins
    c = {1: Port(), 2: Port(), 3: Port(), 4: Port()}

    landpattern = C778186()
    symbol = BoxSymbol(
        columns=[Column(down=[PinGroup([t[1], p, t[2], c[1], c[2], c[3], c[4]])])]
    )

    # Pin mappings based on the pin-properties from the original Stanza file
    mappings = [
        PadMapping(
            {
                t[1]: [landpattern.p[1]],  # Terminal 1 to pad 1
                p: [landpattern.p[2]],  # Common terminal to pad 2
                t[2]: [landpattern.p[3]],  # Terminal 2 to pad 3
                c[1]: [landpattern.p[4]],  # Contact 1 to pad 4
                c[2]: [landpattern.p[5]],  # Contact 2 to pad 5
                c[3]: [landpattern.p[6]],  # Contact 3 to pad 6
                c[4]: [landpattern.p[7]],  # Contact 4 to pad 7
            }
        ),
    ]

    # Property for datasheet URL
    datasheet = (
        "https://datasheet.lcsc.com/lcsc/2009021103_G-Switch-MK-12C02-G025_C778186.pdf"
    )


Device: type[MK_12C02_G025] = MK_12C02_G025

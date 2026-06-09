from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.landpattern import Landpattern, Pad
from jitx.layerindex import Side
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polygon, Polyline, Text
from jitx.feature import Finish, Silkscreen, Soldermask, Cutout
from jitx.symbol import Direction, Pin, Symbol
from jitxlib.symbols.box import BoxSymbol, Column, Row, PinGroup


class CircleTHPad(Pad):
    # Using circle shape for through-hole pad
    shape = Circle(radius=0.9)
    layer = Soldermask(Circle(radius=0.9))
    layer = Cutout(Circle(radius=0.5500125))


class OvalTHPad(Pad):
    # Using rectangle as approximation for oval/capsule shape
    rect = rectangle(2.9, 3.0)
    shape = rect
    layer = Soldermask(rect)
    layer = Cutout(rectangle(1.900025, 2.200025))


class C470295(Landpattern):
    p = {
        1: CircleTHPad().at(-2.5, -6.230505, on=Side.Top),
        2: CircleTHPad().at(0.000127, -6.230505, on=Side.Top),
        3: CircleTHPad().at(2.5, -6.230505, on=Side.Top),
        4: OvalTHPad().at(-4.899797, 0.769495, on=Side.Top),
        5: OvalTHPad().at(4.900051, 0.769495, on=Side.Top),
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 8.286513))
    value_text = Finish(Text(">VALUE", 1.0, Anchor.C).at(0.0, -8.286513))
    ref_alt_text = Finish(Text("REF**", 1.0, Anchor.C).at(0.0, -10.286513))

    silk_lines = [
        Silkscreen(Polyline(0.254001, [(-5.08001, 2.349505), (-5.08001, 6.286513)])),
        Silkscreen(Polyline(0.254001, [(-5.08001, -6.286513), (-3.683007, -6.286513)])),
        Silkscreen(Polyline(0.254001, [(5.08001, -6.286513), (5.08001, -0.952502)])),
        Silkscreen(Polyline(0.254001, [(3.556007, -6.286513), (5.08001, -6.286513)])),
        Silkscreen(Polyline(0.254001, [(5.08001, 6.286513), (5.08001, 2.349505)])),
        Silkscreen(Polyline(0.254001, [(-5.08001, 6.286513), (5.08001, 6.286513)])),
        Silkscreen(Polyline(0.254001, [(-5.08001, -0.952502), (-5.08001, -6.286513)])),
    ]

    silk_arcs = [
        Silkscreen(
            ArcPolyline(
                0.059995, [Arc((-5.149809, -6.480518), 0.0299970000000007, 0.0, 360.0)]
            )
        ),
        Silkscreen(
            ArcPolyline(0.254001, [Arc((0.000127, -0.317374), 2.773686, 0.0, 360.0)])
        ),
    ]

    # model = Model3D(
    #     "../../3d-models/C470295.wrl",
    #     position=(0, 0, 0),
    #     scale=(1, 1, 1),
    #     rotation=(0, 0, 0)
    # )


class RK09K1130AP5_Symbol(Symbol):
    pin_name_size = 0.6
    pad_name_size = 0.6

    p = {
        1: Pin(at=(-30, 20), direction=Direction.Right, length=1),
        2: Pin(at=(-31, 21), direction=Direction.Up, length=1),
        3: Pin(at=(-32, 20), direction=Direction.Left, length=1),
        4: Pin(at=(-32, 19), direction=Direction.Right, length=1),
        5: Pin(at=(-32, 19), direction=Direction.Left, length=1),
    }

    ref_text = Text(">REF", 1.27, Anchor.C).at(0.0, 1.27)
    value_text = Text(">VALUE", 1.27, Anchor.C).at(0.0, -2.54)

    # Potentiometer symbol lines
    pot_lines = [
        Polyline(0.0, [(-39.4, 26.6), (-39.4, 27.1)]),  # Wiper line
        Polyline(0.0, [(-40.4, 25.0), (-38.4, 25.0)]),  # Bottom line
        Polyline(
            0.0,
            [(-40.4, 26.4), (-38.4, 26.4), (-38.4, 25.4), (-40.4, 25.4), (-40.4, 26.4)],
        ),  # Rectangle
    ]

    # Potentiometer wiper arrow
    wiper_arrow = Polygon([(-39.4, 26.4), (-39.6, 26.9), (-39.2, 26.9), (-39.4, 26.4)])


class RK09K1130AP5(Component):
    """Compact type potentiometer with 9.8mm width"""

    mpn = "RK09K1130AP5"
    reference_designator_prefix = "VR"

    # Potentiometer pins
    p = {i: Port() for i in range(1, 6)}  # Pin 1

    landpattern = C470295()
    symbol = BoxSymbol(
        rows=[Row(left=[PinGroup([p[3], p[5]])]), Row(right=[PinGroup([p[1], p[4]])])],
        columns=[
            Column(up=[PinGroup([p[2]])]),
        ],
    )

    # Pin mappings based on the pin-properties from the original Stanza file
    mappings = [
        PadMapping(
            {
                p[1]: [landpattern.p[1]],  # Pin 1 to pad 1
                p[2]: [landpattern.p[2]],  # Pin 2 (wiper) to pad 2
                p[3]: [landpattern.p[3]],  # Pin 3 to pad 3
                p[4]: [landpattern.p[4]],  # Pin 4 to pad 4
                p[5]: [landpattern.p[5]],  # Pin 5 to pad 5
            }
        ),
    ]

    # Property for datasheet URL
    datasheet = (
        "https://datasheet.lcsc.com/lcsc/2005150038_ALPSALPINE-RK09K1130AP5_C470295.pdf"
    )


Device: type[RK09K1130AP5] = RK09K1130AP5

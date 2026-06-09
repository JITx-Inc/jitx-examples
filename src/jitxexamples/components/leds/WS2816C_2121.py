from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.landpattern import Landpattern, Pad
from jitx.layerindex import Side
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polygon, Text
from jitx.feature import Finish, Paste, Silkscreen, Soldermask
from jitx.symbol import Direction, Pin, Symbol
from jitxlib.symbols.box import BoxSymbol, Row, PinGroup
from jitx.si import Toleranced
from jitx.property import Property
from dataclasses import dataclass


class RectSMDPad(Pad):
    rect = rectangle(0.7, 0.31999)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class C965561(Landpattern):
    p = {
        1: RectSMDPad().at(-0.940056, 0.630023, on=Side.Top, rotate=180),
        2: RectSMDPad().at(-0.940056, -0.000152, on=Side.Top, rotate=180),
        3: RectSMDPad().at(-0.940056, -0.630074, on=Side.Top, rotate=180),
        4: RectSMDPad().at(0.940056, -0.630074, on=Side.Top, rotate=180),
        5: RectSMDPad().at(0.940056, 0.000102, on=Side.Top, rotate=180),
        6: RectSMDPad().at(0.940056, 0.630023, on=Side.Top, rotate=180),
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 3.143002))
    value_text = Finish(Text(">VALUE", 1.0, Anchor.C).at(0.0, -3.143002))

    # Commented out silkscreen lines from original
    # silk_lines = [
    #     Silkscreen(Polyline(0.254001, [(-1.143002, 1.143002), (1.143002, 1.143002)])),
    #     Silkscreen(Polyline(0.254001, [(1.143002, -1.143002), (-1.143002, -1.143002)])),
    #     Silkscreen(Polyline(0.254001, [(-1.143002, 1.03114), (-1.143002, 1.143002)])),
    #     Silkscreen(Polyline(0.254001, [(-1.143002, -1.143002), (-1.143002, -1.031064)])),
    #     Silkscreen(Polyline(0.254001, [(1.143002, -1.031064), (1.143002, -1.143002)])),
    #     Silkscreen(Polyline(0.254001, [(1.143002, 1.143002), (1.143002, 1.03114)])),
    # ]

    silk_arcs = [
        Silkscreen(
            ArcPolyline(
                0.059995, [Arc((-1.1, 1.100025), 0.0299970000000001, 0.0, 360.0)]
            )
        ),
    ]

    # model = Model3D(
    #     "../../3d-models/C965561.wrl",
    #     position=(0, 0, 0),
    #     scale=(1, 1, 1),
    #     rotation=(0, 0, -180)
    # )


class WS2816C_2121_Symbol(Symbol):
    pin_name_size = 0.6
    pad_name_size = 0.6

    BI = Pin(at=(-2, -4), direction=Direction.Left, length=1)
    DI = Pin(at=(-2, -5), direction=Direction.Left, length=1)
    VDD = Pin(at=(-2, -6), direction=Direction.Left, length=1)
    DO = Pin(at=(2, -6), direction=Direction.Right, length=1)
    BO = Pin(at=(2, -5), direction=Direction.Right, length=1)
    GND = Pin(at=(2, -4), direction=Direction.Right, length=1)

    ref_text = Text(">REF", 1.0, Anchor.C).at(0.0, 1.0)
    value_text = Text(">VALUE", 1.0, Anchor.C).at(0.0, -2.0)

    component_box = Polygon(
        [(2.5, -3.0), (-2.5, -3.0), (-2.5, -7.0), (2.5, -7.0), (2.5, -3.0)]
    )
    pin1_indicator = Circle(radius=0.15).at(-2.0, -3.5)


class WS2816C_2121(Component):
    """16Bit 3 Channel Constant current digital LED"""

    manufacturer = "Worldsemi"
    mpn = "WS2816C-2121"
    reference_designator_prefix = "D"

    # RGB LED pins
    BI = Port()  # Blue input
    DI = Port()  # Data input
    VDD = Port()  # Power supply
    DO = Port()  # Data output
    BO = Port()  # Blue output
    GND = Port()  # Ground

    landpattern = C965561()
    symbol = BoxSymbol(
        rows=[Row(left=[PinGroup([BI, DI, VDD])]), Row(right=[PinGroup([DO, BO, GND])])]
    )

    # Pin mappings based on the pin-properties from the original Stanza file
    mappings = [
        PadMapping(
            {
                BI: [landpattern.p[1]],  # Blue input to pad 1
                DI: [landpattern.p[2]],  # Data input to pad 2
                VDD: [landpattern.p[3]],  # Power supply to pad 3
                DO: [landpattern.p[4]],  # Data output to pad 4
                BO: [landpattern.p[5]],  # Blue output to pad 5
                GND: [landpattern.p[6]],  # Ground to pad 6
            }
        ),
    ]

    # Electrical properties
    @dataclass
    class PowerPin(Property):
        voltage_range: Toleranced

    # Power pin properties
    VDD_power_pin = PowerPin(voltage_range=Toleranced.min_max(3.7, 5.5))

    # Property for datasheet URL
    datasheet = (
        "https://datasheet.lcsc.com/lcsc/2012110135_Worldsemi-WS2816C-2121_C965561.pdf"
    )


Device: type[WS2816C_2121] = WS2816C_2121

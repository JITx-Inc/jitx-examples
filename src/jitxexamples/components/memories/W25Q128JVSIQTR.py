from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.landpattern import Landpattern, Pad
from jitx.layerindex import Side
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polygon, Polyline, Text
from jitx.feature import Finish, Paste, Silkscreen, Soldermask
from jitx.symbol import Direction, Pin, Symbol
from jitxlib.symbols.box import BoxSymbol, Row, PinGroup


class OvalSMDPad(Pad):
    # Using rectangle as approximation for oval/capsule shape
    rect = rectangle(0.629997, 2.250013)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class C97521(Landpattern):
    p = {
        1: OvalSMDPad().at(-1.905004, -3.530099, on=Side.Top),
        2: OvalSMDPad().at(-0.635001, -3.530099, on=Side.Top),
        3: OvalSMDPad().at(0.635001, -3.530099, on=Side.Top),
        4: OvalSMDPad().at(1.905004, -3.530099, on=Side.Top),
        5: OvalSMDPad().at(1.905004, 3.530099, on=Side.Top),
        6: OvalSMDPad().at(0.635001, 3.530099, on=Side.Top),
        7: OvalSMDPad().at(-0.635001, 3.530099, on=Side.Top),
        8: OvalSMDPad().at(-1.905004, 3.530099, on=Side.Top),
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 5.530099))
    value_text = Finish(Text(">VALUE", 1.0, Anchor.C).at(0.0, -5.530099))
    ref_alt_text = Finish(Text("REF**", 1.0, Anchor.C).at(0.0, -7.530099))

    silk_lines = [
        Silkscreen(Polyline(0.1524, [(-2.63871, 2.176403), (2.63871, 2.176403)])),
        Silkscreen(Polyline(0.1524, [(2.63871, 2.176403), (2.63871, -2.176403)])),
        Silkscreen(Polyline(0.1524, [(-2.63871, -2.176403), (-2.63871, 2.176403)])),
        Silkscreen(Polyline(0.1524, [(2.63871, -2.176403), (-2.63871, -2.176403)])),
    ]

    silk_arcs = [
        Silkscreen(
            ArcPolyline(0.3, [Arc((-2.672339, -3.530099), 0.150114, 0.0, 360.0)])
        ),
        Silkscreen(
            ArcPolyline(0.3, [Arc((-1.905004, -1.423927), 0.150114, 0.0, 360.0)])
        ),
        Silkscreen(
            ArcPolyline(
                0.059995, [Arc((-2.58509, -3.920041), 0.0299720000000003, 0.0, 360.0)]
            )
        ),
    ]

    finish_arc = Finish(
        ArcPolyline(0.3, [Arc((-1.905004, -4.350013), 0.150114, 0.0, 360.0)])
    )

    # model = Model3D(
    #     "../../3d-models/C97521.wrl",
    #     position=(0, 0, 0),
    #     scale=(1, 1, 1),
    #     rotation=(0, 0, 0)
    # )


class W25Q128JVSIQTR_Symbol(Symbol):
    pin_name_size = 0.6
    pad_name_size = 0.6

    CS = Pin(at=(-4, -6), direction=Direction.Left, length=1)
    DO = Pin(at=(-4, -7), direction=Direction.Left, length=1)
    IO2 = Pin(at=(-4, -8), direction=Direction.Left, length=1)
    GND = Pin(at=(-4, -9), direction=Direction.Left, length=1)
    DI = Pin(at=(4, -9), direction=Direction.Right, length=1)
    CLK = Pin(at=(4, -8), direction=Direction.Right, length=1)
    IO3 = Pin(at=(4, -7), direction=Direction.Right, length=1)
    VCC = Pin(at=(4, -6), direction=Direction.Right, length=1)

    ref_text = Text(">REF", 1.27, Anchor.C).at(0.0, 1.27)
    value_text = Text(">VALUE", 1.27, Anchor.C).at(0.0, -2.54)

    component_box = Polygon(
        [(4.0, -5.0), (-4.0, -5.0), (-4.0, -10.0), (4.0, -10.0), (4.0, -5.0)]
    )
    pin1_indicators = [
        Circle(radius=0.15).at(-3.5, -5.3),
        Circle(radius=0.15).at(3.5, -5.3),
    ]


class W25Q128JVSIQTR(Component):
    """3V 128M-Bit Serial Flash Memory With Dual/Quad SPI"""

    mpn = "W25Q128JVSIQTR"
    reference_designator_prefix = "U"

    # Flash memory pins
    CS = Port()  # Chip select (active low)
    DO = Port()  # Data output
    IO2 = Port()  # I/O pin 2
    GND = Port()  # Ground
    DI = Port()  # Data input
    CLK = Port()  # Clock
    IO3 = Port()  # I/O pin 3
    VCC = Port()  # Power supply

    landpattern = C97521()
    symbol = BoxSymbol(
        rows=[
            Row(left=[PinGroup([CS, DO, IO2, GND])]),
            Row(right=[PinGroup([DI, CLK, IO3, VCC])]),
        ]
    )

    # Pin mappings based on the pin-properties from the original Stanza file
    mappings = [
        PadMapping(
            {
                CS: [landpattern.p[1]],  # Chip select to pad 1
                DO: [landpattern.p[2]],  # Data output to pad 2
                IO2: [landpattern.p[3]],  # I/O2 to pad 3
                GND: [landpattern.p[4]],  # Ground to pad 4
                DI: [landpattern.p[5]],  # Data input to pad 5
                CLK: [landpattern.p[6]],  # Clock to pad 6
                IO3: [landpattern.p[7]],  # I/O3 to pad 7
                VCC: [landpattern.p[8]],  # Power supply to pad 8
            }
        ),
    ]

    # Property for datasheet URL
    datasheet = "https://datasheet.lcsc.com/lcsc/1811142111_Winbond-Elec-W25Q128JVSIQ_C97521.pdf"


Device: type[W25Q128JVSIQTR] = W25Q128JVSIQTR

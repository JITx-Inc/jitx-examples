"""
Onsemi NCP1117LPST33T3G LDO Regulator
=====================================

1.0A, Low-Dropout Positive, Fixed 3.3V Voltage Regulator
in SOT-223 package.
"""

from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.feature import Finish, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.layerindex import Side
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polygon, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol
from jitxlib.parts.query_api import Capacitor
from jitxlib.symbols.box import BoxSymbol, Row, PinGroup


class RectSMDPad1(Pad):
    rect = rectangle(2.464999, 1.050013)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class RectSMDPad2(Pad):
    rect = rectangle(2.464999, 3.540005)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class C146799(Landpattern):
    p = {
        1: RectSMDPad1().at(2.857506, -2.299975, on=Side.Top),
        2: RectSMDPad1().at(2.857506, 0.0, on=Side.Top),
        3: RectSMDPad1().at(2.857506, 2.299975, on=Side.Top),
        4: RectSMDPad2().at(-2.857506, 0.0, on=Side.Top),
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 5.401219))
    value_text = Finish(Text(">VALUE", 1.0, Anchor.C).at(0.0, -5.401219))
    ref_alt_text = Finish(Text("REF**", 1.0, Anchor.C).at(0.0, -7.401219))

    silk_lines = [
        Silkscreen(Polyline(0.1524, [(-1.396393, -3.401219), (-1.396393, 3.401219)])),
        Silkscreen(Polyline(0.1524, [(1.396393, -3.401219), (-1.396393, -3.401219)])),
        Silkscreen(Polyline(0.1524, [(1.396393, 3.401219), (1.396393, -3.401219)])),
        Silkscreen(Polyline(0.1524, [(-1.396393, 3.401219), (1.396393, 3.401219)])),
    ]

    silk_arcs = [
        Silkscreen(
            ArcPolyline(
                0.059995, [Arc((3.5, -3.250038), 0.0299969999999998, 0.0, 360.0)]
            )
        ),
    ]

    finish_arc = Finish(
        ArcPolyline(0.5, [Arc((4.228626, -2.276607), 0.250013, 0.0, 360.0)])
    )


class NCP1117LPST33T3G_Symbol(Symbol):
    pin_name_size = 0.6
    pad_name_size = 0.6

    ADJGND = Pin(at=(3, -8), direction=Direction.Right, length=2)
    VOUT = Pin(at=(3, -6), direction=Direction.Right, length=2)
    VIN = Pin(at=(-3, -6), direction=Direction.Left, length=2)
    EP = Pin(at=(3, -7), direction=Direction.Right, length=2)

    ref_text = Text(">REF", 1.27, Anchor.C).at(0.0, 1.27)
    value_text = Text(">VALUE", 1.27, Anchor.C).at(0.0, -2.54)

    component_box = Polygon(
        [(3.0, -5.0), (-3.0, -5.0), (-3.0, -9.0), (3.0, -9.0), (3.0, -5.0)]
    )


class NCP1117LPST33T3G(Component):
    """1.0A, Low-Dropout Positive, Fixed and Adjustable Voltage Regulator"""

    mpn = "NCP1117LPST33T3G"
    reference_designator_prefix = "U"

    ADJGND = Port()  # Adjust/Ground pin
    VOUT = Port()  # Output voltage
    VIN = Port()  # Input voltage

    landpattern = C146799()
    symbol = BoxSymbol(
        rows=[Row(right=[PinGroup([ADJGND, VOUT])]), Row(left=[PinGroup([VIN])])]
    )

    # Pin mappings based on the pin-properties from the original Stanza file
    mappings = [
        PadMapping(
            {
                ADJGND: [landpattern.p[1]],  # Adjust/Ground to pad 1
                VOUT: [landpattern.p[2], landpattern.p[4]],  # Output to pads 2 and 4
                VIN: [landpattern.p[3]],  # Input to pad 3
            }
        ),
    ]

    # Property for datasheet URL
    datasheet = (
        "https://datasheet.lcsc.com/lcsc/1809111714_onsemi-NCP1117LPST33T3G_C146799.pdf"
    )


class NCP1117LPST33T3GCircuit(Circuit):
    """
    NCP1117LPST33T3G Circuit
    Voltage regulator module with bypass capacitors
    """

    vin = Power()
    vout = Power()

    def __init__(self):
        self.ld = NCP1117LPST33T3G()

        self.nets = [
            self.vin.Vp + self.ld.VIN,
            self.vin.Vn + self.ld.ADJGND,
            self.vout.Vp + self.ld.VOUT,
            self.vout.Vn + self.ld.ADJGND,
        ]

        # Input Capacitor (10uF)
        self.cin = Capacitor(capacitance=10e-6, case="0805").insert(
            self.ld.VIN, self.ld.ADJGND, short_trace=True
        )

        # Output Capacitor (10uF)
        self.cout = Capacitor(capacitance=10e-6, case="0805").insert(
            self.ld.VOUT, self.ld.ADJGND, short_trace=True
        )


Device: type[NCP1117LPST33T3GCircuit] = NCP1117LPST33T3GCircuit

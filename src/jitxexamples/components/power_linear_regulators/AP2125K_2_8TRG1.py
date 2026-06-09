"""
Diodes Incorporated AP2125K-2.8TRG1 LDO Regulator
=================================================

300mA, High Speed, Extremely Low Dropout CMOS Regulator
Fixed 2.8V Output, SOT-23-5 Package
"""

from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.net import Port
from jitx.shapes.primitive import Polygon, Text
from jitx.symbol import Direction, Pin, Symbol
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.parts import Capacitor
from jitxlib.symbols.box import BoxSymbol, Row, PinGroup
from jitxlib.landpatterns.generators.sot import SOT23_5, T, SOTLeadProfile


class AP2125K_2_8TRG1_Symbol(Symbol):
    pin_name_size = 0.6
    pad_name_size = 0.6

    VIN = Pin(at=(-2, 0), direction=Direction.Left, length=1)
    GND = Pin(at=(-2, -1), direction=Direction.Left, length=1)
    EN = Pin(at=(-2, -2), direction=Direction.Left, length=1)
    NC = Pin(at=(2, -2), direction=Direction.Right, length=1)
    VOUT = Pin(at=(2, 0), direction=Direction.Right, length=1)

    ref_text = Text(">REF", 1.0, Anchor.C).at(0.0, 1.0)
    value_text = Text(">VALUE", 1.0, Anchor.C).at(0.0, -3.0)

    # Voltage regulator symbol box
    component_box = Polygon(
        [(1.5, 0.5), (-1.5, 0.5), (-1.5, -2.5), (1.5, -2.5), (1.5, 0.5)]
    )


class AP2125K_2_8TRG1(Component):
    """300ma CMOS LDO Regulator NPN"""

    mpn = "AP2125K-2.8TRG1"
    reference_designator_prefix = "U"

    VIN = Port()
    GND = Port()
    EN = Port()
    NC = Port()
    VOUT = Port()
    landpattern = (
        SOT23_5()
        .package_body(
            RectanglePackage(
                width=T.min_max(1.5, 1.7),
                length=T.min_max(2.82, 3.1),
                height=T.min_max(1.4, 1.45),
            )
        )
        .lead_profile(
            SOTLeadProfile(
                span=T.min_max(2.65, 3.0),
            )
        )
    )
    symbol = BoxSymbol(
        rows=[Row(left=[PinGroup([VIN, GND, EN])], right=[PinGroup([NC, VOUT])])]
    )

    # Pin mappings based on the pin-properties from the original Stanza file
    mappings = [
        PadMapping(
            {
                VIN: [landpattern.p[1]],
                GND: [landpattern.p[2]],
                EN: [landpattern.p[3]],
                NC: [landpattern.p[4]],
                VOUT: [landpattern.p[5]],
            }
        ),
    ]

    # Properties
    LCSC = "C176953"


class AP2125K_2_8TRG1Circuit(Circuit):
    vin = Power()
    vout = Power()
    EN = Port()

    def __init__(self):
        self.reg = AP2125K_2_8TRG1()

        self.nets = [
            self.vin.Vp + self.reg.VIN,
            self.vin.Vn + self.reg.GND,
            self.vout.Vp + self.reg.VOUT,
            self.vout.Vn + self.reg.GND,
            self.EN + self.reg.EN,
        ]

        # Input Capacitor (1uF)
        self.cin = Capacitor(capacitance=1e-6).insert(
            self.reg.VIN, self.reg.GND, short_trace=True
        )

        # Output Capacitor (1uF)
        self.cout = Capacitor(capacitance=1e-6).insert(
            self.reg.VOUT, self.reg.GND, short_trace=True
        )

        self.reg.NC.no_connect()


Device: type[AP2125K_2_8TRG1Circuit] = AP2125K_2_8TRG1Circuit

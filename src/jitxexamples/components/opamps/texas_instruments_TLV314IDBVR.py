"""
Texas Instruments TLV314IDBVR OpAmp
===================================

3-MHz, Low-Power, Internal EMI Filter, RRIO, CMOS Operational Amplifier
in SOT-23-5 package.
"""

from jitx.anchor import Anchor
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.landpattern import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.primitive import Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitxlib.landpatterns.generators.sot import SOT23_5, SOTLeadProfile, T
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.parts import Capacitor


class SymbolTLV314IDBVR(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    INn = Pin((-4, 2), 4, Direction.Left)
    INp = Pin((-4, -2), 4, Direction.Left)
    Vn = Pin((0, -4), 4, Direction.Down)
    OUT = Pin((4, 0), 4, Direction.Right)
    Vp = Pin((0, 4), 4, Direction.Up)
    reference_designator = Text(">REF", 0.55559, Anchor.C).at((0, 5.57481))
    value_label = Text(">VALUE", 0.55559, Anchor.C).at((0, 4.78741))
    shapes = [
        Polyline(
            0.254,
            [
                (-4, -4),
                (4, 0),
                (-4, 4),
                (-4, -4),
            ],
        ),
        Polyline(0.254, [(-3.2, 2), (-2, 2)]),
        Polyline(0.254, [(-3.2, -2), (-2, -2)]),
        Polyline(0.254, [(-2.6, -1.4), (-2.6, -2.6)]),
        Polyline(0.254, [(0, 4), (0, 2)]),
        Polyline(0.254, [(0, -2), (0, -4)]),
    ]


class TLV314IDBVR(Component):
    """
    Texas Instruments TLV314IDBVR OpAmp

    3-MHz, Low-Power, Internal EMI Filter, RRIO, CMOS Operational Amplifier

    Key Specifications:
    - Supply Voltage: 1.8V to 5.5V
    - Bandwidth: 3 MHz (typical)
    - Slew Rate: 1.4 V/µs
    - Offset Voltage: 1.5 mV (max)
    - Package: SOT-23-5

    Pin Configuration:
    - INn: Inverting input
    - INp: Non-inverting input
    - Vn: Negative supply (GND)
    - OUT: Output
    - Vp: Positive supply

    Typical Applications:
    - Low-power signal conditioning
    - Sensor interfaces
    - Active filters
    - General-purpose amplification

    Datasheet: https://www.lcsc.com/datasheet/lcsc_datasheet_1809251733_Texas-Instruments-TLV314IDBVR_C133032.pdf
    """

    manufacturer = "Texas Instruments"
    mpn = "TLV314IDBVR"
    reference_designator_prefix = "U"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_1809251733_Texas-Instruments-TLV314IDBVR_C133032.pdf"

    INn = Port()
    INp = Port()
    Vn = Port()
    OUT = Port()
    Vp = Port()

    landpattern = (
        SOT23_5()
        .package_body(
            RectanglePackage(
                width=T.min_max(1.5, 1.7),
                length=T.min_max(2.82, 3.1),
                height=T.min_max(0.9, 1.0),
            )
        )
        .lead_profile(
            SOTLeadProfile(
                span=T.min_max(2.65, 3.0),
            )
        )
    )
    landpattern.model3d = Model3D(
        "texas_instruments_TLV314IDBVR.stp",
        position=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
        rotation=(0.0, 0.0, 0.0),
    )

    symbol = SymbolTLV314IDBVR()

    cmappings = [
        SymbolMapping(
            {
                INn: symbol.INn,
                INp: symbol.INp,
                Vn: symbol.Vn,
                OUT: symbol.OUT,
                Vp: symbol.Vp,
            }
        ),
        PadMapping(
            {
                OUT: [landpattern.p[1]],
                Vn: [landpattern.p[2]],
                INp: [landpattern.p[3]],
                INn: [landpattern.p[4]],
                Vp: [landpattern.p[5]],
            }
        ),
    ]


class TLV314IDBVRCircuit(Circuit):
    power = Power()
    INn = Port()
    INp = Port()
    OUT = Port()

    def __init__(self):
        self.opamp = TLV314IDBVR()

        self.nets = [
            self.power.Vp + self.opamp.Vp,
            self.power.Vn + self.opamp.Vn,
            self.INn + self.opamp.INn,
            self.INp + self.opamp.INp,
            self.OUT + self.opamp.OUT,
        ]

        self.byp = Capacitor(capacitance=100e-9).insert(
            self.opamp.Vp, self.opamp.Vn, short_trace=True
        )


Device: type[TLV314IDBVRCircuit] = TLV314IDBVRCircuit

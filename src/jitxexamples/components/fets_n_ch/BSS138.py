from jitx.anchor import Anchor
from jitx.component import Component as JITXComponent
from jitx.landpattern import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.primitive import Polygon, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitxlib.landpatterns.generators.sot import SOT23_3, SOTLeadProfile, T
from jitxlib.landpatterns.package import RectanglePackage


class SymbolBSS138_C713688(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    D = Pin((0, 2), 2, Direction.Up)
    G = Pin((-4, 0), 2, Direction.Left)
    S = Pin((0, -2), 2, Direction.Down)
    layer_reference = Text(">REF", 0.55559, Anchor.C).at((0, 3.57481))
    layer_value = Text(">VALUE", 0.55559, Anchor.C).at((0, 2.78741))
    draws = [
        Polyline(0.254, [(-2, 1.4), (0, 1.4), (0, 2), (2, 2), (2, 0.4)]),
        Polyline(0.254, [(-2, 0), (0, 0), (0, -2), (2, -2), (2, -0.6)]),
        Polyline(0.254, [(0, -1.4), (-2, -1.4)]),
        Polyline(0.254, [(-2.4, 1.8), (-2.4, -1.8)]),
        Polyline(0.254, [(-2, 1.8), (-2, 1)]),
        Polyline(0.254, [(-2, -0.4), (-2, 0.4)]),
        Polyline(0.254, [(-2, -1.8), (-2, -1)]),
        Polyline(0.254, [(-4.00001, 0), (-2.4, 0)]),
        Polyline(0.254, [(2.80001, 0.4), (2.4, 0.4), (1.6, 0.4), (1.2, 0.4)]),
        Polygon([(-2, 0), (-0.8, 0.4), (-0.8, -0.4)]),
        Polygon([(2, 0.4), (1.4, -0.6), (2.60001, -0.6)]),
    ]


class BSS138(JITXComponent):
    """
    BSS138 N-Channel MOSFET

    Key Specifications:
    - Drain-Source Voltage (Vdss): 50V
    - Continuous Drain Current (Id): 220mA
    - On-Resistance (Rds): 3.5Ω @ Vgs=10V
    - Gate Threshold Voltage: 0.8V - 1.5V
    - Package: SOT-23-3

    Pin Configuration:
    - G: Gate (Pin 1)
    - S: Source (Pin 2)
    - D: Drain (Pin 3)

    Typical Applications:
    - Level shifting circuits
    - Low-power switching
    - Logic interfacing
    - Battery-powered systems

    Datasheet: https://www.lcsc.com/datasheet/lcsc_datasheet_2008011839_LGE-BSS138_C713688.pdf
    """

    manufacturer = "LGE"
    mpn = "BSS138"
    reference_designator_prefix = "Q"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_2008011839_LGE-BSS138_C713688.pdf"

    D = Port()
    G = Port()
    S = Port()

    landpattern = (
        SOT23_3()
        .package_body(
            RectanglePackage(
                width=T.min_max(1.2, 1.4),
                length=T.min_max(2.8, 3.0),
                height=T.min_max(0.9, 1.1),
            )
        )
        .lead_profile(
            SOTLeadProfile(
                span=T.min_max(2.3, 2.6),
            )
        )
    )
    landpattern.model3d = Model3D(
        "BSS138.stp",
        position=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
        rotation=(0.0, 0.0, 0.0),
    )

    symbol = SymbolBSS138_C713688()

    cmappings = [
        SymbolMapping({D: symbol.D, G: symbol.G, S: symbol.S}),
        PadMapping(
            {
                G: [landpattern.p[1]],
                S: [landpattern.p[2]],
                D: [landpattern.p[3]],
            }
        ),
    ]


Device: type[BSS138] = BSS138

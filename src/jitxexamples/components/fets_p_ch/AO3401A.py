from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.net import Port
from jitx.shapes.primitive import Polyline, Text
from jitx.symbol import Direction, Pin, Symbol
from jitxlib.landpatterns.generators.sot import SOT23_3, SOTLeadProfile, T
from jitxlib.landpatterns.package import RectanglePackage


class AO3401A_Symbol(Symbol):
    pin_name_size = 0.6
    pad_name_size = 0.6

    # P-channel MOSFET symbol
    G = Pin(at=(-2, 0), direction=Direction.Left, length=1)  # Gate
    S = Pin(at=(0, -1), direction=Direction.Down, length=1)  # Source
    D = Pin(at=(0, 1), direction=Direction.Up, length=1)  # Drain

    ref_text = Text(">REF", 1.0, Anchor.C).at(0.0, 2.5)
    value_text = Text(">VALUE", 1.0, Anchor.C).at(0.0, -2.5)

    # MOSFET symbol elements
    # Channel line
    channel_line = Polyline(0.1, [(-0.5, -0.5), (0.5, -0.5)])

    # Gate line
    gate_line = Polyline(0.1, [(-1, 0), (-0.5, 0)])

    # Drain and source lines
    drain_line = Polyline(0.1, [(0, 0.5), (0, 1.5)])
    source_line = Polyline(0.1, [(0, -0.5), (0, -1.5)])

    # P-channel indicator (arrow pointing toward gate)
    p_channel_arrow = Polyline(
        0.1, [(-0.3, -0.3), (-0.1, -0.5), (-0.3, -0.7), (-0.3, -0.3)]
    )


class AO3401A(Component):
    """
    AO3401A P-Channel MOSFET

    Key Specifications:
    - Drain-Source Voltage (Vdss): -30V
    - Continuous Drain Current (Id): -4A
    - On-Resistance (Rds): 44mΩ @ Vgs=-10V, Id=-4.3A
    - Power Dissipation: 1.4W
    - Gate Threshold Voltage: -1.3V @ 250µA
    - Package: SOT-23-3

    Pin Configuration:
    - G: Gate
    - S: Source
    - D: Drain

    Typical Applications:
    - High-side load switching
    - Battery protection circuits
    - Power management
    - Motor control

    Datasheet: https://aosmd.com/res/data_sheets/AO3401A.pdf
    """

    manufacturer = "Alpha & Omega Semicon"
    mpn = "AO3401A"
    reference_designator_prefix = "Q"
    datasheet = "https://aosmd.com/res/data_sheets/AO3401A.pdf"

    G = Port()
    D = Port()
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

    symbol = AO3401A_Symbol()

    mappings = [
        PadMapping(
            {
                G: [landpattern.p[1]],
                S: [landpattern.p[2]],
                D: [landpattern.p[3]],
            }
        ),
    ]


Device: type[AO3401A] = AO3401A

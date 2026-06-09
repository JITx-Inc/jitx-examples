from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.circuit import Circuit
from jitx.common import Power
from jitx.component import Component
from jitx.landpattern import Landpattern, Pad
from jitx.layerindex import Side
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polyline, Text
from jitx.feature import Finish, Paste, Silkscreen, Soldermask
from jitx.symbol import Direction, Pin, Symbol
from jitxlib.parts import Capacitor, Resistor


class RectSMDPad(Pad):
    rect = rectangle(1.050013, 0.7)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class C116501(Landpattern):
    p = {
        1: RectSMDPad().at(-2.100076, 1.087948, on=Side.Top),
        2: RectSMDPad().at(2.100076, 1.087948, on=Side.Top),
        3: RectSMDPad().at(-2.100076, -1.061913, on=Side.Top),
        4: RectSMDPad().at(2.100076, -1.061913, on=Side.Top),
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 3.536894))
    value_text = Finish(Text(">VALUE", 1.0, Anchor.C).at(0.0, -3.536894))
    ref_alt_text = Finish(Text("REF**", 1.0, Anchor.C).at(0.0, -5.536894))

    silk_lines = [
        Silkscreen(Polyline(0.254001, [(-0.508001, -1.002985), (0.508001, -1.002985)])),
        Silkscreen(Polyline(0.254001, [(-0.508001, 1.02902), (0.508001, 1.02902)])),
        Silkscreen(Polyline(0.254001, [(1.366421, 1.536894), (-1.366421, 1.536894)])),
        Silkscreen(Polyline(0.254001, [(2.199898, 0.556833), (2.199898, -0.530798)])),
        Silkscreen(Polyline(0.254001, [(-2.199898, 0.556833), (-2.199898, -0.530798)])),
        Silkscreen(Polyline(0.254001, [(-1.381102, -1.536894), (1.381102, -1.536894)])),
    ]

    silk_arcs = [
        Silkscreen(
            ArcPolyline(
                0.254001, [Arc((-0.508001, 0.0130179999999999), 1.016003, 90.0, -180.0)]
            )
        ),
        Silkscreen(
            ArcPolyline(
                0.254001,
                [
                    Arc(
                        (2.54000061702092, 0.013018),
                        2.27184561702092,
                        206.565100611358,
                        -53.1302012227158,
                    )
                ],
            )
        ),
        Silkscreen(
            ArcPolyline(
                0.059995, [Arc((-2.299975, 1.612967), 0.0299719999999999, 0.0, 360.0)]
            )
        ),
    ]


class PTS810SJM250SMTRLFS_Symbol(Symbol):
    pin_name_size = 0.6
    pad_name_size = 0.6

    p1 = Pin(at=(-2, -4), direction=Direction.Left, length=2)
    p2 = Pin(at=(2, -4), direction=Direction.Right, length=2)
    p3 = Pin(at=(-2, -6), direction=Direction.Left, length=2)
    p4 = Pin(at=(2, -6), direction=Direction.Right, length=2)

    ref_text = Text(">REF", 1.27, Anchor.C).at(0.0, 1.27)
    value_text = Text(">VALUE", 1.27, Anchor.C).at(0.0, -2.54)

    # Switch symbol lines
    switch_lines = [
        Polyline(0.0, [(0, -6), (0, -5.4)]),  # Vertical line
        Polyline(0.0, [(0, -5.4), (-0.5, -4.7)]),  # Diagonal line
        Polyline(0.0, [(-2, -4), (2, -4)]),  # Top horizontal line
        Polyline(0.0, [(-2, -6), (2, -6)]),  # Bottom horizontal line
        Polyline(0.0, [(0, -4), (0, -4.6)]),  # Center vertical line
    ]


class PTS810SJM250SMTRLFS(Component):
    """
    C&K PTS810 Series Tactile Switch

    Reliable microminiature surface mount tactile switch with 2.5mm actuator.

    Key Specifications:
    - Actuation force: 250gf
    - Travel: 0.25mm
    - Operating life: 1,000,000 cycles minimum
    - Contact resistance: 100mΩ maximum
    - Operating temperature: -40°C to +85°C
    - Package: SMT, 6.0mm x 3.5mm x 2.5mm

    Pin Configuration:
    - p1, p3: Connected together when switch is pressed (one side of switch)
    - p2, p4: Connected together when switch is pressed (other side of switch)
    - When pressed: p1/p3 connects to p2/p4
    - When released: No connection

    Note: Pins 1 and 3 are internally connected, as are pins 2 and 4.
    This provides mechanical stability and redundant electrical connections.

    Typical Applications:
    - User interface buttons
    - Mode selection
    - Reset buttons
    - Menu navigation

    Datasheet: https://datasheet.lcsc.com/lcsc/1811092141_C-K-PTS810SJM250SMTRLFS_C116501.pdf
    """

    mpn = "PTS810SJM250SMTRLFS"
    manufacturer = "C&K"
    reference_designator_prefix = "SW"
    datasheet = (
        "https://datasheet.lcsc.com/lcsc/1811092141_C-K-PTS810SJM250SMTRLFS_C116501.pdf"
    )

    p1 = Port()
    p2 = Port()
    p3 = Port()
    p4 = Port()

    landpattern = C116501()
    symbol = PTS810SJM250SMTRLFS_Symbol()

    mappings = [
        PadMapping(
            {
                p1: [landpattern.p[1]],
                p2: [landpattern.p[2]],
                p3: [landpattern.p[3]],
                p4: [landpattern.p[4]],
            }
        ),
    ]


class PTS810SJM250SMTRLFSCircuit(Circuit):
    """
    Tactile Switch with Pull-up and Debounce Circuit

    Complete tactile switch circuit with:
    - Pull-up resistor (10kΩ) to ensure defined state when not pressed
    - Debounce capacitor (100nF) to filter mechanical bounce
    - Press detection: Output goes LOW when button is pressed

    External Interface:
    - power: Power supply (VCC and GND)
    - button_out: Button state output (HIGH=released, LOW=pressed)

    Circuit Operation:
    - When released: Output pulled HIGH by 10kΩ resistor
    - When pressed: Output pulled LOW through switch
    - Capacitor filters bounce during press/release transitions

    Typical RC time constant: 10kΩ × 100nF = 1ms debounce time
    """

    power = Power()
    button_out = Port()

    def __init__(self):
        """Initialize the tactile switch circuit"""

        self.switch = PTS810SJM250SMTRLFS()

        # Pull-up resistor (10kΩ)
        # Ensures button_out is HIGH when switch is not pressed
        self.r_pullup = Resistor(resistance=10e3, case="0603").insert(
            self.button_out, self.power.Vp
        )

        # Debounce capacitor (100nF)
        # Filters mechanical bounce when pressing/releasing
        # Place close to switch for effective debouncing
        self.c_debounce = Capacitor(capacitance=100e-9, case="0603").insert(
            self.switch.p1, self.power.Vn, short_trace=True
        )

        # Net connections
        # p1 and p3 are connected together (one side of switch)
        # p2 and p4 are connected together (other side of switch)
        self.nets = [
            self.switch.p1 + self.switch.p3 + self.button_out,
            self.switch.p2 + self.switch.p4 + self.power.Vn,
        ]


Device: type[PTS810SJM250SMTRLFSCircuit] = PTS810SJM250SMTRLFSCircuit

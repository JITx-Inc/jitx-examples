from jitx.anchor import Anchor
from jitx.component import Component as JITXComponent
from jitx.circuit import Circuit
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polygon, Polyline, Text
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitxlib.parts.query_api import Capacitor, Resistor
from ..leds.KT_0603R import KT_0603R
from ..leds.KT_0603G import KT_0603G


class RectangleSmdPad(Pad):
    shape = rectangle(0.28, 0.665)
    solder_mask = [Soldermask(rectangle(0.382, 0.767))]


class RectangleSmdPad1(Pad):
    shape = rectangle(0.665, 0.28)
    solder_mask = [Soldermask(rectangle(0.767, 0.382))]


class RectangleSmdPad2(Pad):
    shape = rectangle(1.68, 1.68)
    solder_mask = [Soldermask(rectangle(1.782, 1.782))]


class LandpatternVQFN_16_L3_0_W3_0_P0_50_BL_EP(Landpattern):
    name = "VQFN-16_L3.0-W3.0-P0.50-BL-EP"
    p = {
        1: RectangleSmdPad().at((-0.75, -1.4075)),
        2: RectangleSmdPad().at((-0.25, -1.4075)),
        3: RectangleSmdPad().at((0.25, -1.4075)),
        4: RectangleSmdPad().at((0.75, -1.4075)),
        5: RectangleSmdPad1().at((1.407, -0.7505)),
        6: RectangleSmdPad1().at((1.407, -0.2495)),
        7: RectangleSmdPad1().at((1.407, 0.2495)),
        8: RectangleSmdPad1().at((1.407, 0.7505)),
        9: RectangleSmdPad().at((0.75, 1.4075)),
        10: RectangleSmdPad().at((0.25, 1.4075)),
        11: RectangleSmdPad().at((-0.25, 1.4075)),
        12: RectangleSmdPad().at((-0.75, 1.4075)),
        13: RectangleSmdPad1().at((-1.407, 0.7505)),
        14: RectangleSmdPad1().at((-1.407, 0.2495)),
        15: RectangleSmdPad1().at((-1.407, -0.2495)),
        16: RectangleSmdPad1().at((-1.407, -0.7505)),
        17: RectangleSmdPad2().at((0, -0.0005)),
    }
    pcb_layer_reference = Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 3.4966)))
    pcb_layer_value = Custom(
        Text(">VALUE", 0.5, Anchor.W).at((-0.75, 2.4966)), name="Fab"
    )
    silkscreen = [
        Silkscreen(
            Polyline(0.152, [(-1.576, 1.0805), (-1.576, 1.5765), (-1.08, 1.5765)])
        ),
        Silkscreen(
            Polyline(0.152, [(1.576, 1.0805), (1.576, 1.5765), (1.081, 1.5765)])
        ),
        Silkscreen(
            Polyline(0.152, [(-1.576, -1.0805), (-1.576, -1.5765), (-1.08, -1.5765)])
        ),
        Silkscreen(
            Polyline(0.152, [(1.576, -1.0805), (1.576, -1.5765), (1.081, -1.5765)])
        ),
        Silkscreen(ArcPolyline(0.15, [Arc((-0.75, -2.0405), 0.075, 0, -360)])),
    ]
    custom_layer = [
        Custom(ArcPolyline(0.06, [Arc((-1.5, -1.5005), 0.03, 0, -360)]), name="Fab"),
        Custom(ArcPolyline(0.15, [Arc((-0.75, -1.8005), 0.075, 0, -360)]), name="Fab"),
    ]
    paste = [
        Paste(
            Polygon(
                [
                    (-0.672, -0.6725),
                    (-0.672, 0.6715),
                    (0.672, 0.6715),
                    (0.672, -0.6725),
                    (-0.672, -0.6725),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (-0.89, -1.7405),
                    (-0.89, -1.0755),
                    (-0.61, -1.0755),
                    (-0.61, -1.7405),
                    (-0.89, -1.7405),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (-0.39, -1.7405),
                    (-0.39, -1.0755),
                    (-0.11, -1.0755),
                    (-0.11, -1.7405),
                    (-0.39, -1.7405),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (0.11, -1.7405),
                    (0.11, -1.0755),
                    (0.39, -1.0755),
                    (0.39, -1.7405),
                    (0.11, -1.7405),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (0.61, -1.7405),
                    (0.61, -1.0755),
                    (0.89, -1.0755),
                    (0.89, -1.7405),
                    (0.61, -1.7405),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (1.74, -0.8905),
                    (1.74, -0.6105),
                    (1.075, -0.6105),
                    (1.075, -0.8905),
                    (1.74, -0.8905),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (1.74, -0.3905),
                    (1.74, -0.1105),
                    (1.075, -0.1105),
                    (1.075, -0.3905),
                    (1.74, -0.3905),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (1.74, 0.1095),
                    (1.74, 0.3895),
                    (1.075, 0.3895),
                    (1.075, 0.1095),
                    (1.74, 0.1095),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (1.74, 0.6095),
                    (1.74, 0.8895),
                    (1.075, 0.8895),
                    (1.075, 0.6095),
                    (1.74, 0.6095),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (0.61, 1.7395),
                    (0.61, 1.0745),
                    (0.89, 1.0745),
                    (0.89, 1.7395),
                    (0.61, 1.7395),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (0.11, 1.7395),
                    (0.11, 1.0745),
                    (0.39, 1.0745),
                    (0.39, 1.7395),
                    (0.11, 1.7395),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (-0.39, 1.7395),
                    (-0.39, 1.0745),
                    (-0.11, 1.0745),
                    (-0.11, 1.7395),
                    (-0.39, 1.7395),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (-0.89, 1.7395),
                    (-0.89, 1.0745),
                    (-0.61, 1.0745),
                    (-0.61, 1.7395),
                    (-0.89, 1.7395),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (-1.075, 0.6095),
                    (-1.075, 0.8895),
                    (-1.74, 0.8895),
                    (-1.74, 0.6095),
                    (-1.075, 0.6095),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (-1.075, 0.1095),
                    (-1.075, 0.3895),
                    (-1.74, 0.3895),
                    (-1.74, 0.1095),
                    (-1.075, 0.1095),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (-1.075, -0.3905),
                    (-1.075, -0.1105),
                    (-1.74, -0.1105),
                    (-1.74, -0.3905),
                    (-1.075, -0.3905),
                ]
            )
        ),
        Paste(
            Polygon(
                [
                    (-1.075, -0.8905),
                    (-1.075, -0.6105),
                    (-1.74, -0.6105),
                    (-1.74, -0.8905),
                    (-1.075, -0.8905),
                ]
            )
        ),
    ]
    courtyard = [Courtyard(rectangle(3.581, 3.582))]
    model3ds = [
        Model3D(
            "BQ24078RGTR.stp",
            position=(0.0, 0.0, 0.0),
            scale=(1.0, 1.0, 1.0),
            rotation=(0.0, 0.0, 0.0),
        )
    ]


class SymbolBQ24078RGTR(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    TS = Pin((-9, 6), 2, Direction.Left)
    BAT0 = Pin((-9, 4), 2, Direction.Left)
    BAT1 = Pin((-9, 2), 2, Direction.Left)
    CE_NOT = Pin((-9, 0), 2, Direction.Left)
    EN2 = Pin((-9, -2), 2, Direction.Left)
    EN1 = Pin((-9, -4), 2, Direction.Left)
    PGOOD_NOT = Pin((-9, -6), 2, Direction.Left)
    VSS = Pin((-9, -8), 2, Direction.Left)
    CHG_NOT = Pin((9, -8), 2, Direction.Right)
    OUT0 = Pin((9, -6), 2, Direction.Right)
    OUT1 = Pin((9, -4), 2, Direction.Right)
    ILIM = Pin((9, -2), 2, Direction.Right)
    IN = Pin((9, 0), 2, Direction.Right)
    TMR = Pin((9, 2), 2, Direction.Right)
    SYSOFF = Pin((9, 4), 2, Direction.Right)
    ISET = Pin((9, 6), 2, Direction.Right)
    EP = Pin((9, 8), 2, Direction.Right)
    layer_reference = Text(">REF", 0.55559, Anchor.C).at((0, 10.87482))
    layer_value = Text(">VALUE", 0.55559, Anchor.C).at((0, 10.08742))
    draws = [rectangle(18.00004, 20.00004), Circle(radius=0.3).at((-8.00002, 9.00002))]


class Component(JITXComponent):
    """1.5-A High Battery Voltage Li-Ion Battery Chargers with Power-Path Management IC"""

    manufacturer = "Texas Instruments"
    mpn = "BQ24078RGTR"
    reference_designator_prefix = "U"
    datasheet = "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2001031722_Texas-Instruments-BQ24078RGTR_C473396.pdf"
    TS = Port()
    BAT0 = Port()
    BAT1 = Port()
    CE_NOT = Port()
    EN2 = Port()
    EN1 = Port()
    PGOOD_NOT = Port()
    VSS = Port()
    CHG_NOT = Port()
    OUT0 = Port()
    OUT1 = Port()
    ILIM = Port()
    IN = Port()
    TMR = Port()
    SYSOFF = Port()
    ISET = Port()
    EP = Port()
    landpattern = LandpatternVQFN_16_L3_0_W3_0_P0_50_BL_EP()
    symbol = SymbolBQ24078RGTR()
    cmappings = [
        SymbolMapping(
            {
                TS: symbol.TS,
                BAT0: symbol.BAT0,
                BAT1: symbol.BAT1,
                CE_NOT: symbol.CE_NOT,
                EN2: symbol.EN2,
                EN1: symbol.EN1,
                PGOOD_NOT: symbol.PGOOD_NOT,
                VSS: symbol.VSS,
                CHG_NOT: symbol.CHG_NOT,
                OUT0: symbol.OUT0,
                OUT1: symbol.OUT1,
                ILIM: symbol.ILIM,
                IN: symbol.IN,
                TMR: symbol.TMR,
                SYSOFF: symbol.SYSOFF,
                ISET: symbol.ISET,
                EP: symbol.EP,
            }
        ),
        PadMapping(
            {
                TS: landpattern.p[1],
                BAT0: landpattern.p[2],
                BAT1: landpattern.p[3],
                CE_NOT: landpattern.p[4],
                EN2: landpattern.p[5],
                EN1: landpattern.p[6],
                PGOOD_NOT: landpattern.p[7],
                VSS: landpattern.p[8],
                CHG_NOT: landpattern.p[9],
                OUT0: landpattern.p[10],
                OUT1: landpattern.p[11],
                ILIM: landpattern.p[12],
                IN: landpattern.p[13],
                TMR: landpattern.p[14],
                SYSOFF: landpattern.p[15],
                ISET: landpattern.p[16],
                EP: landpattern.p[17],
            }
        ),
    ]


class BQ24078RGTR(Circuit):
    """
    BQ24078RGTR Lithium Battery Charger Circuit

    Texas Instruments 1.5A Li-Ion Battery Charger with Power-Path Management

    Key Features:
    - Input voltage: 4.35V to 6.45V
    - Charge current: Programmable up to 1.5A (set to 325mA in this design)
    - USB current limit: 500mA (configurable)
    - Power-path management for simultaneous charge and load
    - Status LEDs: Charge (red) and Power Good (green)
    - Thermal regulation and safety timer

    External Interface:
    - vin: Input voltage (USB/wall adapter)
    - vout: System output voltage
    - gnd: Ground
    - bat_plus: Battery positive terminal

    Component Values:
    - Input/Output bypass caps: 4.7µF (close to IC)
    - Charge current: Set by 2.7kΩ resistor (325mA)
    - USB current limit: 500mA (EN1=high, EN2=low)

    Datasheet: https://www.ti.com/lit/ds/symlink/bq24078.pdf
    """

    # Port definitions (external interface)
    vin = Port()
    vout = Port()
    gnd = Port()
    bat_plus = Port()

    def __init__(self):
        """Initialize the battery charger circuit with all components and connections"""

        # Create the battery charger IC instance
        self.bq = Component()

        # Input bypass capacitor (4.7µF, 16V rated)
        # Place close to IN pin for input ripple filtering
        self.c_in = Capacitor(
            capacitance=4.7e-6,
            rated_voltage=16.0,
        ).insert(self.bq.IN, self.gnd, short_trace=True)

        # Output bypass capacitor (4.7µF, 16V rated)
        # Place close to OUT pins for output stability
        self.c_out = Capacitor(
            capacitance=4.7e-6,
            rated_voltage=16.0,
        ).insert(self.bq.OUT0, self.gnd, short_trace=True)

        # Battery bypass capacitor (4.7µF, 16V rated)
        # Place close to BAT pins for battery connection stability
        self.c_bat = Capacitor(
            capacitance=4.7e-6,
            rated_voltage=16.0,
        ).insert(self.bq.BAT0, self.gnd, short_trace=True)

        # Charge indicator LED (red, 0603)
        # Turns on when battery is charging
        self.charge_led = KT_0603R()

        # Power good indicator LED (green, 0603)
        # Turns on when input power is good
        self.good_power_led = KT_0603G()

        # LED ballast resistors
        # Limit current through status LEDs
        self.r_chg_led = Resistor(
            resistance=1.0e3,
            case="0603",
        ).insert(self.bq.CHG_NOT, self.charge_led.K, short_trace=True)

        self.r_gpw_led = Resistor(
            resistance=2.0e3,
            case="0603",
        ).insert(self.bq.PGOOD_NOT, self.good_power_led.K, short_trace=True)

        # CE pin pulldown resistor (33Ω)
        # Enable charging by pulling CE low
        self.r_pd_ce = Resistor(
            resistance=33.0,
            case="0603",
        ).insert(self.bq.CE_NOT, self.gnd, short_trace=True)

        # TS pin pulldown resistor (10kΩ)
        # Disable thermistor function (no temperature sensing)
        self.r_ts = Resistor(
            resistance=10.0e3,
            case="0603",
        ).insert(self.bq.TS, self.gnd, short_trace=True)

        # Current limit setting resistors
        # EN1=high, EN2=low sets USB current limit to 500mA
        self.r_pu_en1 = Resistor(
            resistance=33.0,
            case="0603",
        ).insert(self.bq.EN1, self.bat_plus, short_trace=True)

        self.r_pd_en2 = Resistor(
            resistance=33.0,
            case="0603",
        ).insert(self.bq.EN2, self.gnd, short_trace=True)

        # Current limit resistor (1.1kΩ)
        # Sets the maximum input current limit
        self.r_ilim = Resistor(
            resistance=1.1e3,
            case="0603",
        ).insert(self.bq.ILIM, self.gnd, short_trace=True)

        # Charge current setting resistor (2.7kΩ)
        # Formula: I_CHG = 890V / R_ISET
        # 890V / 2700Ω = 330mA (approximately 325mA target)
        self.r_chg = Resistor(
            resistance=2700.0,
            case="0603",
        ).insert(self.bq.ISET, self.gnd, short_trace=True)

        # Net connections
        self.nets = [
            # Power connections
            self.bq.OUT0 + self.bq.OUT1 + self.vout,
            self.bq.BAT0 + self.bq.BAT1 + self.bat_plus,
            self.bq.VSS + self.bq.EP + self.gnd,  # EP (exposed pad) to GND
            self.bq.IN + self.vin,
            self.bq.SYSOFF + self.gnd,  # SYSOFF low for normal operation
            # LED connections
            self.charge_led.A + self.vout,
            self.good_power_led.A + self.vout,
        ]


Device: type[BQ24078RGTR] = BQ24078RGTR

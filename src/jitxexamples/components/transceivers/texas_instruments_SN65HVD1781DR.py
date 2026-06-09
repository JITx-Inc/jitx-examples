"""
Texas Instruments SN65HVD1781DR RS-485 Transceiver

Component definition for Texas Instruments SN65HVD1781DR 3.3V RS-485 transceiver
with reference circuit implementation including bypass capacitors, pull-up resistors,
and TVS protection.
"""

from jitx.anchor import Anchor
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.component import Component
from jitx.circuit import Circuit
from jitx.common import Power, GPIO
from jitx.net import Net
from jitxlib.parts import Capacitor, Resistor
from jitxlib.protocols.serial import UART

from ..diodes_tvs.littelfuse_SMBJ43CA import SMBJ43CA


class CapsuleSmdPad(Pad):
    shape = rectangle(0.588, 2.045)
    solder_mask = [Soldermask(rectangle(0.69, 2.147))]
    paste = [Paste(rectangle(0.69, 2.147))]


class LandpatternSOIC_8_L4_9_W3_9_P1_27_LS6_0_BL(Landpattern):
    name = "SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL"
    p = {
        1: CapsuleSmdPad().at((-1.905, -2.7725)),
        2: CapsuleSmdPad().at((-0.635, -2.7725)),
        3: CapsuleSmdPad().at((0.635, -2.7725)),
        4: CapsuleSmdPad().at((1.905, -2.7725)),
        5: CapsuleSmdPad().at((1.905, 2.7725)),
        6: CapsuleSmdPad().at((0.635, 2.7725)),
        7: CapsuleSmdPad().at((-0.635, 2.7725)),
        8: CapsuleSmdPad().at((-1.905, 2.7725)),
    }
    pcb_layer_reference = Silkscreen(Text(">REF", 0.5, Anchor.W).at((-0.75, 5.5516)))
    pcb_layer_value = Custom(
        Text(">VALUE", 0.5, Anchor.W).at((-0.75, 4.5516)), name="Fab"
    )
    silkscreen = [
        Silkscreen(
            Polyline(
                0.152,
                [
                    (-2.526, -1.5215),
                    (-2.526, 1.5215),
                    (2.526, 1.5215),
                    (2.526, -1.5215),
                    (-2.526, -1.5215),
                ],
            )
        ),
        Silkscreen(ArcPolyline(0.3, [Arc((-1.905, -0.7695), 0.15, 0, -360)])),
        Silkscreen(ArcPolyline(0.3, [Arc((-2.651, -2.7725), 0.15, 0, -360)])),
    ]
    custom_layer = [
        Custom(ArcPolyline(0.3, [Arc((-1.905, -3.4005), 0.15, 0, -360)]), name="Fab"),
        Custom(ArcPolyline(0.06, [Arc((-2.45, -3.0005), 0.03, 0, -360)]), name="Fab"),
    ]
    courtyard = [Courtyard(rectangle(5.204, 7.692))]
    model3ds = [
        Model3D(
            "texas_instruments_SN65HVD1781DR.stp",
            position=(0.0, 0.0, 0.0),
            scale=(1.0, 1.0, 1.0),
            rotation=(0.0, 0.0, 0.0),
        )
    ]


class SymbolSN65HVD1781DR(Symbol):
    pin_name_size = 0.7874
    pad_name_size = 0.7874
    R = Pin((-6, 3), 2, Direction.Left)
    RE_NOT = Pin((-6, 1), 2, Direction.Left)
    DE = Pin((-6, -1), 2, Direction.Left)
    D = Pin((-6, -3), 2, Direction.Left)
    GND = Pin((6, -3), 2, Direction.Right)
    A = Pin((6, -1), 2, Direction.Right)
    B = Pin((6, 1), 2, Direction.Right)
    VCC = Pin((6, 3), 2, Direction.Right)
    layer_reference = Text(">REF", 0.55559, Anchor.C).at((0, 6.27481))
    layer_value = Text(">VALUE", 0.55559, Anchor.C).at((0, 5.48741))
    draws = [
        rectangle(12.00002, 10.80002),
        Circle(radius=0.3).at((-5.00001, 4.40001)),
        Circle(radius=0.3).at((-5.00001, 4.40001)),
    ]


class SN65HVD1781DR(Component):
    """
    Texas Instruments SN65HVD1781DR 3.3V RS-485 transceiver
    3.3V RS-485 transceiver with standby mode and thermal shutdown protection
    """

    name = "C42737"
    manufacturer = "Texas Instruments"
    mpn = "SN65HVD1781DR"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Texas-Instruments-SN65HVD1781DR_C42737.pdf"
    reference_designator_prefix = "U"

    R = Port()
    """Receiver output pin"""
    RE_NOT = Port()
    """Receiver enable (active low)"""
    DE = Port()
    """Driver enable"""
    D = Port()
    """Driver input"""
    GND = Port()
    """Ground"""
    A = Port()
    """RS-485 A line (non-inverting)"""
    B = Port()
    """RS-485 B line (inverting)"""
    VCC = Port()
    """Supply voltage (3.3V)"""
    landpattern = LandpatternSOIC_8_L4_9_W3_9_P1_27_LS6_0_BL()
    symbol = SymbolSN65HVD1781DR()
    cmappings = [
        SymbolMapping(
            {
                R: symbol.R,
                RE_NOT: symbol.RE_NOT,
                DE: symbol.DE,
                D: symbol.D,
                GND: symbol.GND,
                A: symbol.A,
                B: symbol.B,
                VCC: symbol.VCC,
            }
        ),
        PadMapping(
            {
                R: landpattern.p[1],
                RE_NOT: landpattern.p[2],
                DE: landpattern.p[3],
                D: landpattern.p[4],
                GND: landpattern.p[5],
                A: landpattern.p[6],
                B: landpattern.p[7],
                VCC: landpattern.p[8],
            }
        ),
    ]


class SN65HVD1781DRReferenceCircuit(Circuit):
    """
    SN65HVD1781DR RS-485 transceiver reference circuit with typical application components.

    Based on Texas Instruments reference design, this circuit includes:
    - 3.3V power supply with 100nF bypass capacitor
    - 10kΩ pull-up resistors on RE and DE pins for normal operation
    - 10Ω series resistors on RS-485 A/B lines for impedance matching
    - TVS diodes for RS-485 bus protection
    - UART interface bundle for clean MCU connection
    - Proper grounding and power distribution
    """

    # Power and ground
    power = Power()
    """3.3V power supply"""

    # UART/MCU interface
    uart = UART()
    """UART interface for MCU communication"""
    dir_pin = GPIO()
    """Direction control (optional, can be tied to DE)"""

    # RS-485 bus interface
    rs485_a = Net(name="RS485_A")
    """RS-485 A line (non-inverting)"""
    rs485_b = Net(name="RS485_B")
    """RS-485 B line (inverting)"""

    def __init__(self):
        # Main RS-485 transceiver IC
        self.transceiver = SN65HVD1781DR()

        # Power supply bypass capacitor (100nF)
        self.bypass_cap = Capacitor(
            capacitance=100e-9, temperature_coefficient_code="X7R"
        ).insert(self.transceiver.VCC, self.transceiver.GND, short_trace=True)

        # Pull-up resistors for RE and DE pins (10kΩ each)
        self.re_pullup = Resistor(resistance=10e3).insert(
            self.transceiver.VCC, self.transceiver.RE_NOT
        )
        self.de_pullup = Resistor(resistance=10e3).insert(
            self.transceiver.VCC, self.transceiver.DE
        )

        # Series resistors for RS-485 bus (10Ω each for impedance matching)
        self.rs485a_series = Resistor(resistance=10.0).insert(
            self.transceiver.A, self.rs485_a
        )
        self.rs485b_series = Resistor(resistance=10.0).insert(
            self.transceiver.B, self.rs485_b
        )

        # TVS diodes for RS-485 bus protection (using SMBJ43CA as shown in schematic)

        self.tvs_rs485a = SMBJ43CA()
        self.tvs_rs485b = SMBJ43CA()

        # Connect power and ground
        assert self.uart.rx and self.uart.tx
        self.nets = [
            self.power.Vp + self.transceiver.VCC,
            self.power.Vn + self.transceiver.GND,
            # UART interface connections
            self.uart.rx + self.transceiver.R,
            self.uart.tx + self.transceiver.D,
            self.dir_pin.gpio + self.transceiver.DE,
            # RS-485 bus connections with TVS protection (after series resistors)
            self.rs485_a + self.tvs_rs485a.A,
            self.rs485_b + self.tvs_rs485b.A,
            # TVS diode cathodes to ground
            self.power.Vn + self.tvs_rs485a.K + self.tvs_rs485b.K,
        ]


Device: type[SN65HVD1781DRReferenceCircuit] = SN65HVD1781DRReferenceCircuit

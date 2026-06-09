from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.circuit import Circuit
from jitx.landpattern import Landpattern, Pad
from jitx.layerindex import Side
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Polyline, Text
from jitx.feature import Finish, Paste, Silkscreen, Soldermask
from jitxlib.protocols.serial import I2C
from jitxlib.symbols.box import BoxSymbol, Row, PinGroup
from jitx.si import Toleranced
from jitx.property import Property
from dataclasses import dataclass
from jitxlib.parts.query_api import Capacitor
from jitx.common import Power


class RectSMDPad1(Pad):
    rect = rectangle(0.5, 0.650013)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class RectSMDPad2(Pad):
    rect = rectangle(0.550013, 0.550013)
    shape = rect
    layer = Paste(rect)
    layer = Soldermask(rect)


class OPTO_SMD_12P_VL53L0CXV0DH_1(Landpattern):
    p = {
        1: RectSMDPad1().at(1.599949, -0.875032, on=Side.Top),
        2: RectSMDPad1().at(0.800102, -0.875032, on=Side.Top),
        3: RectSMDPad1().at(0.0, -0.875032, on=Side.Top),
        4: RectSMDPad1().at(-0.800102, -0.875032, on=Side.Top),
        5: RectSMDPad1().at(-1.599949, -0.875032, on=Side.Top),
        6: RectSMDPad2().at(-1.599949, 0.0, on=Side.Top),
        7: RectSMDPad1().at(-1.599949, 0.875032, on=Side.Top),
        8: RectSMDPad1().at(-0.800102, 0.875032, on=Side.Top),
        9: RectSMDPad1().at(0.0, 0.875032, on=Side.Top),
        10: RectSMDPad1().at(0.800102, 0.875032, on=Side.Top),
        11: RectSMDPad1().at(1.599949, 0.875032, on=Side.Top),
        12: RectSMDPad2().at(1.599949, 0.0, on=Side.Top),
    }

    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, 3.2762))
    value_text = Finish(Text(">VALUE", 1.0, Anchor.C).at(0.0, -3.2762))
    ref_alt_text = Finish(Text("REF**", 1.0, Anchor.C).at(0.0, -5.2762))

    silk_lines = [
        Silkscreen(Polyline(0.1524, [(-2.2762, -1.2762), (-2.014503, -1.2762)])),
        Silkscreen(Polyline(0.1524, [(2.2762, -0.414503), (2.2762, -1.2762)])),
        Silkscreen(Polyline(0.1524, [(-2.2762, 1.2762), (-2.014503, 1.2762)])),
        Silkscreen(Polyline(0.1524, [(2.2762, 1.2762), (2.014503, 1.2762)])),
        Silkscreen(Polyline(0.1524, [(-2.2762, 0.414503), (-2.2762, 1.2762)])),
        Silkscreen(Polyline(0.1524, [(2.2762, -1.2762), (2.014503, -1.2762)])),
        Silkscreen(Polyline(0.1524, [(2.2762, 0.414503), (2.2762, 1.2762)])),
        Silkscreen(Polyline(0.1524, [(-2.2762, -0.414503), (-2.2762, -1.2762)])),
    ]

    silk_arcs = [
        Silkscreen(ArcPolyline(0.250013, [Arc((0.949962, 0.0), 0.124968, 0.0, 360.0)])),
        Silkscreen(
            ArcPolyline(
                0.059995, [Arc((2.199898, -1.199898), 0.0299719999999999, 0.0, 360.0)]
            )
        ),
        Silkscreen(
            ArcPolyline(0.250013, [Arc((1.649987, -1.599949), 0.124969, 0.0, 360.0)])
        ),
        Silkscreen(
            ArcPolyline(
                0.150013, [Arc((-0.949962, 0.0), 0.0749299999999999, 0.0, 360.0)]
            )
        ),
    ]

    finish_arcs = [
        Finish(
            ArcPolyline(
                0.150013, [Arc((-0.949962, 0.0), 0.0749299999999999, 0.0, 360.0)]
            )
        ),
        Finish(ArcPolyline(0.250013, [Arc((0.949962, 0.0), 0.124968, 0.0, 360.0)])),
    ]

    # model = Model3D(
    #     "../../3d-models/OPTO-SMD_12P_VL53L0CXV0DH-1.wrl",
    #     position=(0, 0, 0),
    #     scale=(1, 1, 1),
    #     rotation=(0, 0, -90)
    # )


class VL53L0CXV0DH_1_Component(Component):
    """VL53L0CXV0DH_1 Time Of Flight Distance Sensor"""

    reference_designator_prefix = "U"

    # Time-of-flight sensor pins
    VDD = Port()  # Digital power supply
    AVDD = Port()  # Analog power supply
    SCL = Port()  # I2C clock
    GND = Port()  # Ground (multiple pins)
    SHT = Port()  # Shutdown pin
    GP1 = Port()  # GPIO pin 1
    DNC = Port()  # Do not connect
    SDA = Port()  # I2C data

    landpattern = OPTO_SMD_12P_VL53L0CXV0DH_1()
    symbol = BoxSymbol(
        rows=[
            Row(left=[PinGroup([VDD, GND, SHT])]),
            Row(right=[PinGroup([AVDD, SCL, GP1, DNC, SDA])]),
        ]
    )

    # Pin mappings based on the pin-properties from the original Stanza file
    mappings = [
        PadMapping(
            {
                VDD: [landpattern.p[1]],  # Digital power to pad 1
                AVDD: [landpattern.p[11]],  # Analog power to pad 11
                SCL: [landpattern.p[10]],  # I2C clock to pad 10
                GND: [
                    landpattern.p[2],
                    landpattern.p[3],
                    landpattern.p[4],
                    landpattern.p[12],
                    landpattern.p[6],
                ],  # Ground to multiple pads
                SHT: [landpattern.p[5]],  # Shutdown to pad 5
                GP1: [landpattern.p[7]],  # GPIO1 to pad 7
                DNC: [landpattern.p[8]],  # Do not connect to pad 8
                SDA: [landpattern.p[9]],  # I2C data to pad 9
            }
        ),
    ]

    # Electrical properties
    @dataclass
    class PowerPin(Property):
        voltage_range: Toleranced

    # Power pin properties
    VDD_power_pin = PowerPin(voltage_range=Toleranced.min_max(2.6, 3.5))
    AVDD_power_pin = PowerPin(voltage_range=Toleranced.min_max(2.6, 3.5))

    # Component properties
    lcsc = "C91199"
    datasheet = "https://item.szlcsc.com/92388.html"


class VL53L0CXV0DH_1(Circuit):
    """
    VL53L0CXV0DH_1 Module
    Time-of-flight sensor module with bypass capacitors and I2C interface
    """

    power = Power()  # Power supply port
    i2c = I2C()  # I2C communication port (Address: 0x52)
    x_shut = Port()  # Shutdown control pin
    gpio1 = Port()  # GPIO1 pin

    # VL53L0CXV0DH1 time-of-flight sensor from STMicroelectronics
    tof = VL53L0CXV0DH_1_Component()

    # Bypass capacitors
    vdd_bypass = Capacitor(
        # description="VDD bypass capacitor",
        capacitance=4.7e-6,  # 4.7µF
        case="0603",
    )

    avdd_bypass = Capacitor(
        # description="AVDD bypass capacitor",
        capacitance=0.1e-6,  # 0.1µF
        case="0603",
    )

    # Circuit connections
    nets = [
        # I2C connections
        i2c.sda + tof.SDA,  # I2C data
        i2c.scl + tof.SCL,  # I2C clock
        # Control pin connections
        x_shut + tof.SHT,  # Shutdown control
        gpio1 + tof.GP1,  # GPIO1
        # Power connections
        power.Vp + tof.AVDD + tof.VDD,  # Power supply
        power.Vn + tof.GND + tof.GND,  # Ground
        # Bypass capacitor connections
        tof.VDD + vdd_bypass.p1,  # VDD bypass
        tof.GND + vdd_bypass.p2,  # VDD bypass ground
        tof.AVDD + avdd_bypass.p1,  # AVDD bypass
        tof.GND + avdd_bypass.p2,  # AVDD bypass ground
    ]

    def __init__(self):
        super().__init__()
        # Group components for schematic and layout
        self.schematic_group = "Vl53L0"
        self.layout_group = "Vl53L0"

    def get_components(self):
        """
        Return list of components for grouping
        """
        return [self.tof, self.vdd_bypass, self.avdd_bypass]


Device: type[VL53L0CXV0DH_1] = VL53L0CXV0DH_1

"""
LIS3DHTR
"""

from jitx import Component
from jitx.circuit import Circuit, SchematicGroup
from jitx.common import Power
from jitx.container import inline
from jitx.feature import Courtyard, Silkscreen
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Anchor, Circle, Text
from jitx.units import F
from jitxlib.parts import Capacitor
from jitxlib.protocols.serial import I2C, SPI
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row


class RectanglePad(Pad):
    shape = rectangle(0.45, 0.35)


class LIS3DHTR(Circuit):
    @inline
    class acc(Component):
        """X,Y,Z LGA-16(3x3)  Attitude Sensor/Gyroscope ROHS"""

        manufacturer = "STMICROELECTRONICS"
        mpn = "LIS3DHTR"
        datasheet = "https://datasheet.lcsc.com/lcsc/1811031937_STMicroelectronics-LIS3DHTR_C15134.pdf"
        reference_designator_prefix = "U"

        VDD_IO = Port()
        NC = {
            0: Port(),
            1: Port(),
        }
        SPC = Port()
        GND = Port()
        SDA_SDI = Port()  # I2C SDA, SPI SDI (pin 6)
        SDO_SA0 = Port()  # SPI SDO, I2C SA0 (pin 7)
        CS = Port()
        INT = {
            1: Port(),
            2: Port(),
        }
        RES = Port()
        ADC = {
            1: Port(),
            2: Port(),
            3: Port(),
        }
        VDD = Port()

        @inline
        class landpattern(Landpattern):
            p = {
                1: RectanglePad().at(-1.225, 1),
                2: RectanglePad().at(-1.225, 0.5),
                3: RectanglePad().at(-1.225, 0),
                4: RectanglePad().at(-1.225, -0.5),
                5: RectanglePad().at(-1.225, -1),
                6: RectanglePad().at(-0.5, -1.225, rotate=90),
                7: RectanglePad().at(0, -1.225, rotate=90),
                8: RectanglePad().at(0.5, -1.225, rotate=90),
                9: RectanglePad().at(1.225, -1),
                10: RectanglePad().at(1.225, -0.5),
                11: RectanglePad().at(1.225, 0),
                12: RectanglePad().at(1.225, 0.5),
                13: RectanglePad().at(1.225, 1),
                14: RectanglePad().at(0.5, 1.225, rotate=90),
                15: RectanglePad().at(0, 1.225, rotate=90),
                16: RectanglePad().at(-0.5, 1.225, rotate=90),
            }
            courtyard = Courtyard(rectangle(3, 3))
            silkscreen = Silkscreen(Circle(radius=0.1).at(-2, 1.275))
            ref = Text(">REF", 1, Anchor.C)

        mappings = [
            PadMapping(
                {
                    VDD_IO: landpattern.p[1],
                    NC[0]: landpattern.p[2],
                    NC[1]: landpattern.p[3],
                    SPC: landpattern.p[4],
                    GND: [landpattern.p[5], landpattern.p[12]],
                    SDA_SDI: landpattern.p[6],
                    SDO_SA0: landpattern.p[7],
                    CS: landpattern.p[8],
                    INT[2]: landpattern.p[9],
                    RES: landpattern.p[10],
                    INT[1]: landpattern.p[11],
                    ADC[3]: landpattern.p[13],
                    VDD: landpattern.p[14],
                    ADC[2]: landpattern.p[15],
                    ADC[1]: landpattern.p[16],
                }
            )
        ]

        box = BoxSymbol(
            rows=[
                Row(
                    right=PinGroup(INT[2], RES, INT[1], ADC[3], VDD, ADC[2], ADC[1]),
                    left=PinGroup(SPC, SDA_SDI, SDO_SA0, CS),
                )
            ],
            columns=[
                Column(up=PinGroup(VDD_IO), down=PinGroup(NC[0], NC[1], GND)),
            ],
        )

        NC[0].no_connect()
        NC[1].no_connect()

    power = Power()
    i2c = I2C()
    spi = SPI(cs=True)
    adc = Port(), Port(), Port()
    int = Port(), Port()
    vio = Port()

    def __init__(self) -> None:
        # STMicroelectronics, "LIS3DH", datasheet DocID17530 Rev 2, December
        # 2016, Section 4 and Figure 5: 100 nF ceramic and 10 uF on Vdd (pin 14).
        self.vdd_bypass = Capacitor(capacitance=(10e-6) * F)
        self.vdd_bypass_100n = Capacitor(capacitance=(0.1e-6) * F)
        self.vdd_io_bypass = Capacitor(capacitance=(0.1e-6) * F)

        # promise pyright that we have the right ports
        assert self.spi.copi and self.spi.cipo and self.spi.cs

        self.VDD = (
            self.power.Vp + self.acc.VDD + self.vdd_bypass.p1 + self.vdd_bypass_100n.p1
        )
        self.GND = (
            self.power.Vn
            + self.acc.GND
            + self.acc.RES
            + self.vdd_bypass.p2
            + self.vdd_bypass_100n.p2
            + self.vdd_io_bypass.p2
        )
        self.VDD_IO = self.vio + self.acc.VDD_IO + self.vdd_io_bypass.p1
        self.SCL_SPC = self.i2c.scl + self.spi.sck + self.acc.SPC
        # LIS3DH data sheet, Table 2: pin 6 is I2C SDA and SPI SDI (peripheral
        # in), pin 7 is SPI SDO (peripheral out) and I2C SA0.
        self.SDA_SDI = self.i2c.sda + self.spi.copi + self.acc.SDA_SDI
        self.SDO_SA0 = self.spi.cipo + self.acc.SDO_SA0
        self.CS = self.spi.cs + self.acc.CS
        self.ADC1 = self.adc[0] + self.acc.ADC[1]
        self.ADC2 = self.adc[1] + self.acc.ADC[2]
        self.ADC3 = self.adc[2] + self.acc.ADC[3]
        self.INT1 = self.int[0] + self.acc.INT[1]
        self.INT2 = self.int[1] + self.acc.INT[2]

        self.lis3dh = SchematicGroup()


# Device alias for easy import following JITX patterns
Device: type[LIS3DHTR] = LIS3DHTR

from jitx import Component
from jitx.circuit import Circuit, SchematicGroup
from jitx.common import Power
from jitx.container import inline
from jitx.feature import Courtyard, Silkscreen
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Anchor, Circle, Text

from jitxlib.parts.query_api import Capacitor
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
        SDO = Port()
        SA0 = Port()
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
                    SDO: landpattern.p[6],
                    SA0: landpattern.p[7],
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
                    left=PinGroup(SPC, SDO, SA0, CS),
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

    def __init__(self):
        self.bypasses = [
            Capacitor(capacitance=10e-6).insert(self.acc.VDD, self.acc.GND),
            Capacitor(capacitance=0.1e-6).insert(self.acc.VDD_IO, self.acc.GND),
        ]

        # promise pyright that we have the right ports
        assert self.spi.copi and self.spi.cipo and self.spi.cs

        # unnamed nets
        self.nets = [
            self.power.Vp + self.acc.VDD,
            self.power.Vn + self.acc.GND + self.acc.RES,
            self.vio + self.acc.VDD_IO,
            self.i2c.scl + self.spi.sck + self.acc.SPC,
            self.i2c.sda + self.spi.cipo + self.acc.SDO,
            self.spi.copi + self.acc.SA0,
            self.spi.cs + self.acc.CS,
            *(a + b for a, b in zip(self.adc, self.acc.ADC.values(), strict=False)),
            *(a + b for a, b in zip(self.int, self.acc.INT.values(), strict=False)),
        ]

        self.lis3dh = SchematicGroup()


# Device alias for easy import following JITX patterns
Device: type[LIS3DHTR] = LIS3DHTR

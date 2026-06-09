from collections.abc import Sequence
from itertools import chain
from jitx import Landpattern
from jitx.anchor import Anchor
from jitx.circuit import Circuit, SchematicGroup
from jitx.common import ADC, GPIO, Power, Timer
from jitx.component import Component
from jitx.container import inline
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.interval import Interval
from jitx.landpattern import Pad, PadMapping
from jitx.net import Net, Port, provide
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polygon, Polyline, Text

from jitxlib.parts import Inductor, Capacitor
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row
from jitxlib.protocols.serial import I2C, SPI, UART, SWD
from jitxlib.protocols.usb import USB2Connector

from jitxexamples.components.transistors.seiko_epson_TSX_3225_32_0000MF10Z_W6 import (
    TSX_3225_32_0000MF10Z_W6,
)


# TODO: Not sure about these dimensions
class SMDPad(Pad):
    shape = rectangle(4.85, 4.85)
    soldermask = Soldermask(rectangle(4.952, 4.952))
    paste = Paste(rectangle(4.952, 4.952))


class nRFBGAPad(Pad):
    shape = Circle(diameter=0.275)
    soldermask = Soldermask(Circle(diameter=0.375))
    paste = Paste(Circle(diameter=0.3))


class Reset(Port):
    reset = Port()


class LFOscillator(Port):
    lo_in = Port()
    lo_out = Port()


class NRF52840_QIAA_R(Circuit):
    """
    NRF52840 reference module.

    Args:
        lfo: include a 32.768kHz resonator in the design
        antenna: include an antenna and matching circuit in the design
        power_config: circuit configuration from
            https://infocenter.nordicsemi.com/index.jsp?topic=%2Fps_nrf52840%2Fref_circuitry.html
            (currently supports 5 and 6)
    """

    vin = Power()

    @inline
    class mcu(Component):
        """AQFN-73-EP(7x7) Advanced Bluetooth 5, Thread and Zigbee multiprotocol SoC"""

        name = "XCVR_NRF52840-QIAA-R"
        mpn = "NRF52840-QIAA-R"
        manufacturer = "Nordic Semiconductor"
        datasheet = "https://datasheet.lcsc.com/lcsc/2304140030_Nordic-Semicon-NRF52840-QIAA-R_C190794.pdf"
        P0 = [Port() for _ in range(32)]
        P1 = [Port() for _ in range(16)]
        Dn = Port()
        Dp = Port()
        SWDCLK = Port()
        SWDIO = Port()
        XC1 = Port()
        XC2 = Port()
        ANT = Port()
        VBUS = Port()
        VDD = [Port() for _ in range(5)]
        VDDH = Port()
        VSS = Port()
        VSS_PA = Port()
        DCC = Port()
        DCCH = Port()
        DEC1 = Port()
        DEC2 = Port()
        DEC3 = Port()
        DEC4 = Port()
        DEC5 = Port()
        DEC6 = Port()
        DECUSB = Port()

        @inline
        class landpattern(Landpattern):
            A10 = nRFBGAPad().at(-3.25, -0.75)
            A12 = nRFBGAPad().at(-3.25, -0.25)
            A14 = nRFBGAPad().at(-3.25, 0.25)
            A16 = nRFBGAPad().at(-3.25, 0.75)
            A18 = nRFBGAPad().at(-3.25, 1.25)
            A20 = nRFBGAPad().at(-3.25, 1.75)
            A22 = nRFBGAPad().at(-3.25, 2.25)
            A23 = nRFBGAPad().at(-3.25, 2.75)
            A8 = nRFBGAPad().at(-3.25, -1.25)
            AA24 = nRFBGAPad().at(2.25, 3.25)
            AB2 = nRFBGAPad().at(2.5, -2.75)
            AC11 = nRFBGAPad().at(2.75, -0.5)
            AC13 = nRFBGAPad().at(2.75, 0)
            AC15 = nRFBGAPad().at(2.75, 0.5)
            AC17 = nRFBGAPad().at(2.75, 1)
            AC19 = nRFBGAPad().at(2.75, 1.5)
            AC21 = nRFBGAPad().at(2.75, 2)
            AC24 = nRFBGAPad().at(2.75, 3.25)
            AC5 = nRFBGAPad().at(2.75, -2)
            AC9 = nRFBGAPad().at(2.75, -1)
            AD10 = nRFBGAPad().at(3.25, -0.75)
            AD12 = nRFBGAPad().at(3.25, -0.25)
            AD14 = nRFBGAPad().at(3.25, 0.25)
            AD16 = nRFBGAPad().at(3.25, 0.75)
            AD18 = nRFBGAPad().at(3.25, 1.25)
            AD20 = nRFBGAPad().at(3.25, 1.75)
            AD22 = nRFBGAPad().at(3.25, 2.25)
            AD23 = nRFBGAPad().at(3.25, 2.75)
            AD2 = nRFBGAPad().at(3.25, -2.75)
            AD4 = nRFBGAPad().at(3.25, -2.25)
            AD6 = nRFBGAPad().at(3.25, -1.75)
            AD8 = nRFBGAPad().at(3.25, -1.25)
            B11 = nRFBGAPad().at(-2.75, -0.5)
            B13 = nRFBGAPad().at(-2.75, 0)
            B15 = nRFBGAPad().at(-2.75, 0.5)
            B17 = nRFBGAPad().at(-2.75, 1)
            B19 = nRFBGAPad().at(-2.75, 1.5)
            B1 = nRFBGAPad().at(-2.75, -3.25)
            B24 = nRFBGAPad().at(-2.75, 3.25)
            B3 = nRFBGAPad().at(-2.75, -2.5)
            B5 = nRFBGAPad().at(-2.75, -2)
            B7 = nRFBGAPad().at(-2.75, -1.5)
            B9 = nRFBGAPad().at(-2.75, -1)
            C1 = nRFBGAPad().at(-2.25, -3.25)
            D23 = nRFBGAPad().at(-2, 2.75)
            D2 = nRFBGAPad().at(-2, -2.75)
            E24 = nRFBGAPad().at(-1.75, 3.25)
            F23 = nRFBGAPad().at(-1.5, 2.75)
            F2 = nRFBGAPad().at(-1.5, -2.75)
            G1 = nRFBGAPad().at(-1.25, -3.25)
            H23 = nRFBGAPad().at(-1, 2.75)
            H2 = nRFBGAPad().at(-1, -2.75)
            J1 = nRFBGAPad().at(-0.75, -3.25)
            J24 = nRFBGAPad().at(-0.75, 3.25)
            K2 = nRFBGAPad().at(-0.5, -2.75)
            L1 = nRFBGAPad().at(-0.25, -3.25)
            L24 = nRFBGAPad().at(-0.25, 3.25)
            M2 = nRFBGAPad().at(0, -2.75)
            N1 = nRFBGAPad().at(0.25, -3.25)
            N24 = nRFBGAPad().at(0.25, 3.25)
            P23 = nRFBGAPad().at(0.5, 2.75)
            P2 = nRFBGAPad().at(0.5, -2.75)
            R1 = nRFBGAPad().at(0.75, -3.25)
            R24 = nRFBGAPad().at(0.75, 3.25)
            T23 = nRFBGAPad().at(1, 2.75)
            T2 = nRFBGAPad().at(1, -2.75)
            U1 = nRFBGAPad().at(1.25, -3.25)
            U24 = nRFBGAPad().at(1.25, 3.25)
            V23 = nRFBGAPad().at(1.5, 2.75)
            W1 = nRFBGAPad().at(1.75, -3.25)
            W24 = nRFBGAPad().at(1.75, 3.25)
            Y23 = nRFBGAPad().at(2, 2.75)
            Y2 = nRFBGAPad().at(2, -2.75)
            p = {74: SMDPad().at(0, 0)}

            labels = [
                Silkscreen(Text(">REF", 0.5, Anchor.W).at(-0.75, 5.332)),
                Custom(Text(">VALUE", 0.5, Anchor.W).at(-0.75, 4.332), name="Fab"),
            ]
            silkscreen = [
                Silkscreen(shape)
                for shape in (
                    Polyline(0.152, [(-3.5, -3.05), (-3, -3.55), (-2.991, -3.55)]),
                    Polyline(
                        0.152,
                        [
                            (3.55, -3.55),
                            (3.55, 3.55),
                            (-3.55, 3.55),
                            (-3.55, -3.55),
                            (3.55, -3.55),
                        ],
                    ),
                    ArcPolyline(0.2, [Arc((-3.35, -3.85), 0.1, 0, -360)]),
                    Polygon(
                        [
                            (-3.55, -2.8),
                            (-3.55, -3.55),
                            (-2.8, -3.55),
                            (-3.55, -2.8),
                        ]
                    ),
                    Polygon(
                        [
                            (-3.55, -3.55),
                            (-3.55, -3),
                            (-3, -3.55),
                            (-3.55, -3.55),
                            (-3.55, -3.55),
                        ]
                    ),
                )
            ]
            fab_drawing = [
                Custom(shape, name="Fab")
                for shape in (
                    ArcPolyline(0.06, [Arc((-3.5, -3.5), 0.03, 0, -360)]),
                    ArcPolyline(0.2, [Arc((-3.35, -3.85), 0.1, 0, -360)]),
                )
            ]
            courtyard = Courtyard(rectangle(7.252, 7.252))

        padmapping = PadMapping(
            {
                P0[0]: landpattern.D2,
                P0[1]: landpattern.F2,
                P0[2]: landpattern.A12,
                P0[3]: landpattern.B13,
                P0[4]: landpattern.J1,
                P0[5]: landpattern.K2,
                P0[6]: landpattern.L1,
                P0[7]: landpattern.M2,
                P0[8]: landpattern.N1,
                P0[9]: landpattern.L24,
                P0[10]: landpattern.J24,
                P0[11]: landpattern.T2,
                P0[12]: landpattern.U1,
                P0[13]: landpattern.AD8,
                P0[14]: landpattern.AC9,
                P0[15]: landpattern.AD10,
                P0[16]: landpattern.AC11,
                P0[17]: landpattern.AD12,
                P0[18]: landpattern.AC13,
                P0[19]: landpattern.AC15,
                P0[20]: landpattern.AD16,
                P0[21]: landpattern.AC17,
                P0[22]: landpattern.AD18,
                P0[23]: landpattern.AC19,
                P0[24]: landpattern.AD20,
                P0[25]: landpattern.AC21,
                P0[26]: landpattern.G1,
                P0[27]: landpattern.H2,
                P0[28]: landpattern.B11,
                P0[29]: landpattern.A10,
                P0[30]: landpattern.B9,
                P0[31]: landpattern.A8,
                P1[0]: landpattern.AD22,
                P1[1]: landpattern.Y23,
                P1[2]: landpattern.W24,
                P1[3]: landpattern.V23,
                P1[4]: landpattern.U24,
                P1[5]: landpattern.T23,
                P1[6]: landpattern.R24,
                P1[7]: landpattern.P23,
                P1[8]: landpattern.P2,
                P1[9]: landpattern.R1,
                P1[10]: landpattern.A20,
                P1[11]: landpattern.B19,
                P1[12]: landpattern.B17,
                P1[13]: landpattern.A16,
                P1[14]: landpattern.B15,
                P1[15]: landpattern.A14,
                Dn: landpattern.AD4,
                Dp: landpattern.AD6,
                SWDCLK: landpattern.AA24,
                SWDIO: landpattern.AC24,
                XC1: landpattern.B24,
                XC2: landpattern.A23,
                ANT: landpattern.H23,
                VBUS: landpattern.AD2,
                VDD[0]: landpattern.A22,
                VDD[1]: landpattern.AD14,
                VDD[2]: landpattern.AD23,
                VDD[3]: landpattern.B1,
                VDD[4]: landpattern.W1,
                VDDH: landpattern.Y2,
                VSS: [landpattern.p[74], landpattern.B7],
                VSS_PA: landpattern.F23,
                DCC: landpattern.B3,
                DCCH: landpattern.AB2,
                DEC1: landpattern.C1,
                DEC2: landpattern.A18,
                DEC3: landpattern.D23,
                DEC4: landpattern.B5,
                DEC5: landpattern.N24,
                DEC6: landpattern.E24,
                DECUSB: landpattern.AC5,
            }
        )

        symbols = [
            BoxSymbol(rows=Row(right=PinGroup(P1))),
            BoxSymbol(rows=Row(right=PinGroup(P0))),
            BoxSymbol(
                rows=Row(
                    right=PinGroup(
                        DCC, DCCH, DEC1, DEC2, DEC3, DEC4, DEC5, DEC6, DECUSB
                    ),
                    left=PinGroup(VBUS, *VDD, VDDH),
                ),
                columns=Column(down=PinGroup(VSS, VSS_PA)),
            ),
            BoxSymbol(
                rows=Row(
                    right=PinGroup(ANT), left=PinGroup(Dn, Dp, SWDCLK, SWDIO, XC1, XC2)
                )
            ),
        ]

    class IOPort(Port):
        p = Port()

    @provide(IOPort)
    def ioport(self, io: IOPort):
        return [{io.p: port} for port in chain(self.mcu.P0, self.mcu.P1)]

    @provide(GPIO)
    def gpio(self, gpio: GPIO):
        return [{gpio.gpio: self.require(self.IOPort).p} for _ in range(48)]

    @provide(Timer)
    def timer(self, timer: Timer):
        return [{timer.timer: self.require(self.IOPort).p} for _ in range(48)]

    @provide(ADC)
    def adc(self, adc: ADC):
        return [{adc.adc: self.mcu.P0[i]} for i in (2, 3, 4, 5, 28, 29, 30, 31)]

    @provide(I2C)
    def i2c(self, i2c: I2C):
        return [
            {
                i2c.scl: self.require(self.IOPort).p,
                i2c.sda: self.require(self.IOPort).p,
            }
            for _ in range(2)
        ]

    @provide(SPI(cs=True))
    def spi(self, spi: SPI):
        return [
            {
                spi.copi: self.require(self.IOPort).p,
                spi.cipo: self.require(self.IOPort).p,
                spi.sck: self.require(self.IOPort).p,
                spi.cs: self.require(self.IOPort).p,
            }
            for _ in range(3)
        ]

    @provide(UART(cts=True, rts=True))
    def uart(self, uart: UART):
        assert uart.cts and uart.rts
        return [
            {
                uart.tx: self.require(self.IOPort).p,
                uart.rx: self.require(self.IOPort).p,
                uart.cts: self.require(self.IOPort).p,
                uart.rts: self.require(self.IOPort).p,
            }
            for _ in range(2)
        ]

    @provide(SWD(swo=True))
    def swd(self, swd: SWD):
        assert swd.swo
        return [
            {
                swd.swdio: self.mcu.SWDIO,
                swd.swdclk: self.mcu.SWDCLK,
                swd.swo: self.mcu.P1[0],
            }
        ]

    @provide(Reset)
    def reset(self, reset: Reset):
        return [
            {
                reset.reset: self.mcu.P0[18],
            }
        ]

    @provide(LFOscillator)
    def crystal(self, crystal: LFOscillator):
        return [
            {
                crystal.lo_in: self.mcu.P0[0],
                crystal.lo_out: self.mcu.P0[1],
            }
        ]

    def __init__(self, *, lfo=True, antenna=True, power_config=5):
        mcu = self.mcu

        self.GND = self.vin.Vn + mcu.VSS + mcu.VSS_PA
        self.nets = []
        self.bypasses: Sequence[Capacitor] = []
        match power_config:
            case 5:
                self.usb = USB2Connector()
                self.GND += self.usb.vbus.Vn
                self.nets += [mcu.VBUS + self.usb.vbus.Vp]
                self.power_config = []
                for pin, cap in [
                    (mcu.DEC1, 100e-9),
                    (mcu.DEC3, 100e-9),
                    (mcu.DEC5, 820e-12),
                    (mcu.DECUSB, 4.7e-6),
                    (mcu.VBUS, 4.7e-6),
                    (mcu.DEC4, 1e-6),
                    (mcu.VDDH, 4.7e-6),
                    (mcu.VDD[0], 0.1e-6),
                    (mcu.VDD[1], 0.1e-6),
                    (mcu.VDD[2], 0.1e-6),
                    (mcu.VDD[3], 1e-6),
                    (mcu.VDD[4], 1e-6),
                ]:
                    self.bypasses.append(
                        Capacitor(capacitance=cap).insert(
                            pin, self.GND, short_trace=True
                        )
                    )

                self.pwr_ind = Inductor(
                    mounting="smd",
                    inductance=10e-6,
                    current_rating=Interval(50e-3),
                )
                self.filt_ind = Inductor(
                    mounting="smd",
                    inductance=15e-9,
                    self_resonant_frequency=2e9,
                    material_core="ceramic",
                )
                self.nets += [
                    mcu.DCCH + self.pwr_ind.p1,
                    self.pwr_ind.p2 + self.filt_ind.p1,
                    self.filt_ind.p2 + mcu.DEC4 + mcu.DEC6,
                ]
                self.nets.append(Net(mcu.VDD[0:4] + [mcu.VDDH, self.vin.Vp]))
            case 6:
                for pin, cap in [
                    (mcu.DEC1, 100e-9),
                    (mcu.DEC3, 100e-9),
                    # mcu.DEC5  820e-12, ; not required for Fxx and later
                    (mcu.DEC4, 1e-6),
                    (mcu.VDDH, 4.7e-6),
                    (mcu.VDD[0], 0.1e-6),
                    (mcu.VDD[1], 0.1e-6),
                    (mcu.VDD[2], 0.1e-6),
                    (mcu.VDD[3], 1e-6),
                ]:
                    self.bypasses.append(
                        Capacitor(capacitance=cap).insert(
                            pin, self.GND, short_trace=True
                        )
                    )

                mcu.DECUSB.no_connect()
                mcu.DEC5.no_connect()
                mcu.DCCH.no_connect()
                mcu.DCC.no_connect()

                dec6cap = Capacitor(capacitance=0.1e-6).insert(
                    mcu.DEC6, self.GND, short_trace=True
                )
                dec6cap.schematic_x_out = True
                dec6cap.soldered = False
                # TODO: Is it in bom?
                # dec6cap.in_bom = False
                self.bypasses.append(dec6cap)

                self.GND += mcu.VBUS
                self.nets += [mcu.DEC4 + mcu.DEC6, mcu.VDDH + self.vin.Vp]
                mcu.Dp.no_connect()
                mcu.Dn.no_connect()
                self.nets.append(Net(mcu.VDD[0:4] + [self.vin.Vp]))
            case _:
                raise ValueError(f"Invalid power config: {power_config}")

        self.bypasses.append(
            Capacitor(capacitance=0.1e-6).insert(mcu.DEC2, self.GND, short_trace=True)
        )

        self.hfosc = TSX_3225_32_0000MF10Z_W6()
        self.nets += [
            mcu.XC1 + self.hfosc.OSC1,
            mcu.XC2 + self.hfosc.OSC2,
        ]
        self.GND += self.hfosc.GND0 + self.hfosc.GND1
        self.hfosc.add_load_caps(self.GND)

        self.util = SchematicGroup(mcu.symbols[2])
        self.power = SchematicGroup(self.bypasses + [mcu.symbols[3]])
        self.NRF52840 = SchematicGroup()


Device: type[NRF52840_QIAA_R] = NRF52840_QIAA_R

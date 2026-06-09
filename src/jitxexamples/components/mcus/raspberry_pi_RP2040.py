"""
Raspberry Pi RP2040 Microcontroller

Component definition for the Raspberry Pi RP2040 dual-core ARM Cortex-M0+ microcontroller.
Includes symbol, component, and circuit definitions with complete peripheral support.
"""

from jitx import Circuit, PadMapping
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.net import Port, provide
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Polygon, Text
from jitx.si import Toleranced
from jitx.symbol import Direction, Pin, Symbol
from jitxlib.landpatterns.generators.qfn import QFN, QFNLead
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.leads import LeadProfile
from jitxlib.landpatterns.package import RectanglePackage
from jitx.common import ADC, GPIO as GPIO_Common, Power, Timer
from jitxlib.protocols.serial import I2C, SPI, UART
from jitxlib.protocols.usb import USB2
from jitxlib.parts import Capacitor, Resistor
from ..crystals.yangxing_tech_X322512MSB4SI import Device as X322512MSB4SI
from ..buttons.xunpu_TS_1088_AR02016 import Device as TactileSwitch
from ..flash.winbond_W25Q128JVSIQ import Device as W25Q128JVSIQ


class RP2040_Symbol(Symbol):
    """Schematic symbol for the RP2040 microcontroller"""

    pin_name_size = 0.58
    pad_name_size = 0.58

    # Power pins
    IOVDD5 = Pin(at=(3, 15), direction=Direction.Up, length=1)
    IOVDD4 = Pin(at=(2, 15), direction=Direction.Up, length=1)
    IOVDD3 = Pin(at=(1, 15), direction=Direction.Up, length=1)
    IOVDD2 = Pin(at=(0, 15), direction=Direction.Up, length=1)
    IOVDD1 = Pin(at=(-1, 15), direction=Direction.Up, length=1)
    IOVDD0 = Pin(at=(-2, 15), direction=Direction.Up, length=1)
    ADC_AVDD = Pin(at=(6, 15), direction=Direction.Up, length=1)
    VREG_IN = Pin(at=(-4, 15), direction=Direction.Up, length=1)
    VREG_VOUT = Pin(at=(-5, 15), direction=Direction.Up, length=1)
    USB_VDD = Pin(at=(5, 15), direction=Direction.Up, length=1)
    DVDD1 = Pin(at=(-7, 15), direction=Direction.Up, length=1)
    DVDD0 = Pin(at=(-8, 15), direction=Direction.Up, length=1)

    # GPIO pins
    GPIO0 = Pin(at=(11, 9), direction=Direction.Right, length=1)
    GPIO1 = Pin(at=(11, 8), direction=Direction.Right, length=1)
    GPIO2 = Pin(at=(11, 7), direction=Direction.Right, length=1)
    GPIO3 = Pin(at=(11, 6), direction=Direction.Right, length=1)
    GPIO4 = Pin(at=(11, 5), direction=Direction.Right, length=1)
    GPIO5 = Pin(at=(11, 4), direction=Direction.Right, length=1)
    GPIO6 = Pin(at=(11, 3), direction=Direction.Right, length=1)
    GPIO7 = Pin(at=(11, 2), direction=Direction.Right, length=1)
    GPIO8 = Pin(at=(11, 1), direction=Direction.Right, length=1)
    GPIO9 = Pin(at=(11, 0), direction=Direction.Right, length=1)
    GPIO10 = Pin(at=(11, -1), direction=Direction.Right, length=1)
    GPIO11 = Pin(at=(11, -2), direction=Direction.Right, length=1)
    GPIO12 = Pin(at=(11, -3), direction=Direction.Right, length=1)
    GPIO13 = Pin(at=(11, -4), direction=Direction.Right, length=1)
    GPIO14 = Pin(at=(11, -5), direction=Direction.Right, length=1)
    GPIO15 = Pin(at=(11, -6), direction=Direction.Right, length=1)
    GPIO16 = Pin(at=(11, -7), direction=Direction.Right, length=1)
    GPIO17 = Pin(at=(11, -8), direction=Direction.Right, length=1)
    GPIO18 = Pin(at=(11, -9), direction=Direction.Right, length=1)
    GPIO19 = Pin(at=(11, -10), direction=Direction.Right, length=1)
    GPIO20 = Pin(at=(11, -11), direction=Direction.Right, length=1)
    GPIO21 = Pin(at=(11, -12), direction=Direction.Right, length=1)
    GPIO22 = Pin(at=(11, -13), direction=Direction.Right, length=1)
    GPIO23 = Pin(at=(11, -14), direction=Direction.Right, length=1)
    GPIO24 = Pin(at=(11, -15), direction=Direction.Right, length=1)
    GPIO25 = Pin(at=(11, -16), direction=Direction.Right, length=1)
    GPIO26_ADC0 = Pin(at=(11, -18), direction=Direction.Right, length=1)
    GPIO27_ADC1 = Pin(at=(11, -19), direction=Direction.Right, length=1)
    GPIO28_ADC2 = Pin(at=(11, -20), direction=Direction.Right, length=1)
    GPIO29_ADC3 = Pin(at=(11, -21), direction=Direction.Right, length=1)

    # Other pins
    TESTEN = Pin(at=(-5, -23), direction=Direction.Down, length=1)
    XIN = Pin(at=(-11, -5), direction=Direction.Left, length=1)
    XOUT = Pin(at=(-11, -7), direction=Direction.Left, length=1)
    SWCLK = Pin(at=(-11, -16), direction=Direction.Left, length=1)
    SWD = Pin(at=(-11, -17), direction=Direction.Left, length=1)
    RUN = Pin(at=(-11, -12), direction=Direction.Left, length=1)
    USB_DM = Pin(at=(11, 12), direction=Direction.Right, length=1)
    USB_DP = Pin(at=(11, 13), direction=Direction.Right, length=1)
    QSPI_SD3 = Pin(at=(-11, 4), direction=Direction.Left, length=1)
    QSPI_SCLK = Pin(at=(-11, 2), direction=Direction.Left, length=1)
    QSPI_SD0 = Pin(at=(-11, 7), direction=Direction.Left, length=1)
    QSPI_SD2 = Pin(at=(-11, 5), direction=Direction.Left, length=1)
    QSPI_SD1 = Pin(at=(-11, 6), direction=Direction.Left, length=1)
    QSPI_SS = Pin(at=(-11, 8), direction=Direction.Left, length=1)
    GND = Pin(at=(0, -23), direction=Direction.Down, length=1)

    ref_text = Text(">REF", 1.27, Anchor.C).at(0.0, 1.27)
    value_text = Text(">VALUE", 1.27, Anchor.C).at(0.0, -2.54)

    component_box = Polygon(
        [(11.0, 15.0), (-11.0, 15.0), (-11.0, -23.0), (11.0, -23.0), (11.0, 15.0)]
    )
    raspberry_pi_text = Text("Raspberry Pi", 1.15, Anchor.C).at(0.0, -2.0)
    rp2040_text = Text("RP2040", 1.15, Anchor.C).at(0.0, -4.0)


class RP2040Component(Component):
    """Raspberry Pi RP2040 microcontroller component"""

    mpn = "RP2040"
    reference_designator_prefix = "U"

    # Power ports
    IOVDD = [Port() for _ in range(6)]
    """I/O supply voltage pins (3.3V nominal)"""
    ADC_AVDD = Port()
    """ADC analog supply voltage"""
    VREG_IN = Port()
    """Voltage regulator input (1.8V-3.6V)"""
    VREG_VOUT = Port()
    """Voltage regulator output (1.1V nominal)"""
    USB_VDD = Port()
    """USB supply voltage"""
    DVDD = [Port() for _ in range(2)]
    """Digital core supply voltage"""

    # GPIO ports
    GPIO = [Port() for _ in range(30)]
    """General purpose I/O pins (GPIO0-GPIO29)"""

    # Other ports
    TESTEN = Port()
    """Test enable pin"""
    XIN = Port()
    """Crystal oscillator input"""
    XOUT = Port()
    """Crystal oscillator output"""
    SWCLK = Port()
    """Serial wire debug clock"""
    SWD = Port()
    """Serial wire debug data"""
    RUN = Port()
    """Reset/run control pin"""
    USB_DM = Port()
    """USB data minus"""
    USB_DP = Port()
    """USB data plus"""
    QSPI_SD3 = Port()
    """QSPI data line 3"""
    QSPI_SCLK = Port()
    """QSPI serial clock"""
    QSPI_SD0 = Port()
    """QSPI data line 0 (MOSI)"""
    QSPI_SD2 = Port()
    """QSPI data line 2"""
    QSPI_SD1 = Port()
    """QSPI data line 1 (MISO)"""
    QSPI_SS = Port()
    """QSPI slave select"""
    GND = Port()
    """Ground connection"""

    landpattern = (
        QFN(num_leads=56)
        .lead_profile(
            LeadProfile(
                span=Toleranced.exact(7.0),  # D/E = 7 BSC
                pitch=0.4,  # 0.400 BSC
                type=QFNLead(
                    length=Toleranced.min_max(0.3, 0.5),  # L dimension
                    width=Toleranced.min_typ_max(0.13, 0.18, 0.23),  # b dimension
                ),
            ),
        )
        .package_body(
            RectanglePackage(
                width=Toleranced.exact(7.0),  # D = 7 BSC
                length=Toleranced.exact(7.0),  # E = 7 BSC
                height=Toleranced.min_max(0.9, 0.9),  # A dimension
            )
        )
        .thermal_pad(rectangle(3.1, 3.1))  # D2/E2 nominal = 3.1mm
        .density_level(DensityLevel.C)
    )
    # symbol = BoxSymbol(rows=[Row(left=[PinGroup([IOVDD5, IOVDD4, IOVDD3, IOVDD2, IOVDD1, IOVDD0, ADC_AVDD, VREG_IN, VREG_VOUT, USB_VDD, DVDD1, DVDD0])])])
    symbol = RP2040_Symbol()

    def __init__(self):
        # Pin mappings based on the pin-properties from the original Stanza file
        landpattern = self.landpattern
        IOVDD = self.IOVDD
        GPIO = self.GPIO
        DVDD = self.DVDD
        self.mappings = [
            PadMapping(
                {
                    IOVDD[5]: [landpattern.p[1]],
                    IOVDD[4]: [landpattern.p[10]],
                    GPIO[8]: [landpattern.p[11]],
                    GPIO[9]: [landpattern.p[12]],
                    GPIO[10]: [landpattern.p[13]],
                    GPIO[11]: [landpattern.p[14]],
                    GPIO[12]: [landpattern.p[15]],
                    GPIO[13]: [landpattern.p[16]],
                    GPIO[14]: [landpattern.p[17]],
                    GPIO[15]: [landpattern.p[18]],
                    self.TESTEN: [landpattern.p[19]],
                    GPIO[0]: [landpattern.p[2]],
                    self.XIN: [landpattern.p[20]],
                    self.XOUT: [landpattern.p[21]],
                    IOVDD[3]: [landpattern.p[22]],
                    self.SWCLK: [landpattern.p[24]],
                    self.SWD: [landpattern.p[25]],
                    self.RUN: [landpattern.p[26]],
                    GPIO[16]: [landpattern.p[27]],
                    GPIO[17]: [landpattern.p[28]],
                    GPIO[18]: [landpattern.p[29]],
                    GPIO[1]: [landpattern.p[3]],
                    GPIO[19]: [landpattern.p[30]],
                    GPIO[20]: [landpattern.p[31]],
                    GPIO[21]: [landpattern.p[32]],
                    IOVDD[2]: [landpattern.p[33]],
                    GPIO[22]: [landpattern.p[34]],
                    GPIO[23]: [landpattern.p[35]],
                    GPIO[24]: [landpattern.p[36]],
                    GPIO[25]: [landpattern.p[37]],
                    GPIO[26]: [landpattern.p[38]],
                    GPIO[27]: [landpattern.p[39]],
                    GPIO[2]: [landpattern.p[4]],
                    GPIO[28]: [landpattern.p[40]],
                    GPIO[29]: [landpattern.p[41]],
                    IOVDD[1]: [landpattern.p[42]],
                    self.ADC_AVDD: [landpattern.p[43]],
                    self.USB_DM: [landpattern.p[46]],
                    self.USB_DP: [landpattern.p[47]],
                    self.USB_VDD: [landpattern.p[48]],
                    IOVDD[0]: [landpattern.p[49]],
                    GPIO[3]: [landpattern.p[5]],
                    self.VREG_IN: [landpattern.p[44]],
                    self.VREG_VOUT: [landpattern.p[45]],
                    DVDD[0]: [landpattern.p[50]],
                    DVDD[1]: [landpattern.p[23]],
                    self.QSPI_SD3: [landpattern.p[51]],
                    self.QSPI_SCLK: [landpattern.p[52]],
                    self.QSPI_SD0: [landpattern.p[53]],
                    self.QSPI_SD2: [landpattern.p[54]],
                    self.QSPI_SD1: [landpattern.p[55]],
                    self.QSPI_SS: [landpattern.p[56]],
                    self.GND: [landpattern.thermal_pads[0]],
                    GPIO[4]: [landpattern.p[6]],
                    GPIO[5]: [landpattern.p[7]],
                    GPIO[6]: [landpattern.p[8]],
                    GPIO[7]: [landpattern.p[9]],
                }
            )
        ]


class RP2040(Circuit):
    """
    Complete RP2040 microcontroller circuit with supporting components

    Includes the RP2040 MCU, crystal oscillator, flash memory, power regulation,
    bypass capacitors, and boot/reset buttons.

    Provides GPIO, I2C, SPI(cs=True), USB2(), and ADC interfaces. Use require to access IO.
    """

    power = Power()
    """Main power supply interface"""
    usb = USB2()
    """USB 2.0 interface"""

    def __init__(self):
        self.mcu = RP2040Component()
        # USB connections
        self.usb_nets = [
            self.usb.data.n >> self.mcu.USB_DM,
            self.usb.data.p >> self.mcu.USB_DP,
        ]

        # Bypass capacitors for VREG_VOUT and VREG_IN
        self.c_byp1 = Capacitor(capacitance=1.0e-6).insert(
            self.mcu.VREG_VOUT, self.power.Vn, short_trace=True
        )
        self.c_byp2 = Capacitor(capacitance=1.0e-6).insert(
            self.mcu.VREG_IN, self.power.Vn, short_trace=True
        )

        # IOVDD bypass capacitors (6 total, 1µF each)
        self.iovdd_bypass = []
        for iovdd_pin in self.mcu.IOVDD:
            bypass_cap = Capacitor(capacitance=1.0e-6).insert(
                iovdd_pin, self.power.Vn, short_trace=True
            )
            self.iovdd_bypass.append(bypass_cap)

        # Power net connections
        self.power_nets = [
            # Connect VREG_VOUT to DVDD pins
            self.mcu.VREG_VOUT + self.mcu.DVDD[0] + self.mcu.DVDD[1],
            # VDD net: connect ADC_AVDD, USB_VDD, VREG_IN, and all IOVDD to power supply
            self.power.Vp
            + self.mcu.ADC_AVDD
            + self.mcu.USB_VDD
            + self.mcu.VREG_IN
            + self.mcu.IOVDD[0]
            + self.mcu.IOVDD[1]
            + self.mcu.IOVDD[2]
            + self.mcu.IOVDD[3]
            + self.mcu.IOVDD[4]
            + self.mcu.IOVDD[5],
            # GND net: connect MCU ground to power supply ground
            self.mcu.GND + self.power.Vn,
        ]
        # Crystal resonator circuit
        self.x = X322512MSB4SI()

        # Crystal load capacitor calculations
        # stray_capacitance = 5.0e-12  # 5pF
        # c_load = 20.0e-12  # 20pF (from crystal datasheet)
        # c_bal = 2.0 * (c_load - stray_capacitance) = 2.0 * (20e-12 - 5e-12) = 30pF
        # Using closest standard value: 33pF
        c_bal = 33.0e-12

        # Load capacitors (C0G temperature coefficient preferred for crystal circuits)
        self.c_b1 = Capacitor(
            capacitance=c_bal, temperature_coefficient_code="C0G"
        ).insert(self.x.OSC2, self.power.Vn, short_trace=True)
        self.c_b2 = Capacitor(
            capacitance=c_bal, temperature_coefficient_code="C0G"
        ).insert(self.x.OSC1, self.power.Vn, short_trace=True)

        # Series resistor between crystal and XOUT
        self.r_x = Resistor(resistance=1.0e3).insert(self.x.OSC2, self.mcu.XOUT)

        # Crystal ground connections
        self.crystal_gnd_nets = [
            self.x.GND0 + self.power.Vn,
            self.x.GND1 + self.power.Vn,
        ]

        # Crystal oscillator connections
        self.crystal_nets = [self.x.OSC1 + self.mcu.XIN]

        # Boot and reset button circuits
        # Boot button (connected to QSPI_SS for boot mode selection)
        self.boot_butt = TactileSwitch()
        self.boot_r = Resistor(resistance=1.0e3).insert(
            self.boot_butt.p[1], self.mcu.QSPI_SS
        )
        self.c_boot = Capacitor(capacitance=0.1e-6).insert(
            self.boot_butt.p[1], self.power.Vp, short_trace=True
        )

        # Reset button (connected to RUN pin)
        self.reset_butt = TactileSwitch()
        self.reset_r = Resistor(resistance=1.0e3).insert(
            self.reset_butt.p[1], self.mcu.RUN
        )
        self.c_reset = Capacitor(capacitance=0.1e-6).insert(
            self.reset_butt.p[1], self.power.Vp, short_trace=True
        )

        # Button ground connections
        self.button_gnd_nets = [
            self.boot_butt.p[2] + self.power.Vn,
            self.reset_butt.p[2] + self.power.Vn,
        ]

        # W25Q128 Flash Memory Circuit
        # Using the W25Q128Circuit which includes the component, bypass capacitor, and WideSPI interface
        self.flash_circuit = W25Q128JVSIQ()

        # Flash CS pull-up resistor: val r-pu = res-strap(flash.VCC flash.CS_NOT, 10.0e3)
        # property(r-pu.DNP) = true  # Do Not Populate by default
        # Since we're using the circuit interface, we need to add this resistor externally
        self.r_flash_pu = Resistor(resistance=10.0e3).insert(
            self.power.Vp, self.mcu.QSPI_SS
        )
        self.r_flash_pu.in_bom = False
        self.r_flash_pu.soldered = False
        self.r_flash_pu.schematic_x_out = True
        # Note: In JITX, we can't directly set DNP property, but this resistor can be marked as optional

        # Connect the flash circuit's power to the RP2040's power
        self.flash_power_nets = [
            self.flash_circuit.power.Vp + self.power.Vp,
            self.flash_circuit.power.Vn + self.power.Vn,
        ]

        # Connect the flash circuit's QSPI interface to the RP2040's QSPI pins
        # The W25Q128Circuit has a WideSPI.quad interface with 4 data lines and clock/cs
        self.flash_qspi_nets = [
            self.flash_circuit.qspi.data[0] + self.mcu.QSPI_SD0,  # DI (MOSI)
            self.flash_circuit.qspi.data[1] + self.mcu.QSPI_SD1,  # DO (MISO)
            self.flash_circuit.qspi.data[2] + self.mcu.QSPI_SD2,  # IO2
            self.flash_circuit.qspi.data[3] + self.mcu.QSPI_SD3,  # IO3
            self.flash_circuit.qspi.sck + self.mcu.QSPI_SCLK,  # Clock
        ]

        # Add chip select connection if available (following the same pattern as in W25Q128Circuit)
        if self.flash_circuit.qspi.cs is not None:
            self.flash_qspi_nets.append(self.flash_circuit.qspi.cs + self.mcu.QSPI_SS)

    # TODO: this is not all the peripherals that are available on the RP2040, we need to add them here

    @provide(GPIO_Common)
    def self_provide_gpio(self, g: GPIO_Common):
        """Provide GPIO pins from the RP2040's 30 available GPIO pins"""
        return [{g.gpio: gpio} for gpio in self.mcu.GPIO]

    @provide(Timer)
    def self_provide_timer(self, timer: Timer):
        """Provide timer interface using GPIO0"""
        return [{timer.timer: t} for t in self.mcu.GPIO]

    class I2C0_SDA(Port):
        """I2C0 SDA pin interface"""

        p = Port()
        """SDA pin"""

    class I2C0_SCL(Port):
        """I2C0 SCL pin interface"""

        p = Port()
        """SCL pin"""

    class I2C1_SDA(Port):
        """I2C1 SDA pin interface"""

        p = Port()
        """SDA pin"""

    class I2C1_SCL(Port):
        """I2C1 SCL pin interface"""

        p = Port()
        """SCL pin"""

    # SPI port classes
    class SPI0_RX(Port):
        """SPI0 RX pin interface"""

        p = Port()
        """RX pin"""

    class SPI0_CSn(Port):
        """SPI0 CSn pin interface"""

        p = Port()
        """CSn pin"""

    class SPI0_SCK(Port):
        """SPI0 SCK pin interface"""

        p = Port()
        """SCK pin"""

    class SPI0_TX(Port):
        """SPI0 TX pin interface"""

        p = Port()
        """TX pin"""

    class SPI1_RX(Port):
        """SPI1 RX pin interface"""

        p = Port()
        """RX pin"""

    class SPI1_CSn(Port):
        """SPI1 CSn pin interface"""

        p = Port()
        """CSn pin"""

    class SPI1_SCK(Port):
        """SPI1 SCK pin interface"""

        p = Port()
        """SCK pin"""

    class SPI1_TX(Port):
        """SPI1 TX pin interface"""

        p = Port()
        """TX pin"""

    # UART port classes
    class UART0_RX(Port):
        """UART0 RX pin interface"""

        p = Port()
        """RX pin"""

    class UART0_TX(Port):
        """UART0 TX pin interface"""

        p = Port()
        """TX pin"""

    class UART0_CTS(Port):
        """UART0 CTS pin interface"""

        p = Port()
        """CTS pin"""

    class UART0_RTS(Port):
        """UART0 RTS pin interface"""

        p = Port()
        """RTS pin"""

    class UART1_RX(Port):
        """UART1 RX pin interface"""

        p = Port()
        """RX pin"""

    class UART1_TX(Port):
        """UART1 TX pin interface"""

        p = Port()
        """TX pin"""

    class UART1_CTS(Port):
        """UART1 CTS pin interface"""

        p = Port()
        """CTS pin"""

    class UART1_RTS(Port):
        """UART1 RTS pin interface"""

        p = Port()
        """RTS pin"""

    # Below we use a technique to individually select pins for each i2c, spi,
    # and uart interface using custom bundles which are solely present to
    # represent a single pin function. Of each set only one pin can be selected
    # for each "subset" of the bundle, which is why we use the
    # "@provide.one_of" decorator, instead of "@provide" which would allow all
    # pins to be used. It's technically not an error to use "@provide" in this
    # particular case, since we control where it's being used and each will
    # only be used once, but it's good practice to use the correct decorator.

    @provide.one_of(I2C0_SDA)
    def self_provide_i2c0_sda(self, i2c0_sda: I2C0_SDA):
        """Provide I2C0 SDA pins (GPIO 0, 4, 8, 12, 16, 20)"""
        return [{i2c0_sda.p: self.mcu.GPIO[i]} for i in [0, 4, 8, 12, 16, 20]]

    @provide.one_of(I2C0_SCL)
    def self_provide_i2c0_scl(self, i2c0_scl: I2C0_SCL):
        """Provide I2C0 SCL pins (GPIO 1, 5, 9, 13, 17, 21)"""
        return [{i2c0_scl.p: self.mcu.GPIO[i]} for i in [1, 5, 9, 13, 17, 21]]

    @provide.one_of(I2C1_SDA)
    def self_provide_i2c1_sda(self, i2c1_sda: I2C1_SDA):
        """Provide I2C1 SDA pins (GPIO 2, 6, 10, 14, 18, 26)"""
        return [{i2c1_sda.p: self.mcu.GPIO[i]} for i in [2, 6, 10, 14, 18, 26]]

    @provide.one_of(I2C1_SCL)
    def self_provide_i2c1_scl(self, i2c1_scl: I2C1_SCL):
        """Provide I2C1 SCL pins (GPIO 3, 7, 11, 15, 19, 27)"""
        return [{i2c1_scl.p: self.mcu.GPIO[i]} for i in [3, 7, 11, 15, 19, 27]]

    # SPI pin providers
    @provide.one_of(SPI0_RX)
    def self_provide_spi0_rx(self, spi0_rx: SPI0_RX):
        """Provide SPI0 RX pins (GPIO 0, 4, 16, 20)"""
        return [{spi0_rx.p: self.mcu.GPIO[i]} for i in [0, 4, 16, 20]]

    @provide.one_of(SPI0_CSn)
    def self_provide_spi0_csn(self, spi0_csn: SPI0_CSn):
        """Provide SPI0 CSn pins (GPIO 1, 5, 17, 21)"""
        return [{spi0_csn.p: self.mcu.GPIO[i]} for i in [1, 5, 17, 21]]

    @provide.one_of(SPI0_SCK)
    def self_provide_spi0_sck(self, spi0_sck: SPI0_SCK):
        """Provide SPI0 SCK pins (GPIO 2, 6, 18, 22)"""
        return [{spi0_sck.p: self.mcu.GPIO[i]} for i in [2, 6, 18, 22]]

    @provide.one_of(SPI0_TX)
    def self_provide_spi0_tx(self, spi0_tx: SPI0_TX):
        """Provide SPI0 TX pins (GPIO 3, 7, 19, 23)"""
        return [{spi0_tx.p: self.mcu.GPIO[i]} for i in [3, 7, 19, 23]]

    @provide.one_of(SPI1_RX)
    def self_provide_spi1_rx(self, spi1_rx: SPI1_RX):
        """Provide SPI1 RX pins (GPIO 8, 12, 24, 28)"""
        return [{spi1_rx.p: self.mcu.GPIO[i]} for i in [8, 12, 24, 28]]

    @provide.one_of(SPI1_CSn)
    def self_provide_spi1_csn(self, spi1_csn: SPI1_CSn):
        """Provide SPI1 CSn pins (GPIO 9, 13, 25, 29)"""
        return [{spi1_csn.p: self.mcu.GPIO[i]} for i in [9, 13, 25, 29]]

    @provide.one_of(SPI1_SCK)
    def self_provide_spi1_sck(self, spi1_sck: SPI1_SCK):
        """Provide SPI1 SCK pins (GPIO 10, 14, 26)"""
        return [{spi1_sck.p: self.mcu.GPIO[i]} for i in [10, 14, 26]]

    @provide.one_of(SPI1_TX)
    def self_provide_spi1_tx(self, spi1_tx: SPI1_TX):
        """Provide SPI1 TX pins (GPIO 11, 15, 27)"""
        return [{spi1_tx.p: self.mcu.GPIO[i]} for i in [11, 15, 27]]

    # UART pin providers
    @provide.one_of(UART0_RX)
    def self_provide_uart0_rx(self, uart0_rx: UART0_RX):
        """Provide UART0 RX pins (GPIO 1, 13, 17, 29)"""
        return [{uart0_rx.p: self.mcu.GPIO[i]} for i in [1, 13, 17, 29]]

    @provide.one_of(UART0_TX)
    def self_provide_uart0_tx(self, uart0_tx: UART0_TX):
        """Provide UART0 TX pins (GPIO 0, 4, 12, 16)"""
        return [{uart0_tx.p: self.mcu.GPIO[i]} for i in [0, 4, 12, 16]]

    @provide.one_of(UART0_CTS)
    def self_provide_uart0_cts(self, uart0_cts: UART0_CTS):
        """Provide UART0 CTS pins (GPIO 2, 6, 14, 18)"""
        return [{uart0_cts.p: self.mcu.GPIO[i]} for i in [2, 6, 14, 18]]

    @provide.one_of(UART0_RTS)
    def self_provide_uart0_rts(self, uart0_rts: UART0_RTS):
        """Provide UART0 RTS pins (GPIO 3, 7, 15, 19)"""
        return [{uart0_rts.p: self.mcu.GPIO[i]} for i in [3, 7, 15, 19]]

    @provide.one_of(UART1_RX)
    def self_provide_uart1_rx(self, uart1_rx: UART1_RX):
        """Provide UART1 RX pins (GPIO 5, 9, 21, 25, 29)"""
        return [{uart1_rx.p: self.mcu.GPIO[i]} for i in [5, 9, 21, 25, 29]]

    @provide.one_of(UART1_TX)
    def self_provide_uart1_tx(self, uart1_tx: UART1_TX):
        """Provide UART1 TX pins (GPIO 4, 8, 20, 24, 28)"""
        return [{uart1_tx.p: self.mcu.GPIO[i]} for i in [4, 8, 20, 24, 28]]

    @provide.one_of(UART1_CTS)
    def self_provide_uart1_cts(self, uart1_cts: UART1_CTS):
        """Provide UART1 CTS pins (GPIO 6, 10, 22, 26)"""
        return [{uart1_cts.p: self.mcu.GPIO[i]} for i in [6, 10, 22, 26]]

    @provide.one_of(UART1_RTS)
    def self_provide_uart1_rts(self, uart1_rts: UART1_RTS):
        """Provide UART1 RTS pins (GPIO 7, 11, 23, 27)"""
        return [{uart1_rts.p: self.mcu.GPIO[i]} for i in [7, 11, 23, 27]]

    @provide(I2C)
    def provide_i2c0(self, i2c: I2C):
        """Provide I2C0 interface using available SDA/SCL pin pairs"""
        sda = self.require(self.I2C0_SDA)
        scl = self.require(self.I2C0_SCL)
        return [{i2c.sda: sda.p, i2c.scl: scl.p}]

    @provide(I2C)
    def provide_i2c1(self, i2c: I2C):
        """Provide I2C1 interface using available SDA/SCL pin pairs"""
        sda = self.require(self.I2C1_SDA)
        scl = self.require(self.I2C1_SCL)
        return [{i2c.sda: sda.p, i2c.scl: scl.p}]

    @provide(SPI(cs=True))
    def provide_spi0(self, spi: SPI):
        """Provide SPI0 interface using available pin pairs"""
        rx = self.require(self.SPI0_RX)
        csn = self.require(self.SPI0_CSn)
        sck = self.require(self.SPI0_SCK)
        tx = self.require(self.SPI0_TX)
        assert spi.cs and spi.copi and spi.cipo
        return [{spi.cipo: rx.p, spi.cs: csn.p, spi.sck: sck.p, spi.copi: tx.p}]

    @provide(SPI(cs=True))
    def provide_spi1(self, spi: SPI):
        """Provide SPI1 interface using available pin pairs"""
        rx = self.require(self.SPI1_RX)
        csn = self.require(self.SPI1_CSn)
        sck = self.require(self.SPI1_SCK)
        tx = self.require(self.SPI1_TX)
        assert spi.cs and spi.copi and spi.cipo
        return [{spi.cipo: rx.p, spi.cs: csn.p, spi.sck: sck.p, spi.copi: tx.p}]

    @provide(UART)
    def provide_uart0(self, uart: UART):
        """Provide UART0 interface using available TX/RX pin pairs"""
        tx = self.require(self.UART0_TX)
        rx = self.require(self.UART0_RX)
        assert uart.tx and uart.rx
        return [{uart.tx: tx.p, uart.rx: rx.p}]

    @provide(UART)
    def provide_uart1(self, uart: UART):
        """Provide UART1 interface using available TX/RX pin pairs"""
        tx = self.require(self.UART1_TX)
        rx = self.require(self.UART1_RX)
        assert uart.tx and uart.rx
        return [{uart.tx: tx.p, uart.rx: rx.p}]

    @provide(ADC)
    def self_provide_adc(self, adc: ADC):
        """Provide ADC interface using GPIO26-29 (ADC0-3)"""
        return [{adc.adc: self.mcu.GPIO[i]} for i in [26, 27, 28, 29]]

    ## Property for datasheet URL
    datasheet = (
        "https://datasheet.lcsc.com/lcsc/2201101600_Raspberry-Pi-RP2040_C2040.pdf"
    )


Device: type[RP2040] = RP2040
